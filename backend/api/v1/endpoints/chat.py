# backend/api/v1/endpoints/chat.py
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, date  # Add this import
from backend.api.models.chat import ChatQuestion, ChatResponse, VisualizationSuggestion
from backend.core.security import get_current_user
from backend.services import ai_service, db_service, validation_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    chat_question: ChatQuestion,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Verify authentication
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Generate SQL
        generated_sql = ai_service.generate_sql_from_prompt(chat_question.question)
        
        # Execute query
        data, columns = db_service.execute_query(generated_sql)
        
        # Generate summary if there's data
        summary = None
        if data:
            try:
                summary = ai_service.summarize_data(chat_question.question, data, columns)
            except Exception as e:
                logger.warning(f"Summary generation failed: {e}")
                summary = "Could not generate summary."
        else:
            summary = "No data found."

        # Suggest visualization
        visualization = suggest_visualization(columns, data) if data else None

        # Return response
        return ChatResponse(
            query=generated_sql,
            data=data,
            columns=columns,
            summary=summary,
            visualization=visualization,
            error=None
        )
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        return ChatResponse(
            error=str(e),
            query=None,
            data=None,
            columns=None,
            summary=None,
            visualization=None
        )

# Basic logic to suggest visualization based on data types/counts
def suggest_visualization(columns: list[str], data: list[dict]) -> VisualizationSuggestion | None:
    if not data or not columns:
        return VisualizationSuggestion(type='table') # Default to table if no data/cols

    # Simple rules (can be expanded significantly)
    numeric_cols = []
    category_cols = []
    date_cols = [] # Basic date check

    # Rudimentary type detection based on first row (improve with actual DB types if available)
    first_row = data[0]
    for col in columns:
        val = first_row.get(col)
        if isinstance(val, (int, float)):
            numeric_cols.append(col)
        # Now datetime.date and datetime.datetime are properly imported
        elif isinstance(val, (date, datetime)) or (isinstance(val, str) and len(val) > 8 and '-' in val):
             date_cols.append(col)
        elif isinstance(val, str):
            category_cols.append(col)

    num_numeric = len(numeric_cols)
    num_category = len(category_cols)
    num_date = len(date_cols)

    if num_numeric == 1 and (num_category == 1 or num_date == 1):
        x_axis = category_cols[0] if category_cols else date_cols[0]
        y_axis = numeric_cols[0]
        chart_type = 'bar' if num_category == 1 else 'line' # Line for dates, bar for categories
        return VisualizationSuggestion(type=chart_type, x_axis=x_axis, y_axis=y_axis)
    elif num_numeric > 1 and (num_category == 1 or num_date == 1):
         # Could suggest multi-line/bar or stacked bar, default to table for now
         return VisualizationSuggestion(type='table')
    else:
        # Default to table for other cases (e.g., multiple numerics, multiple categories)
        return VisualizationSuggestion(type='table')