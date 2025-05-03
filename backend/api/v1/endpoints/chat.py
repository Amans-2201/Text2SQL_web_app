# backend/api/v1/endpoints/chat.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, Body
from typing import List, Dict, Any
from datetime import datetime, date  # Add this import
from backend.api.models.chat import ChatQuestion, ChatResponse, VisualizationSuggestion, QuerySuggestions
from backend.services import ai_service, validation_service
from backend.core.config import settings, reload_settings  # Add this import
from backend.api.v1.endpoints.config import DbConfig
import asyncio
import logging
import os
from backend.services.db_factory import get_db_connection, get_current_env_config, clear_connection_cache
from backend.core.config_utils import get_current_config
from backend.services.db_service import MySQLPool   # ← add this line

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/suggestions")
async def get_suggestions():
    """Get AI-generated questions based on database schema"""
    try:
        # Clear any cached connections to ensure fresh data
        clear_connection_cache()
        
        logger.info("Generating fresh Gemini-powered query suggestions")
        suggestions = await ai_service.generate_query_suggestions()
        
        # Return consistent response format
        return {"suggestions": suggestions}
    except Exception as e:
        logger.exception(f"Error generating suggestions: {e}")
        return {"suggestions": ["How many records are in each table?", 
                             "Show me a sample of data from each table", 
                             "What are the relationships between the main tables?", 
                             "Summarize the data distribution in the primary tables", 
                             "What interesting patterns exist in this dataset?"]}

@router.post("/ask", response_model=ChatResponse)
async def ask_question(chat_question: ChatQuestion):
    try:
        question = chat_question.question.lower().strip()
        
        # Handle special queries directly
        if question in ['how many tables in the database', 'show tables', 'list tables']:
            query = """
            SELECT COUNT(*) as table_count 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE()
            AND table_type = 'BASE TABLE';
            """
            try:
                logger.info(f"/ask: Executing query. Current settings.DB_TYPE: {settings.DB_TYPE}")
                db = get_db_connection()
                data, columns = await db.execute_query(query)
                logger.info("/ask: Query executed successfully.")
                count = data[0]['table_count'] if data else 0
                return ChatResponse(
                    query=query,
                    data=data,
                    columns=columns,
                    summary=f"There are {count} tables in the database."
                )
            except Exception as e:
                logger.error(f"Database query error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
            
        elif question in ['list all table names', 'show all tables', 'give table names']:
            query = """
            SELECT TABLE_NAME 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE()
            AND table_type = 'BASE TABLE'
            ORDER BY TABLE_NAME;
            """
            db = get_db_connection()
            data, columns = await db.execute_query(query)
            tables = [row['TABLE_NAME'] for row in data] if data else []
            return ChatResponse(
                query=query,
                data=data,
                columns=columns,
                summary=f"Here are all the tables: {', '.join(tables)}"
            )

        # For other queries, use AI generation
        generated_sql = await ai_service.generate_sql_from_prompt(
            chat_question.question,
            db_type=settings.DB_TYPE
        )
        
        logger.info(f"/ask: Executing validated query. Current settings.DB_TYPE: {settings.DB_TYPE}")
        db = get_db_connection()
        data, columns = await db.execute_query(generated_sql)
        logger.info("/ask: Query executed successfully.")
        
        # Get visualization suggestion
        visualization = await ai_service.suggest_visualization(
            data=data,
            columns=columns
        )

        summary = await ai_service.summarize_data(chat_question.question, data, columns)

        return ChatResponse(
            query=generated_sql,
            data=data,
            columns=columns,
            summary=summary,
            visualization=visualization
        )

    except Exception as e:
        logger.error(f"Error processing question: {e}")
        return ChatResponse(
            error=str(e),
            query=None,
            data=None,
            columns=None
        )

@router.post("/visualize")
async def create_visualization(
    data: List[Dict[str, Any]] = Body(...),
    columns: List[str] = Body(...),
    chart_type: str = Body(...)
):
    """Create visualization from data"""
    try:
        # Change to use the ai_service module's function
        visualization = await ai_service.suggest_visualization_with_type(
            data=data,
            columns=columns,
            preferred_type=chart_type
        )
        if visualization:
            return {"visualization": visualization}
        return {"error": "Could not create visualization from provided data"}
    except Exception as e:
        logger.error(f"Error creating visualization: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create visualization: {str(e)}"
        )

@router.get("/database-info")
async def get_database_info():
    """Get database name and list of tables"""
    try:
        # Clear connection cache and get fresh config
        clear_connection_cache()
        config = get_current_config()
        db_name = config.get("DB_NAME", "")
        db_type = config.get("DB_TYPE", "").lower()
        
        logger.info(f"Getting database info for {db_type}:{db_name}")
        
        # Get a fresh DB connection
        db = get_db_connection(use_cache=False)
        
        # Use the appropriate query based on DB type
        if db_type == "postgresql":
            query = """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name;
            """
            col_name = 'table_name'
        else:  # mysql
            query = """
            SELECT TABLE_NAME FROM information_schema.tables
            WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE'
            ORDER BY TABLE_NAME;
            """
            col_name = 'TABLE_NAME'
        
        # Execute query
        data, _ = await db.execute_query(query)
        tables = [row[col_name] for row in data] if data else []
        
        logger.info(f"Found tables for {db_name}: {tables}")
        
        return {
            "dbName": db_name,
            "tables": tables
        }
    except Exception as e:
        logger.exception(f"Error fetching database info: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch database info: {str(e)}"
        )

@router.get("/table-columns/{table_name}")
async def get_table_columns(table_name: str):
    """Get columns for a specific table"""
    try:
        # Get fresh config and connection
        config = get_current_config()
        db_type = config.get("DB_TYPE", "").lower()
        
        logger.info(f"Getting columns for table {table_name} in {db_type} database")
        
        # Get a fresh DB connection
        db = get_db_connection(use_cache=False)
        
        # Use appropriate query based on DB type
        if db_type == "postgresql":
            safe_table = table_name.replace("'", "''")
            query = f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = '{safe_table}'
            ORDER BY ordinal_position;
            """
        else:  # mysql
            safe_table = table_name.replace("'", "''")
            query = f"""
            SELECT COLUMN_NAME as column_name, DATA_TYPE as data_type
            FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = '{safe_table}'
            ORDER BY ORDINAL_POSITION;
            """
        
        # Execute query
        data, _ = await db.execute_query(query)
        
        # Format column info
        columns = [f"{row['column_name']} ({row['data_type']})" for row in data]
        
        logger.info(f"Found {len(columns)} columns for table {table_name}")
        
        return {
            "table": table_name,
            "columns": columns
        }
    except Exception as e:
        logger.exception(f"Error fetching columns for {table_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch columns: {str(e)}"
        )

@router.post("/save")
async def save_config(config: DbConfig):
    try:
        if config.dbType == "mysql":
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

        # Reload settings after saving .env
        reload_settings()

        return {"status": "success", "message": "Configuration saved and database switched successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save configuration: {str(e)}")

reload_settings()