# backend/core/config.py
from pydantic_settings import BaseSettings
from typing import Literal
import os
from dotenv import load_dotenv
import sys

def get_application_path():
    """Get the path to the application directory, works both in dev and packaged"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_env():
    env_path = os.path.join(get_application_path(), '.env')
    load_dotenv(dotenv_path=env_path)

# Load .env file from the 'backend' directory specifically
load_env()

class Settings(BaseSettings):
    # Database settings
    DB_TYPE: Literal["postgresql", "mysql"] = "postgresql"
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DATABASE_URL: str = ""
    
    # MySQL specific settings
    MYSQL_DATABASE_URL: str = ""
    
    # Make JWT settings optional with defaults
    JWT_SECRET_KEY: str = "dummy_secret_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Google API Key
    GOOGLE_API_KEY: str
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Construct database URLs based on DB_TYPE
        if self.DB_TYPE == "postgresql":
            self.DATABASE_URL = f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        else:
            self.MYSQL_DATABASE_URL = f"mysql+mysqlconnector://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def active_database_url(self) -> str:
        """Returns the appropriate database URL based on DB_TYPE"""
        if self.DB_TYPE == "postgresql":
            return self.DATABASE_URL
        elif self.DB_TYPE == "mysql":
            return self.MYSQL_DATABASE_URL
        raise ValueError(f"Unsupported database type: {self.DB_TYPE}")
    
    @property
    def schema_query(self) -> str:
        """Returns the appropriate schema query based on DB_TYPE"""
        if self.DB_TYPE == "postgresql":
            return """
                SELECT 
                    table_name,
                    string_agg(
                        column_name || ' (' || data_type || ')', 
                        ', ' ORDER BY ordinal_position
                    ) as columns
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                GROUP BY table_name;
            """
        else:  # MySQL
            return """
                SELECT 
                    TABLE_NAME,
                    GROUP_CONCAT(
                        CONCAT(COLUMN_NAME, ' (', 
                            CASE 
                                WHEN DATA_TYPE = 'varchar' THEN 'VARCHAR'
                                WHEN DATA_TYPE = 'double' THEN 'DECIMAL'
                                ELSE UPPER(DATA_TYPE)
                            END, ')')
                        ORDER BY ORDINAL_POSITION
                    ) as columns
                FROM information_schema.columns 
                WHERE table_schema = DATABASE()
                GROUP BY TABLE_NAME;
            """
    
    # Other settings remain the same
    SCHEMA_QUERY: str
    
    class Config:
        env_file = ".env"

settings = Settings()