# backend/services/db_service.py
import psycopg2 # Or import mysql.connector or pyodbc
from psycopg2.extras import RealDictCursor
from backend.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Establishes a database connection."""
    try:
        conn = psycopg2.connect(settings.DATABASE_URL)
        logger.info("Database connection established successfully.")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise ConnectionError(f"Could not connect to the database: {e}")

def execute_query(query: str) -> tuple[list[dict], list[str]]:
    """
    Executes a SQL query and returns results and column names
    """
    try:
        with psycopg2.connect(settings.DATABASE_URL) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                results = cur.fetchall()
                if results:
                    # Convert results to list of dicts
                    data = [dict(row) for row in results]
                    # Get column names from the first row
                    columns = list(data[0].keys())
                    return data, columns
                return [], []
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise RuntimeError(f"Failed to execute query: {e}")

def get_db_schema() -> str:
    """
    Fetches database schema information directly from PostgreSQL
    """
    try:
        with psycopg2.connect(settings.DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # Query to get table and column information
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
                
                cur.execute(schema_query)
                tables = cur.fetchall()
                
                schema_info = []
                for table_name, columns in tables:
                    schema_info.append(f"Table: {table_name}\nColumns: {', '.join(columns)}")
                
                return '\n'.join(schema_info)

    except Exception as e:
        logger.error(f"Error fetching database schema: {e}")
        raise RuntimeError(f"Failed to fetch database schema: {e}")