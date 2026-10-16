from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import verify_api_key
from .. import models

router = APIRouter(
    prefix="/employees",
    tags=["employees"],
    dependencies=[Depends(verify_api_key)],
)


def _emp(e: models.Employee) -> dict:
    return {
        "emp_code": e.emp_code, "name": e.name, "email": e.email,
        "department": e.department, "designation": e.designation,
        "location": e.location, "manager_code": e.manager_code,
    }


@router.get("/{emp_code}")
def get_employee(emp_code: str, db: Session = Depends(get_db)) -> dict:
    emp = db.query(models.Employee).filter_by(emp_code=emp_code).first()
    if not emp:
        raise HTTPException(404, "Employee not found")
    return _emp(emp)


@router.get("/{emp_code}/manager")
def get_manager(emp_code: str, db: Session = Depends(get_db)) -> dict:
    emp = db.query(models.Employee).filter_by(emp_code=emp_code).first()
    if not emp:
        raise HTTPException(404, "Employee not found")
    if not emp.manager_code:
        return {"manager": None, "message": "No manager assigned"}
    mgr = db.query(models.Employee).filter_by(emp_code=emp.manager_code).first()
    return {"manager": _emp(mgr) if mgr else None}


@router.get("/{emp_code}/team")
def get_team(emp_code: str, db: Session = Depends(get_db)) -> dict:
    team = db.query(models.Employee).filter(
        models.Employee.manager_code == emp_code
    ).all()
    return {"team": [_emp(e) for e in team], "count": len(team)}