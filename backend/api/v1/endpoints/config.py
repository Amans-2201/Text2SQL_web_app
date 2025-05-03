from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
import mysql.connector
import psycopg2
from backend.core.config_utils import get_current_config, save_config, get_config_paths

logger = logging.getLogger(__name__)
router = APIRouter()

# Log paths on startup for debugging
logger.info(f"Config paths: {get_config_paths()}")

class DbConfig(BaseModel):
    dbType: str
    host: str
    port: str
    name: str
    user: str
    password: str

@router.post("/test-connection")
async def test_connection(config: DbConfig):
    """Test database connection with provided configuration"""
    logger.info(f"Testing connection: type={config.dbType}, host={config.host}, db={config.name}")
    
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
            logger.info(f"MySQL connection successful. Found databases: {databases}")
            return {
                "status": "success",
                "databases": databases
            }
        elif config.dbType == "postgresql":
            conn = psycopg2.connect(
                host=config.host,
                port=config.port,
                user=config.user,
                password=config.password,
                dbname=config.name
            )
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
            databases = [db[0] for db in cursor.fetchall()]
            conn.close()
            logger.info(f"PostgreSQL connection successful. Found databases: {databases}")
            return {
                "status": "success",
                "databases": databases
            }
        else:
            raise HTTPException(status_code=400, detail="Unsupported database type")
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/save")
async def save_configuration(config: DbConfig):
    """Save database configuration"""
    logger.info(f"Saving configuration: type={config.dbType}, host={config.host}, db={config.name}")
    
    try:
        # Create config dict
        config_dict = {
            "DB_TYPE": config.dbType,
            "DB_HOST": config.host,
            "DB_PORT": config.port,
            "DB_NAME": config.name,
            "DB_USER": config.user,
            "DB_PASSWORD": config.password
        }
        
        # Save config to both .env and JSON
        success = save_config(config_dict)
        if not success:
            raise Exception("Failed to save configuration")
        
        # Test the connection with the new config
        current = get_current_config()
        logger.info(f"Verified current config after save: {current}")
        
        return {"status": "success", "message": "Configuration saved successfully"}
    except Exception as e:
        logger.exception(f"Failed to save configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")

@router.get("/current")
async def get_current_db_config():
    """Get current database configuration (for debugging)"""
    config = get_current_config()
    # Mask password
    if "DB_PASSWORD" in config:
        config["DB_PASSWORD"] = "********"
    return {"config": config, "paths": get_config_paths()}