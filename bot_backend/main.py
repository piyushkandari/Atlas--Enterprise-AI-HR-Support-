"""Bot backend FastAPI app on port 8000."""
from fastapi import FastAPI
from .database import Base, engine
from .routers import auth, chat

Base.metadata.create_all(bind=engine)

app = FastAPI(title="HR Bot Backend", version="0.1.0",
              description="JWT login + LangGraph HR agent. Port 8000.")


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(chat.router)