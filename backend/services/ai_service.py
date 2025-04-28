# backend/services/ai_service.py
from backend.services.db_service import get_db_schema
import google.generativeai as genai
from backend.core.config import settings
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure the Google AI client
try:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    # Use the stable model version
    model = genai.GenerativeModel('gemini-2.0-flash')
    logger.info("Google AI SDK configured successfully.")
except Exception as e:
    logger.error(f"Failed to configure Google AI SDK: {e}")
    raise RuntimeError(f"Failed to configure Google AI: {e}")

def generate_sql_from_prompt(question: str, db_type: str = "PostgreSQL") -> str:
    """Generates SQL query from natural language using Google AI."""
    if not model:
        raise RuntimeError("Google AI SDK not configured.")
    
    try:
        # Fetch current schema from database
        schema = get_db_schema()
        
        prompt = f"""
        You are a SQL query generator. Follow these instructions precisely:
        
        Database Schema:
        {schema}

        Important Rules:
        1. Use ONLY the columns exactly as they appear in the schema
        2. Tables and columns are case-sensitive - use exact names
        3. For revenue/sales calculations, use the 'amount' column from the sales table
        4. Never assume column names - use only what's in the schema
        5. Always return a complete, executable SQL query
        6. Do not include any explanations, just the SQL query
        7. Ensure the query starts with SELECT
        
        User Question: "{question}"
        
        Generate a PostgreSQL query that:
        1. Uses only the columns shown in the schema
        2. Is a SELECT statement only
        3. Returns exactly what the user asks for
        """

        response = model.generate_content(prompt)
        
        if not response or not response.text:
            raise RuntimeError("No response generated from AI model")
            
        sql = clean_sql_response(response.text)
        if not sql:
            raise RuntimeError("Generated SQL query is empty")
            
        return sql
            
    except Exception as e:
        logger.error(f"Error generating SQL: {e}")
        raise RuntimeError(f"Failed to generate SQL query: {e}")

def clean_sql_response(sql: str) -> str:
    """Cleans the SQL response from AI model"""
    # Remove any markdown code blocks
    sql = sql.replace('```sql', '').replace('```', '')
    
    # Remove any leading/trailing whitespace
    sql = sql.strip()
    
    # Remove any comments
    sql_lines = [line for line in sql.splitlines() if not line.strip().startswith('--')]
    sql = ' '.join(sql_lines)
    
    # Basic validation
    if not sql.lower().startswith('select'):
        raise ValueError("Generated query must start with SELECT")
        
    return sql

def summarize_data(question: str, data: list[dict], columns: list[str]) -> str:
    """Generates a concise summary of the data using Google AI."""
    if not model:
        raise RuntimeError("Google AI SDK not configured.")
    if not data:
        return "No data available to summarize."

     # Limit data size sent for summary to avoid large prompts/costs
    max_rows_for_summary = 20 # Adjust as needed
    data_subset = data[:max_rows_for_summary]

    # Format data subset for the prompt
    data_str = "\n".join([str(row) for row in data_subset])
    if len(data) > max_rows_for_summary:
        data_str += f"\n... (and {len(data) - max_rows_for_summary} more rows)"

    prompt = f"""
    The user asked the following question: "{question}"
    The query resulted in the following data (showing first {len(data_subset)} rows):
    Columns: {', '.join(columns)}
    Data:
    {data_str}

    Provide a very concise (1-2 sentences) and insightful summary of this data that directly answers the user's original question. Focus on key trends or findings. Be business-friendly. Do not just list the data.

    Summary:
    """

    logger.info("Generating summary from data...")
    try:
        response = model.generate_content(prompt)
        summary = response.text.strip()
        logger.info(f"Successfully generated summary: {summary}")
        return summary
    except Exception as e:
        logger.error(f"Error calling Google AI for summarization: {e}")
        return "Could not generate summary." # Return a default message