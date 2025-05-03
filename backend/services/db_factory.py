import asyncio
from typing import Protocol, Tuple, List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import mysql.connector
import logging
import os
from backend.core.config_utils import get_current_config

logger = logging.getLogger(__name__)

# --- Protocol and Connection Classes ---
class DatabaseConnection(Protocol):
    """Database connection interface"""
    async def execute_query(self, query: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        pass
    
    async def get_schema(self) -> str:
        pass

class PostgresConnection:
    """PostgreSQL connection implementation"""
    def __init__(self, config: Dict[str, str]):
        self.config = config
        logger.info(f"PostgresConnection initialized with DB: {config.get('DB_NAME', 'unknown')}")
    
    def connect(self):
        """Create a new PostgreSQL connection"""
        db_name = self.config.get("DB_NAME", "")
        host = self.config.get("DB_HOST", "localhost")
        port = self.config.get("DB_PORT", "5432")
        user = self.config.get("DB_USER", "")
        password = self.config.get("DB_PASSWORD", "")
        
        logger.info(f"Connecting to PostgreSQL: {host}:{port}/{db_name} as {user}")
        
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                dbname=db_name,
                user=user,
                password=password
            )
            logger.info("PostgreSQL connection successful")
            return conn
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise ConnectionError(f"Failed to connect to PostgreSQL: {str(e)}")
    
    async def execute_query(self, query: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Execute a query and return results"""
        conn = None
        try:
            conn = self.connect()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                logger.debug(f"Executing query: {query}")
                cur.execute(query)
                if cur.description:
                    results = cur.fetchall()
                    data = [dict(row) for row in results]
                    columns = [desc.name for desc in cur.description]
                    return data, columns
                return [], []
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    async def get_schema(self) -> str:
        """Get database schema"""
        schema_query = """
        SELECT 
            t.table_name,
            string_agg(c.column_name || ' (' || 
                CASE 
                    WHEN c.data_type = 'character varying' THEN 'VARCHAR'
                    WHEN c.data_type = 'double precision' THEN 'DECIMAL'
                    ELSE upper(c.data_type)
                END || ')', ', ' ORDER BY c.ordinal_position
            ) as columns
        FROM information_schema.tables t
        JOIN information_schema.columns c 
            ON t.table_name = c.table_name AND t.table_schema = c.table_schema
        WHERE t.table_schema = 'public'
        AND t.table_type = 'BASE TABLE'
        GROUP BY t.table_name;
        """
        try:
            data, _ = await self.execute_query(schema_query)
            schema_info = []
            for row in data:
                schema_info.append(f"Table: {row['table_name']}\nColumns: {row['columns']}")
            return '\n'.join(schema_info)
        except Exception as e:
            logger.error(f"Schema fetch error: {e}")
            raise

class MySQLConnection:
    """MySQL connection implementation"""
    def __init__(self, config: Dict[str, str]):
        self.config = config
        logger.info(f"MySQLConnection initialized with DB: {config.get('DB_NAME', 'unknown')}")
    
    def connect(self):
        """Create a new MySQL connection"""
        db_name = self.config.get("DB_NAME", "")
        host = self.config.get("DB_HOST", "localhost")
        port = self.config.get("DB_PORT", "3306")
        user = self.config.get("DB_USER", "")
        password = self.config.get("DB_PASSWORD", "")
        
        logger.info(f"Connecting to MySQL: {host}:{port}/{db_name} as {user}")
        
        try:
            conn = mysql.connector.connect(
                host=host,
                port=port,
                database=db_name,
                user=user,
                password=password
            )
            logger.info("MySQL connection successful")
            return conn
        except Exception as e:
            logger.error(f"MySQL connection failed: {e}")
            raise ConnectionError(f"Failed to connect to MySQL: {str(e)}")
    
    async def execute_query(self, query: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Execute a query and return results"""
        conn = None
        cursor = None
        try:
            conn = self.connect()
            cursor = conn.cursor(dictionary=True)
            logger.debug(f"Executing query: {query}")
            cursor.execute(query)
            results = cursor.fetchall() if cursor.description else []
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            return results, columns
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    async def get_schema(self) -> str:
        """Get database schema"""
        schema_query = """
        SELECT 
            TABLE_NAME,
            GROUP_CONCAT(
                CONCAT(COLUMN_NAME, ' (', 
                CASE 
                    WHEN DATA_TYPE = 'varchar' THEN 'VARCHAR'
                    WHEN DATA_TYPE = 'double' THEN 'DECIMAL'
                    ELSE UPPER(DATA_TYPE)
                END, ')')
                ORDER BY ORDINAL_POSITION SEPARATOR ', '
            ) as columns
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
        GROUP BY TABLE_NAME;
        """
        try:
            data, _ = await self.execute_query(schema_query)
            schema_info = []
            for row in data:
                schema_info.append(f"Table: {row['TABLE_NAME']}\nColumns: {row['columns']}")
            return '\n'.join(schema_info)
        except Exception as e:
            logger.error(f"Schema fetch error: {e}")
            raise

# --- Factory Function with Fresh Config Reading ---
_connection_cache = {}

def get_db_connection(use_cache=False) -> DatabaseConnection:
    """Get database connection based on current configuration"""
    # Always read the current config
    config = get_current_config()
    db_type = config.get("DB_TYPE", "").lower()
    db_name = config.get("DB_NAME", "unknown")
    
    # Generate cache key
    cache_key = f"{db_type}:{db_name}"
    
    # Clear cache if requested
    if not use_cache:
        if cache_key in _connection_cache:
            logger.info(f"Clearing connection cache for {cache_key}")
            _connection_cache.pop(cache_key, None)
    
    # Use cached connection if available and requested
    if use_cache and cache_key in _connection_cache:
        logger.info(f"Using cached connection for {db_type}:{db_name}")
        return _connection_cache[cache_key]
    
    # Create new connection
    logger.info(f"Creating new connection for {db_type}:{db_name}")
    
    if db_type == "postgresql":
        connection = PostgresConnection(config)
    elif db_type == "mysql":
        connection = MySQLConnection(config)
    else:
        logger.error(f"Unsupported database type: {db_type}")
        raise ValueError(f"Unsupported database type: {db_type}")
    
    # Cache connection
    if use_cache:
        _connection_cache[cache_key] = connection
    
    return connection

def clear_connection_cache():
    """Clear the connection cache"""
    global _connection_cache
    logger.info("Clearing entire connection cache")
    _connection_cache = {}

# Add this function to provide backward compatibility
def get_current_env_config():
    """Legacy function for backward compatibility"""
    logger.warning("get_current_env_config() is deprecated, use get_current_config() instead")
    return get_current_config()