"""Regularization for MISSING_PUNCH days only."""
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import verify_api_key
from .. import models
from ..schemas import RegularizationValidateRequest

router = APIRouter(
    prefix="/employees",
    tags=["regularization"],
    dependencies=[Depends(verify_api_key)],
)

MAX_PER_MONTH = 3


def _validate_regularization(
    db: Session, emp_code: str, day: date, in_time: str, out_time: str,
) -> dict:
    if day > date.today():
        return {"valid": False, "reason": "Cannot regularize a future date"}

    att = db.query(models.Attendance).filter_by(emp_code=emp_code, date=day).first()
    if not att:
        return {"valid": False, "reason": f"No attendance record for {day}"}
    if att.status != "MISSING_PUNCH":
        return {"valid": False, "reason": f"Only MISSING_PUNCH days can be regularized (got {att.status})"}

    # Count existing (non-cancelled) regularizations in the same month.
    month_start = day.replace(day=1)
    next_month = (month_start + timedelta(days=32)).replace(day=1)
    count = db.query(models.Regularization).filter(
        models.Regularization.emp_code == emp_code,
        models.Regularization.date >= month_start,
        models.Regularization.date < next_month,
        models.Regularization.status != "Cancelled",
    ).count()
    if count >= MAX_PER_MONTH:
        return {"valid": False, "reason": f"Limit reached: max {MAX_PER_MONTH} per month"}

    if in_time >= out_time:
        return {"valid": False, "reason": "in_time must be before out_time"}

    return {"valid": True, "date": str(day), "in_time": in_time,
            "out_time": out_time, "existing_this_month": count}


@router.post("/{emp_code}/regularization/validate")
def validate_regularization(
    emp_code: str, body: RegularizationValidateRequest,
    db: Session = Depends(get_db),
) -> dict:
    return _validate_regularization(db, emp_code, body.date, body.in_time, body.out_time)


@router.post("/{emp_code}/regularization")
def create_regularization(
    emp_code: str, body: RegularizationValidateRequest,
    db: Session = Depends(get_db),
) -> dict:
    res = _validate_regularization(db, emp_code, body.date, body.in_time, body.out_time)
    if not res["valid"]:
        raise HTTPException(400, res["reason"])
    reg = models.Regularization(
        emp_code=emp_code, date=body.date,
        in_time=body.in_time, out_time=body.out_time,
        reason=body.reason, status="Pending",
    )
    db.add(reg)
    db.commit()
    db.refresh(reg)
    return {"regularization_id": reg.id, "status": reg.status, **res}