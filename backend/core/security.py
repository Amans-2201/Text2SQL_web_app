# backend/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from .config import settings

# OAuth2 scheme configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

# Update the dummy user database with correct credentials
DUMMY_USER_DB = {
    "chatbot_user": {
        "username": "chatbot_user",
        "password": "testing12345"  # Match the password you're using in frontend
    }
}

def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Authenticate user with simple password check"""
    user = DUMMY_USER_DB.get(username)
    if not user:
        return None
    if password != user["password"]:
        return None
    return user

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
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