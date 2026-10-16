"""Small LangGraph agent: router -> specialist -> tool loop -> end."""
from datetime import date
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import (
    AIMessage, BaseMessage, HumanMessage, SystemMessage,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from .hrms_adapter import HRSystem
from .tool_factory import build_read_tools


MODEL = "gemini-flash-lite-latest"    #    # gemini-2.0-flash was retired by Google in 2026

SYSTEM_PROMPT = """You are an HR support assistant for one specific employee.
Today's date is {today}.

Rules:
- Never ask for, guess, or accept another person's employee ID.
- Always call a tool to fetch facts. If a tool returns {{"error": ...}} or
  nothing, say so clearly. NEVER make up numbers.
- When a policy or IT KB result includes a source file and page, cite them
  like: (leave_policy.pdf, page 1).
- Resolve "today", "tomorrow", "next Friday" against today's date above
  and SHOW the resolved date in your answer.
- Keep answers short, friendly, factual.
"""

ROUTER_PROMPT = """Classify the user's request into exactly ONE label:

- payroll            (payslip, salary, PF)
- leave_attendance   (leave balance, holidays, attendance)
- info_policy        (manager, team, company policies, HR rules)
- helpdesk           (IT issues: VPN, printer, password, Wi-Fi, laptop)
- unclear            (not enough info)

Reply with ONE lowercase word only. No punctuation.
"""

VALID_INTENTS = {"payroll", "leave_attendance", "info_policy",
                 "helpdesk", "unclear"}


def content_to_text(content) -> str:
    """Normalize LLM content into plain text.

    Newer langchain-google-genai versions can return `content` as a list
    of content blocks like [{'type': 'text', 'text': 'hello'}, ...].
    Older versions returned a plain string. This handles both.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                if block.get("type") == "text" or "text" in block:
                    parts.append(block.get("text", ""))
            else:
                text = getattr(block, "text", None)
                if text:
                    parts.append(text)
        return " ".join(p for p in parts if p)
    return str(content)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    intent: str


def build_agent(hrms: HRSystem, emp_code: str, checkpointer=None):
    """Build a compiled LangGraph agent for one emp_code. Call per request."""
    tools = build_read_tools(hrms, emp_code)

    payroll_tools = [tools["get_payslip"], tools["get_pf_balance"]]
    leave_tools = [tools["get_leave_balance"], tools["get_attendance_summary"],
                   tools["get_holidays"]]
    info_tools = [tools["get_my_manager"], tools["get_my_team"],
                  tools["search_policy"]]
    helpdesk_tools = [tools["search_it_kb"]]

    llm = ChatGoogleGenerativeAI(model=MODEL, temperature=0)
    router_llm = ChatGoogleGenerativeAI(model=MODEL, temperature=0)

    payroll_llm = llm.bind_tools(payroll_tools)
    leave_llm = llm.bind_tools(leave_tools)
    info_llm = llm.bind_tools(info_tools)
    helpdesk_llm = llm.bind_tools(helpdesk_tools)

    def router_node(state: AgentState):
        last_raw = state["messages"][-1].content
        last = content_to_text(last_raw)
        reply = router_llm.invoke([
            SystemMessage(content=ROUTER_PROMPT),
            HumanMessage(content=last),
        ])
        text = content_to_text(reply.content).strip().lower()
        intent = text.split()[0] if text else "unclear"
        if intent not in VALID_INTENTS:
            intent = "unclear"
        return {"intent": intent}

    def specialist(llm_with_tools):
        def node(state: AgentState):
            sys = SystemMessage(content=SYSTEM_PROMPT.format(today=date.today()))
            msgs = [sys] + state["messages"]
            return {"messages": [llm_with_tools.invoke(msgs)]}
        return node

    def clarify_node(state: AgentState):
        return {"messages": [AIMessage(
            content="Could you give me a bit more detail? For example, "
                    "which month and year for the payslip, or the leave type."
        )]}

    def route_after_router(state: AgentState) -> Literal[
        "payroll", "leave_attendance", "info_policy", "helpdesk", "unclear"
    ]:
        return state["intent"]

    builder = StateGraph(AgentState)
    builder.add_node("router", router_node)
    builder.add_node("payroll", specialist(payroll_llm))
    builder.add_node("leave_attendance", specialist(leave_llm))
    builder.add_node("info_policy", specialist(info_llm))
    builder.add_node("helpdesk", specialist(helpdesk_llm))
    builder.add_node("unclear", clarify_node)

    builder.add_node("payroll_tools", ToolNode(payroll_tools))
    builder.add_node("leave_tools", ToolNode(leave_tools))
    builder.add_node("info_tools", ToolNode(info_tools))
    builder.add_node("helpdesk_tools", ToolNode(helpdesk_tools))

    builder.add_edge(START, "router")
    builder.add_conditional_edges("router", route_after_router, {
        "payroll": "payroll",
        "leave_attendance": "leave_attendance",
        "info_policy": "info_policy",
        "helpdesk": "helpdesk",
        "unclear": "unclear",
    })

    builder.add_conditional_edges("payroll", tools_condition,
                                  {"tools": "payroll_tools", END: END})
    builder.add_conditional_edges("leave_attendance", tools_condition,
                                  {"tools": "leave_tools", END: END})
    builder.add_conditional_edges("info_policy", tools_condition,
                                  {"tools": "info_tools", END: END})
    builder.add_conditional_edges("helpdesk", tools_condition,
                                  {"tools": "helpdesk_tools", END: END})

    builder.add_edge("payroll_tools", "payroll")
    builder.add_edge("leave_tools", "leave_attendance")
    builder.add_edge("info_tools", "info_policy")
    builder.add_edge("helpdesk_tools", "helpdesk")
    builder.add_edge("unclear", END)

    return builder.compile(checkpointer=checkpointer)


MEMORY = MemorySaver()