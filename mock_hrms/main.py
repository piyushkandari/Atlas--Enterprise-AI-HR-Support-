"""Mock HRMS FastAPI app."""
from fastapi import FastAPI
from .database import Base, engine
from .routers import employees, payslips, pf, leave, attendance, regularization, holidays

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mock HRMS", version="0.1.0",
              description="Fake SAP/HR backend. Port 8001.")


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}


app.include_router(employees.router)
app.include_router(payslips.router)
app.include_router(pf.router)
app.include_router(leave.router)
app.include_router(attendance.router)
app.include_router(regularization.router)
app.include_router(holidays.router)