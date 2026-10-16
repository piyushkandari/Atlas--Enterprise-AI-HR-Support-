from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import verify_api_key
from .. import models

router = APIRouter(
    prefix="/employees",
    tags=["payslips"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("/{emp_code}/payslips/{year}/{month}")
def get_payslip(
    emp_code: str, year: int, month: int, db: Session = Depends(get_db),
) -> dict:
    p = db.query(models.Payslip).filter_by(
        emp_code=emp_code, year=year, month=month
    ).first()
    if not p:
        raise HTTPException(404, f"No payslip for {emp_code} {year}-{month:02d}")
    return {
        "emp_code": p.emp_code, "month": p.month, "year": p.year,
        "basic": p.basic, "hra": p.hra, "bonus": p.bonus,
        "deductions": p.deductions, "net_pay": p.net_pay,
    }