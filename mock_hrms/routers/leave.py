"""Leave balances + validation (plain code, NOT LLM)."""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import verify_api_key
from .. import models
from ..schemas import LeaveValidateRequest

router = APIRouter(prefix="/employees", tags=["leave"],
                   dependencies=[Depends(verify_api_key)])

VALID_LEAVE_TYPES = {"Casual", "Sick", "Earned"}


def _validate_leave(db: Session, emp_code: str, leave_type: str,
                    from_date: date, to_date: date) -> dict:
    if leave_type not in VALID_LEAVE_TYPES:
        return {"valid": False, "reason": f"Invalid leave type '{leave_type}'"}

    emp = db.query(models.Employee).filter_by(emp_code=emp_code).first()
    if not emp:
        return {"valid": False, "reason": "Employee not found"}
    if from_date < date.today():
        return {"valid": False, "reason": "Past dates cannot be requested"}
    if to_date < from_date:
        return {"valid": False, "reason": "End date is before start date"}

    overlap = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.emp_code == emp_code,
        models.LeaveRequest.status.in_(["Pending", "Approved"]),
        models.LeaveRequest.from_date <= to_date,
        models.LeaveRequest.to_date >= from_date).first()
    if overlap:
        return {"valid": False, "reason": f"Overlaps with existing request #{overlap.id}"}

    days = skipped_we = skipped_hol = 0
    cur = from_date
    while cur <= to_date:
        if cur.weekday() >= 5:
            skipped_we += 1
        else:
            hol = db.query(models.Holiday).filter(
                models.Holiday.date == cur,
                models.Holiday.location.in_(["ALL", emp.location])).first()
            if hol:
                skipped_hol += 1
            else:
                days += 1
        cur += timedelta(days=1)

    if days == 0:
        return {"valid": False, "reason": "Range contains no working days"}

    bal = db.query(models.LeaveBalance).filter_by(
        emp_code=emp_code, leave_type=leave_type).first()
    if not bal:
        return {"valid": False, "reason": f"No balance record for {leave_type}"}

    available = bal.total - bal.used
    if available < days:
        return {"valid": False,
                "reason": f"Insufficient balance (available {available}, requested {days})"}

    return {"valid": True, "days": days,
            "skipped_weekends": skipped_we, "skipped_holidays": skipped_hol,
            "balance_before": available, "balance_after": available - days}


@router.get("/{emp_code}/leave/balances")
def get_balances(emp_code: str, db: Session = Depends(get_db)) -> dict:
    rows = db.query(models.LeaveBalance).filter_by(emp_code=emp_code).all()
    return {"balances": [
        {"leave_type": r.leave_type, "total": r.total, "used": r.used,
         "available": r.total - r.used} for r in rows]}


@router.post("/{emp_code}/leave/validate")
def validate_leave(emp_code: str, body: LeaveValidateRequest,
                   db: Session = Depends(get_db)) -> dict:
    return _validate_leave(db, emp_code, body.leave_type, body.from_date, body.to_date)


@router.post("/{emp_code}/leave")
def create_leave(emp_code: str, body: LeaveValidateRequest,
                 db: Session = Depends(get_db)) -> dict:
    result = _validate_leave(db, emp_code, body.leave_type, body.from_date, body.to_date)
    if not result["valid"]:
        raise HTTPException(400, result["reason"])
    req = models.LeaveRequest(emp_code=emp_code, leave_type=body.leave_type,
                              from_date=body.from_date, to_date=body.to_date,
                              days=result["days"], reason=body.reason,
                              status="Pending")
    db.add(req)
    bal = db.query(models.LeaveBalance).filter_by(
        emp_code=emp_code, leave_type=body.leave_type).first()
    bal.used += result["days"]
    db.commit()
    db.refresh(req)
    return {"request_id": req.id, "status": req.status, "days": req.days, **result}


@router.get("/{emp_code}/leave/requests")
def list_requests(emp_code: str, db: Session = Depends(get_db)) -> dict:
    rows = db.query(models.LeaveRequest).filter_by(emp_code=emp_code).order_by(
        models.LeaveRequest.from_date.desc()).all()
    return {"requests": [
        {"id": r.id, "leave_type": r.leave_type,
         "from_date": str(r.from_date), "to_date": str(r.to_date),
         "days": r.days, "status": r.status} for r in rows]}


@router.post("/{emp_code}/leave/{request_id}/cancel")
def cancel_leave(emp_code: str, request_id: int,
                 db: Session = Depends(get_db)) -> dict:
    req = db.query(models.LeaveRequest).filter_by(
        id=request_id, emp_code=emp_code).first()
    if not req:
        raise HTTPException(404, "Leave request not found")
    if req.status != "Pending":
        raise HTTPException(400, f"Only Pending can be cancelled (status={req.status})")
    req.status = "Cancelled"
    bal = db.query(models.LeaveBalance).filter_by(
        emp_code=emp_code, leave_type=req.leave_type).first()
    if bal:
        bal.used = max(0, bal.used - req.days)
    db.commit()
    return {"request_id": req.id, "status": req.status}