from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import verify_api_key
from .. import models

router = APIRouter(prefix="/holidays", tags=["holidays"],
                   dependencies=[Depends(verify_api_key)])


@router.get("")
def list_holidays(from_date: date, to_date: date, location: str = "ALL",
                  db: Session = Depends(get_db)) -> dict:
    rows = db.query(models.Holiday).filter(
        models.Holiday.date >= from_date,
        models.Holiday.date <= to_date,
        models.Holiday.location.in_(["ALL", location])).order_by(models.Holiday.date).all()
    return {"from": str(from_date), "to": str(to_date),
            "holidays": [{"date": str(h.date), "name": h.name} for h in rows]}