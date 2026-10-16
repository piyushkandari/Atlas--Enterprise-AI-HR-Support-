"""FastAPI dependency: read the JWT and extract emp_code + role."""
from fastapi import Header, HTTPException
from .security import decode_token


def get_current_user(authorization: str = Header(..., alias="Authorization")) -> dict:
    """Returns {'emp_code': ..., 'role': ...}. The LLM never sees this."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authorization header must be 'Bearer <token>'")
    token = authorization[7:]
    try:
        payload = decode_token(token)
    except ValueError as e:
        raise HTTPException(401, str(e))
    return {"emp_code": payload["sub"], "role": payload.get("role", "employee")}