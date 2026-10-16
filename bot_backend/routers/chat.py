"""Chat endpoint. emp_code comes from the JWT — never from the request body."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage

from ..database import get_db
from ..deps import get_current_user
from ..schemas import ChatRequest, ChatResponse
from ..hrms_adapter import MockHRMSClient
from ..agent import build_agent, MEMORY, content_to_text
from ..models import ChatHistory, AuditLog

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp_code = user["emp_code"]

    # Save the user's message first.
    db.add(ChatHistory(session_id=body.session_id, emp_code=emp_code,
                       role="user", content=body.message))
    db.commit()

    hrms = MockHRMSClient()
    agent = build_agent(hrms, emp_code, checkpointer=MEMORY)
    config = {"configurable": {"thread_id": f"{emp_code}:{body.session_id}"}}

    reply: str
    intent: str | None = None

    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=body.message)]},
            config=config,
        )
        reply = content_to_text(result["messages"][-1].content)
        intent = result.get("intent")

        # Audit every tool call — name + args only, never values.
        for msg in result["messages"]:
            for call in getattr(msg, "tool_calls", []) or []:
                db.add(AuditLog(emp_code=emp_code,
                                tool_name=call.get("name", "?"),
                                args_summary=str(call.get("args", {}))[:500]))
    except Exception as e:
        # Any LLM / graph / network hiccup becomes a friendly reply, not a 500.
        reply = (f"Sorry — I ran into a temporary problem while handling that "
                 f"({type(e).__name__}). Please try again in a moment.")
        intent = "error"
        db.add(AuditLog(emp_code=emp_code, tool_name="chat_error",
                        args_summary=str(e)[:500]))

    db.add(ChatHistory(session_id=body.session_id, emp_code=emp_code,
                       role="assistant", content=reply))
    db.commit()

    return ChatResponse(reply=reply, session_id=body.session_id, intent=intent)