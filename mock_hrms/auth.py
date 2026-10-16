"""Static API-key check for the mock HRMS.

Uses APIKeyHeader so Swagger UI shows an 'Authorize' button.
"""
import os
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("HRMS_API_KEY", "dev-hrms-key")

# auto_error=True makes FastAPI return 401 automatically if the header is missing.
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")
    return api_key