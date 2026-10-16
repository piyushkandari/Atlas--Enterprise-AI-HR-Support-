"""Pydantic request bodies."""
from datetime import date
from pydantic import BaseModel


class LeaveValidateRequest(BaseModel):
    leave_type: str
    from_date: date
    to_date: date
    reason: str = ""


class RegularizationValidateRequest(BaseModel):
    date: date
    in_time: str
    out_time: str
    reason: str = ""