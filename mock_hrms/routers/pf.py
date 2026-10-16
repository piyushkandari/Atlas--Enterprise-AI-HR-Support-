from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import verify_api_key
from .. import models

router = APIRouter(prefix="/employees", tags=["pf"],
                   dependencies=[Depends(verify_api_key)])


@router.get("/{emp_code}/pf")
def get_pf(emp_code: str, db: Session = Depends(get_db)) -> dict:
    recs = db.query(models.PFRecord).filter_by(emp_code=emp_code).order_by(
        models.PFRecord.year, models.PFRecord.month).all()
    te = sum(r.employee_contribution for r in recs)
    tr = sum(r.employer_contribution for r in recs)
    return {"emp_code": emp_code,
            "total_employee_contribution": round(te, 2),
            "total_employer_contribution": round(tr, 2),
            "balance": round(te + tr, 2)}