# backend/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from .config import settings

# OAuth2 scheme configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")  # Added leading slash

# Simple user database - for development only
DUMMY_USER_DB = {
    "testuser": {
        "username": "testuser",
        "password": "password"  # Plain text password for development
    }
}

def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user with simple password check"""
    user = DUMMY_USER_DB.get(username)
    if not user:
        return None
    if password != user["password"]:  # Simple password comparison
        return None
    return user

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Validate JWT token and return current user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = DUMMY_USER_DB.get(username)
    if user is None:
        raise credentials_exception
    return user