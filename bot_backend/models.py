"""Bot backend tables. audit_log NEVER stores salary values."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    emp_code = Column(String, nullable=False)
    role = Column(String, default="employee")
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True)
    session_id = Column(String, index=True)
    emp_code = Column(String, index=True)
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True)
    emp_code = Column(String, index=True)
    category = Column(String)
    summary = Column(String)
    description = Column(Text)
    priority = Column(String)
    status = Column(String, default="Open")
    steps_tried = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True)
    emp_code = Column(String, index=True)
    tool_name = Column(String)
    args_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)