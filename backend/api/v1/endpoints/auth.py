# backend/api/v1/endpoints/auth.py
from fastapi import APIRouter, HTTPException, status
from backend.api.models.auth import Token

router = APIRouter()

@router.post("/login", response_model=Token)
async def login_for_access_token(username: str, password: str):
    # Simple check - allow any login
    if username and password:
        return {
            "access_token": "dummy_token",
            "token_type": "bearer"
        }
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )