from fastapi import APIRouter
from backend.api.v1.endpoints import auth, chat, config

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(config.router, prefix="/config", tags=["Configuration"])
