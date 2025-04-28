# backend/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# Load .env file from the 'backend' directory specifically
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=dotenv_path)

class Settings(BaseSettings):
    # Database settings
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DATABASE_URL: str
    
    # Schema settings
    SCHEMA_QUERY: str
    
    # Auth settings
    JWT_SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    # AI settings
    GOOGLE_API_KEY: str
    
    class Config:
        env_file = ".env"

settings = Settings()