"""Read-only LangChain tools bound to ONE emp_code.

No tool takes a user-id parameter. The emp_code is captured at creation
time from the JWT. The LLM cannot ask for another person's data.
"""
from langchain_core.tools import tool
from .hrms_adapter import HRSystem


def build_read_tools(hrms: HRSystem, emp_code: str) -> dict:
    """Return tool-name -> LangChain tool bound to this emp_code."""

    @tool
    def get_payslip(month: int, year: int) -> dict:
        """Get the logged-in employee's payslip for a month (1-12) and year."""
        res = hrms.get_payslip(emp_code, year, month)
        return res or {"error": f"No payslip found for {year}-{month:02d}"}

    @tool
    def get_pf_balance() -> dict:
        """Get PF (provident fund) balance for the logged-in employee."""
        res = hrms.get_pf(emp_code)
        return res or {"error": "No PF records found"}

    @tool
    def get_leave_balance() -> dict:
        """Get leave balances (Casual, Sick, Earned) for the logged-in employee."""
        res = hrms.get_leave_balances(emp_code)
        return res or {"error": "No leave balance records found"}

    @tool
    def get_attendance_summary(month: int, year: int) -> dict:
        """Attendance summary (present/missing-punch/etc.) for a month and year."""
        res = hrms.get_attendance(emp_code, year, month)
        return res or {"error": f"No attendance records for {year}-{month:02d}"}

    @tool
    def get_holidays(from_date: str, to_date: str) -> dict:
        """Company holidays between two ISO dates (YYYY-MM-DD)."""
        emp = hrms.get_employee(emp_code)
        loc = emp.get("location", "ALL") if emp else "ALL"
        res = hrms.get_holidays(from_date, to_date, loc)
        return res or {"error": "No holidays in that range"}

    @tool
    def get_my_manager() -> dict:
        """Get the manager of the logged-in employee."""
        res = hrms.get_manager(emp_code)
        return res or {"error": "No manager assigned"}

    @tool
    def get_my_team() -> dict:
        """List the direct reports of the logged-in employee."""
        res = hrms.get_team(emp_code)
        return res or {"error": "No direct reports"}

    @tool
    def search_policy(query: str) -> dict:
        """Search company HR / payroll / leave / code-of-conduct policies.
        Returns matching snippets with the source PDF name and page number."""
        try:
            from rag.retrievers import search_policy as _sp
            hits = _sp(query, k=4)
        except Exception as e:
            return {"error": f"Policy search failed: {type(e).__name__}: {e}"}
        if not hits:
            return {"error": "No matching policy sections found."}
        return {"results": hits}

    @tool
    def search_it_kb(query: str) -> dict:
        """Search the IT knowledge base for fixes to common issues
        (VPN, printer, password reset, Wi-Fi)."""
        try:
            from rag.retrievers import search_it_kb as _sk
            hits = _sk(query, k=4)
        except Exception as e:
            return {"error": f"IT KB search failed: {type(e).__name__}: {e}"}
        if not hits:
            return {"error": "No matching IT KB articles found."}
        return {"results": hits}

    return {
        "get_payslip": get_payslip,
        "get_pf_balance": get_pf_balance,
        "get_leave_balance": get_leave_balance,
        "get_attendance_summary": get_attendance_summary,
        "get_holidays": get_holidays,
        "get_my_manager": get_my_manager,
        "get_my_team": get_my_team,
        "search_policy": search_policy,
        "search_it_kb": search_it_kb,
    }