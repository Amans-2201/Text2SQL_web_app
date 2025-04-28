import os
import sys
from pathlib import Path

# Get the absolute path to the project root
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException, Request # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from fastapi.responses import JSONResponse
from backend.api.v1.api import api_router
import logging
from backend.services.db_service import get_db_connection
# Ensure the correct path to the Token module
try:
    from backend.schemas.token import Token # type: ignore
except ModuleNotFoundError:
    raise ImportError("The module 'backend.schemas.token' could not be found. Ensure the file exists and the path is correct.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Text-to-SQL Chatbot API", version="1.0.0")

# --- CORS Middleware ---
# WARNING: Allow all origins for local development ease.
# For production, restrict origins to your frontend's actual URL.
origins = [
    "http://localhost",      # Allow requests from base localhost
    "http://localhost:3000", # Default React dev server port
    "http://127.0.0.1:3000",
    # Add any other origins you might use locally (e.g., different port)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Or ["*"] for testing, but be careful
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)

# --- Include API Routers ---
app.include_router(api_router, prefix="/api/v1") # Prefix all v1 routes with /api/v1

# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    logger.info("Root endpoint accessed.")
    return {"message": "Welcome to the Text-to-SQL Chatbot API"}

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers
    )

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except HTTPException as e:
        if e.status_code == 401:
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication failed"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        raise e