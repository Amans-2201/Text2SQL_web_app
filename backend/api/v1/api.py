from fastapi import APIRouter
from backend.api.v1.endpoints import auth, chat

api_router = APIRouter()

# Include endpoint routers with correct prefixes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
