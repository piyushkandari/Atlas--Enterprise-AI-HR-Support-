from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import verify_api_key
from .. import models

router = APIRouter(
    prefix="/employees",
    tags=["attendance"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("/{emp_code}/attendance/{year}/{month}")
def get_attendance(
    emp_code: str, year: int, month: int, db: Session = Depends(get_db),
) -> dict:
    start = date(year, month, 1)
    next_month = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    end = next_month - timedelta(days=1)

    rows = db.query(models.Attendance).filter(
        models.Attendance.emp_code == emp_code,
        models.Attendance.date >= start,
        models.Attendance.date <= end,
    ).order_by(models.Attendance.date).all()

    summary = {"PRESENT": 0, "ABSENT": 0, "MISSING_PUNCH": 0,
               "WEEKEND": 0, "HOLIDAY": 0}
    records = []
    for r in rows:
        summary[r.status] = summary.get(r.status, 0) + 1
        records.append({
            "date": str(r.date), "punch_in": r.punch_in,
            "punch_out": r.punch_out, "status": r.status,
        })

    return {
        "emp_code": emp_code, "year": year, "month": month,
        "summary": summary, "records": records,
    }