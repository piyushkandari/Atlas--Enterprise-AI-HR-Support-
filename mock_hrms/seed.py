"""Seed the mock HRMS SQLite DB with 10 fake employees.

Run from project root:  python -m mock_hrms.seed
"""
import random
from datetime import date, timedelta

from .database import Base, engine, SessionLocal
from . import models

random.seed(42)

EMPLOYEES = [
    ("E001", "Alice Johnson", "alice.johnson@company.com", "Engineering", "Senior Engineer", "Bangalore", "E010"),
    ("E002", "Bob Smith",     "bob.smith@company.com",     "Engineering", "Engineer",        "Bangalore", "E001"),
    ("E003", "Carol Davis",   "carol.davis@company.com",   "Engineering", "Engineer",        "Bangalore", "E001"),
    ("E004", "David Lee",     "david.lee@company.com",     "HR",          "HR Manager",      "Mumbai",    None),
    ("E005", "Eve Wilson",    "eve.wilson@company.com",    "Sales",       "Sales Executive", "Delhi",     "E006"),
    ("E006", "Frank Miller",  "frank.miller@company.com",  "Sales",       "Sales Manager",   "Delhi",     None),
    ("E007", "Grace Kim",     "grace.kim@company.com",     "Finance",     "Analyst",         "Mumbai",    "E008"),
    ("E008", "Henry Brown",   "henry.brown@company.com",   "Finance",     "Finance Manager", "Mumbai",    None),
    ("E009", "Ivy Chen",      "ivy.chen@company.com",      "Engineering", "QA Engineer",     "Bangalore", "E001"),
    ("E010", "Jack Taylor",   "jack.taylor@company.com",   "Engineering", "VP Engineering",  "Bangalore", None),
]

HOLIDAY_TEMPLATE = [
    ((1, 1),  "New Year's Day"),
    ((1, 26), "Republic Day"),
    ((3, 14), "Holi"),
    ((5, 1),  "May Day"),
    ((8, 15), "Independence Day"),
    ((10, 2), "Gandhi Jayanti"),
    ((12, 25), "Christmas"),
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # wipe tables so re-running is safe
        for m in (models.Holiday, models.Regularization, models.Attendance,
                  models.LeaveRequest, models.LeaveBalance, models.PFRecord,
                  models.Payslip, models.Employee):
            db.query(m).delete()
        db.commit()

        today = date.today()

        # employees
        for code, name, email, dept, desig, loc, mgr in EMPLOYEES:
            db.add(models.Employee(emp_code=code, name=name, email=email,
                                   department=dept, designation=desig,
                                   location=loc, manager_code=mgr))
        db.commit()

        # holidays for this year + next
        for y in (today.year, today.year + 1):
            for (mo, d), name in HOLIDAY_TEMPLATE:
                db.add(models.Holiday(date=date(y, mo, d), name=name, location="ALL"))
        db.commit()
        holiday_dates = {h.date for h in db.query(models.Holiday).all()}

        # payslips + PF for last 6 months
        for code, *_ in EMPLOYEES:
            base = 30000.0 + int(code[1:]) * 2000.0
            for i in range(6):
                m, y = today.month - i, today.year
                while m <= 0:
                    m += 12
                    y -= 1
                hra = round(base * 0.40, 2)
                bonus = 5000.0 if m == 12 else 0.0
                deductions = 3000.0
                db.add(models.Payslip(emp_code=code, month=m, year=y,
                                      basic=base, hra=hra, bonus=bonus,
                                      deductions=deductions,
                                      net_pay=base + hra + bonus - deductions))
                db.add(models.PFRecord(emp_code=code, month=m, year=y,
                                       employee_contribution=round(base * 0.12, 2),
                                       employer_contribution=round(base * 0.12, 2)))

        # leave balances
        for code, *_ in EMPLOYEES:
            db.add(models.LeaveBalance(emp_code=code, leave_type="Casual", total=12, used=random.randint(0, 5)))
            db.add(models.LeaveBalance(emp_code=code, leave_type="Sick",   total=8,  used=random.randint(0, 3)))
            db.add(models.LeaveBalance(emp_code=code, leave_type="Earned", total=15, used=random.randint(0, 5)))

        # attendance for last 60 days
        for code, *_ in EMPLOYEES:
            missing_budget = 4
            for i in range(60):
                d = today - timedelta(days=i)
                if d.weekday() >= 5:
                    db.add(models.Attendance(emp_code=code, date=d, status="WEEKEND"))
                elif d in holiday_dates:
                    db.add(models.Attendance(emp_code=code, date=d, status="HOLIDAY"))
                else:
                    pin = f"09:{random.randint(0, 59):02d}"
                    pout = f"18:{random.randint(0, 59):02d}"
                    if missing_budget > 0 and random.random() < 0.08:
                        missing_budget -= 1
                        db.add(models.Attendance(emp_code=code, date=d,
                                                 punch_in=pin, punch_out=None,
                                                 status="MISSING_PUNCH"))
                    else:
                        db.add(models.Attendance(emp_code=code, date=d,
                                                 punch_in=pin, punch_out=pout,
                                                 status="PRESENT"))

        # a couple of sample leave requests
        db.add(models.LeaveRequest(emp_code="E005", leave_type="Casual",
                                   from_date=today - timedelta(days=20),
                                   to_date=today - timedelta(days=18),
                                   days=3, reason="Family function", status="Approved"))
        next_15 = (today.replace(day=1) + timedelta(days=32)).replace(day=15)
        db.add(models.LeaveRequest(emp_code="E007", leave_type="Sick",
                                   from_date=next_15, to_date=next_15 + timedelta(days=1),
                                   days=2, reason="Medical", status="Pending"))

        db.commit()
        print(f"Seeded. Employees: {len(EMPLOYEES)}, Holidays: {len(holiday_dates)}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()