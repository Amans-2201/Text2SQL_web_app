from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import mysql.connector
import psycopg2
from backend.core.config import settings
import os
import json
from backend.services.db_factory import get_db_connection
from backend.services.db_service import MySQLPool

router = APIRouter()

class DbConfig(BaseModel):
    dbType: str
    host: str
    port: str
    name: str
    user: str
    password: str

def test_mysql_connection(config: DbConfig) -> List[str]:
    try:
        conn = mysql.connector.connect(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password
        )
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in cursor.fetchall()]
        conn.close()
        return databases
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"MySQL connection failed: {str(e)}")

def test_postgres_connection(config: DbConfig) -> List[str]:
    try:
        conn = psycopg2.connect(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        databases = [db[0] for db in cursor.fetchall()]
        conn.close()
        return databases
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PostgreSQL connection failed: {str(e)}")

@router.post("/test-connection")
async def test_connection(config: DbConfig):
    try:
        if config.dbType == "mysql":
            conn = mysql.connector.connect(
                host=config.host,
                port=config.port,
                user=config.user,
                password=config.password
            )
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SHOW DATABASES")
            databases = [db['Database'] for db in cursor.fetchall()]
            cursor.close()
            conn.close()
            return {
                "status": "success",
                "databases": databases
            }
        elif config.dbType == "postgresql":
            # PostgreSQL connection code here
            return test_postgres_connection(config)
        else:
            raise HTTPException(status_code=400, detail="Unsupported database type")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/save")
async def save_config(config: DbConfig):
    """Save database configuration and switch to the selected database"""
    try:
        # Switch to the selected database
        mysql_pool = MySQLPool.get_instance()
        mysql_pool.switch_database(config.name)

        # Save configuration to .env file
        env_content = f"""
DB_TYPE={config.dbType}
DB_HOST={config.host}
DB_PORT={config.port}
DB_NAME={config.name}
DB_USER={config.user}
DB_PASSWORD={config.password}
"""
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        # Update settings
        settings.DB_NAME = config.name
        
        return {"status": "success", "message": "Configuration saved and database switched successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")