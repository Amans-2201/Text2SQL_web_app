# backend/api/v1/endpoints/chat.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, Body
from typing import List, Dict, Any
from datetime import datetime, date  # Add this import
from backend.api.models.chat import ChatQuestion, ChatResponse, VisualizationSuggestion, QuerySuggestions
from backend.services import ai_service, db_service, validation_service
from backend.core.config import settings  # Add this import
import asyncio
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/suggestions", response_model=QuerySuggestions)
async def get_query_suggestions():
    """Get smart query suggestions based on database schema"""
    try:
        suggestions = await ai_service.generate_query_suggestions()
        return QuerySuggestions(suggestions=suggestions)
    except Exception as e:
        logger.error(f"Error generating suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
                data, columns = await db_service.execute_query(query)
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
            data, columns = await db_service.execute_query(query)
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
        
        data, columns = await db_service.execute_query(generated_sql)
        
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
        # Get database name from settings
        db_name = settings.DB_NAME

        # Get list of tables using the existing db service
        query = """
        SELECT TABLE_NAME 
        FROM information_schema.tables 
        WHERE table_schema = DATABASE()
        AND table_type = 'BASE TABLE'
        ORDER BY TABLE_NAME;
        """
        data, _ = await db_service.execute_query(query)
        tables = [row['TABLE_NAME'] for row in data] if data else []

        return {
            "dbName": db_name,
            "tables": tables
        }
    except Exception as e:
        logger.error(f"Error fetching database info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch database information: {str(e)}"
        )

@router.get("/table-columns/{table_name}")
async def get_table_columns(table_name: str):
    """Get columns for a specific table"""
    try:
        query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_KEY
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION;
        """
        
        data, _ = await db_service.execute_query(query, values=[table_name])
        
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No columns found for table {table_name}"
            )
        
        # Format column information
        columns = [
            f"{row['COLUMN_NAME']} ({row['DATA_TYPE'].upper()}){' [KEY]' if row['COLUMN_KEY'] == 'PRI' else ''}"
            for row in data
        ]
        
        return {
            "tableName": table_name,
            "columns": columns
        }
    except Exception as e:
        logger.error(f"Error fetching columns for table {table_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch columns: {str(e)}"
        )