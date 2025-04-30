# backend/services/db_service.py
from typing import Tuple, List, Dict, Any
import mysql.connector
from mysql.connector import pooling
import logging
from contextlib import asynccontextmanager
from backend.core.config import settings

logger = logging.getLogger(__name__)

class MySQLPool:
    _instance = None
    _pool = None
    _current_db = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.initialize_pool()

    def initialize_pool(self, database_name=None):
        """Initialize or reinitialize the connection pool with a new database"""
        if database_name:
            self._current_db = database_name
        else:
            self._current_db = settings.DB_NAME

        # Close existing pool if it exists
        if self._pool:
            try:
                self._pool.close()
            except:
                pass

        self._pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=5,
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=self._current_db
        )

    def switch_database(self, new_database):
        """Switch to a different database"""
        self.initialize_pool(new_database)

async def get_db_connection():
    """Get database connection with better error handling"""
    try:
        connection = MySQLPool.get_instance()._pool.get_connection()
        return connection
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise Exception(f"Failed to connect to database: {str(e)}")

@asynccontextmanager
async def get_db():
    """Async context manager for database connections"""
    connection = await get_db_connection()
    try:
        yield connection
    finally:
        connection.close()

async def execute_query(query: str, values: List[Any] = None) -> Tuple[List[Dict], List[str]]:
    """Execute SQL query and return results"""
    try:
        async with get_db() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, values or ())
            data = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            return list(data), columns
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise

async def get_db_schema() -> str:
    """Fetches database schema information"""
    try:
        query = """
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
        data, _ = await execute_query(query)
        schema_info = []
        for row in data:
            schema_info.append(f"Table: {row['TABLE_NAME']}\nColumns: {row['columns']}")
        return '\n'.join(schema_info)
    except Exception as e:
        logger.error(f"Error fetching database schema: {e}")
        raise RuntimeError(f"Failed to fetch database schema: {e}")

async def refresh_schema_info():
    """Refresh schema information after database switch"""
    try:
        query = """
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
        data, _ = await execute_query(query)
        return data
    except Exception as e:
        logger.error(f"Error refreshing schema info: {e}")
        raise RuntimeError(f"Failed to refresh schema info: {e}")