import asyncio
from typing import Protocol, Tuple, List, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import mysql.connector
from mysql.connector import pooling
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)

class DatabaseConnection(Protocol):
    async def execute_query(self, query: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        pass
    
    async def get_schema(self) -> str:
        pass

    async def get_databases(self):
        """Get list of available databases"""
        try:
            if self.db_type == "mysql":
                query = "SHOW DATABASES"
            else:
                query = "SELECT datname FROM pg_database WHERE datistemplate = false;"
            
            data, _ = await self.execute_query(query)
            return [db['Database'] if self.db_type == "mysql" else db['datname'] 
                    for db in data]
        except Exception as e:
            raise Exception(f"Failed to fetch databases: {str(e)}")

class PostgresConnection:
    def connect(self):
        return psycopg2.connect(settings.DATABASE_URL)

    def _execute_schema_query(self, query: str) -> str:
        """Execute schema query and format results"""
        try:
            with self.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    results = cur.fetchall()
                    
                    schema_info = []
                    for table_name, columns in results:
                        if isinstance(columns, list):
                            cols = ', '.join(columns)
                        else:
                            cols = columns
                        schema_info.append(f"Table: {table_name}\nColumns: {cols}")
                    
                    return '\n'.join(schema_info)
        except Exception as e:
            logger.error(f"Schema query execution error: {e}")
            raise

    async def execute_query(self, query: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        try:
            with self.connect() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query)
                    results = cur.fetchall()
                    if results:
                        data = [dict(row) for row in results]
                        columns = list(data[0].keys())
                        return data, columns
                    return [], []
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise

    async def get_schema(self) -> str:
        schema_query = """
            SELECT 
                t.table_name,
                array_agg(
                    c.column_name || ' (' || 
                    CASE 
                        WHEN c.data_type = 'character varying' THEN 'VARCHAR'
                        WHEN c.data_type = 'double precision' THEN 'DECIMAL'
                        ELSE upper(c.data_type)
                    END || ')'
                    ORDER BY c.ordinal_position
                ) as columns
            FROM information_schema.tables t
            JOIN information_schema.columns c 
                ON t.table_name = c.table_name
            WHERE t.table_schema = 'public'
            AND t.table_type = 'BASE TABLE'
            GROUP BY t.table_name;
        """
        return self._execute_schema_query(schema_query)

class MySQLConnection:
    def __init__(self):
        self.db_type = "mysql"
        self.pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=5,
            host=settings.DB_HOST,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME
        )

    async def execute_query(self, query: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        try:
            connection = self.pool.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query)
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            return list(results), columns
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()

    async def get_schema(self) -> str:
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
        try:
            data, _ = await self.execute_query(query)
            schema_info = []
            for row in data:
                schema_info.append(f"Table: {row['TABLE_NAME']}\nColumns: {row['columns']}")
            return '\n'.join(schema_info)
        except Exception as e:
            logger.error(f"Schema fetch error: {e}")
            raise

    async def get_databases(self) -> List[str]:
        """Get list of available databases"""
        try:
            connection = self.pool.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SHOW DATABASES")
            results = cursor.fetchall()
            return [db['Database'] for db in results]
        except Exception as e:
            logger.error(f"Failed to fetch databases: {e}")
            raise Exception(f"Failed to fetch databases: {str(e)}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()

def get_db_connection() -> DatabaseConnection:
    """Factory function to get the appropriate database connection"""
    if settings.DB_TYPE == "postgresql":
        return PostgresConnection()
    elif settings.DB_TYPE == "mysql":
        return MySQLConnection()
    else:
        raise ValueError(f"Unsupported database type: {settings.DB_TYPE}")