"""SQLAlchemy models for the mock HRMS."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from .database import Base


class Employee(Base):
    __tablename__ = "employees"
    emp_code = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    department = Column(String)
    designation = Column(String)
    location = Column(String)
    manager_code = Column(String, ForeignKey("employees.emp_code"), nullable=True)


class Payslip(Base):
    __tablename__ = "payslips"
    id = Column(Integer, primary_key=True)
    emp_code = Column(String, ForeignKey("employees.emp_code"), index=True)
    month = Column(Integer)   # 1..12
    year = Column(Integer)
    basic = Column(Float)
    hra = Column(Float)
    bonus = Column(Float, default=0.0)
    deductions = Column(Float, default=0.0)
    net_pay = Column(Float)


class PFRecord(Base):
    __tablename__ = "pf_records"
    id = Column(Integer, primary_key=True)
    emp_code = Column(String, ForeignKey("employees.emp_code"), index=True)
    month = Column(Integer)
    year = Column(Integer)
    employee_contribution = Column(Float)
    employer_contribution = Column(Float)


class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    id = Column(Integer, primary_key=True)
    emp_code = Column(String, ForeignKey("employees.emp_code"), index=True)
    leave_type = Column(String)          # Casual / Sick / Earned
    total = Column(Integer)
    used = Column(Integer, default=0)


class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    id = Column(Integer, primary_key=True)
    emp_code = Column(String, ForeignKey("employees.emp_code"), index=True)
    leave_type = Column(String)
    from_date = Column(Date)
    to_date = Column(Date)
    days = Column(Integer)
    reason = Column(String, default="")
    status = Column(String, default="Pending")   # Pending/Approved/Rejected/Cancelled
    created_at = Column(DateTime, default=datetime.utcnow)


class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True)
    emp_code = Column(String, ForeignKey("employees.emp_code"), index=True)
    date = Column(Date, index=True)
    punch_in = Column(String, nullable=True)     # "09:15" or None
    punch_out = Column(String, nullable=True)
    # PRESENT / ABSENT / MISSING_PUNCH / WEEKEND / HOLIDAY
    status = Column(String)


class Regularization(Base):
    __tablename__ = "regularizations"
    id = Column(Integer, primary_key=True)
    emp_code = Column(String, ForeignKey("employees.emp_code"), index=True)
    date = Column(Date)
    in_time = Column(String)
    out_time = Column(String)
    reason = Column(String, default="")
    status = Column(String, default="Pending")
    created_at = Column(DateTime, default=datetime.utcnow)


class Holiday(Base):
    __tablename__ = "holidays"
    id = Column(Integer, primary_key=True)
    date = Column(Date, index=True)
    name = Column(String)
    location = Column(String, default="ALL")     # "ALL" or a city