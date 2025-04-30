# backend/services/ai_service.py
import google.generativeai as genai
from backend.core.config import settings
from backend.services.db_service import get_db_schema
from backend.api.models.chat import VisualizationSuggestion
from typing import List, Dict, Any, Optional
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=3)

# Configure the AI model
try:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-flash') #gemini-2.0-flash
    logger.info("Google AI SDK configured successfully")
except Exception as e:
    logger.error(f"Failed to configure Google AI SDK: {e}")
    model = None

def _generate_content(prompt: str):
    """Synchronous wrapper for model.generate_content"""
    try:
        return model.generate_content(prompt)
    except Exception as e:
        logger.error(f"Error in generate_content: {e}")
        raise

async def generate_content_async(prompt: str):
    """Asynchronously generates content using thread pool"""
    try:
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(_executor, _generate_content, prompt)
        return response
    except Exception as e:
        logger.error(f"Error in generate_content_async: {e}")
        raise

async def generate_sql_from_prompt(question: str, db_type: str = None) -> str:
    """Generates SQL query from natural language"""
    if not model:
        raise RuntimeError("AI model not configured")
    
    try:
        db_type = db_type or settings.DB_TYPE
        schema = await get_db_schema()
        
        prompt = f"""
        You are a SQL query generator for {db_type.upper()}. Follow these instructions precisely:
        
        Database Schema:
        {schema}

        Rules:
        1. Use ONLY the columns exactly as they appear in the schema
        2. Tables and columns are case-sensitive - use exact names
        3. Always return a complete, executable SQL query
        4. Do not include any explanations, just the SQL query
        5. Ensure the query starts with SELECT
        
        User Question: "{question}"
        
        Generate a {db_type.upper()} query that:
        1. Uses only the columns shown in the schema
        2. Is a SELECT statement only
        3. Returns exactly what the user asks for
        """

        response = await generate_content_async(prompt)
        if not response or not response.text:
            raise RuntimeError("No response generated from AI model")
            
        sql = await clean_sql_response(response.text)
        return sql
            
    except Exception as e:
        logger.error(f"Error generating SQL: {e}")
        raise RuntimeError(f"Failed to generate SQL query: {e}")

async def clean_sql_response(sql: str) -> str:
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

async def summarize_data(question: str, data: list[dict], columns: list[str]) -> str:
    """Generates a concise summary of the data"""
    if not model:
        raise RuntimeError("AI model not configured")

    data_str = "\n".join([str(row) for row in data[:20]])
    if len(data) > 20:
        data_str += f"\n... (and {len(data) - 20} more rows)"

    prompt = f"""
    Question: "{question}"
    Data (first 20 rows):
    Columns: {', '.join(columns)}
    {data_str}

    Provide a concise (1-2 sentences) summary that answers the question.
    """

    try:
        response = await generate_content_async(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return "Could not generate summary."

async def generate_query_suggestions() -> list[str]:
    """Generates smart query suggestions"""
    try:
        schema = await get_db_schema()
        
        prompt = """Generate 5 useful business questions about the data. Return ONLY questions, one per line."""

        response = await generate_content_async(prompt)
        if not response or not response.text:
            return await get_default_suggestions()
        
        suggestions = [q.strip() for q in response.text.split('\n') if q.strip()]
        valid_suggestions = [s for s in suggestions if await is_valid_suggestion(s)][:5]
        
        return valid_suggestions if valid_suggestions else await get_default_suggestions()
        
    except Exception as e:
        logger.error(f"Error generating suggestions: {e}")
        return await get_default_suggestions()

async def get_default_suggestions() -> list[str]:
    """Returns default suggestions when AI generation fails"""
    return [
        "How many tables are in the database?",
        "Show me all table names",
        "What are our total sales?",
        "Show customer order history",
        "List all products"
    ]

async def is_valid_suggestion(suggestion: str) -> bool:
    """Validates if a suggestion is appropriate"""
    if not suggestion:
        return False
    # Check minimum length and ensure it's a question or command
    return (len(suggestion) > 10 and 
            any(word in suggestion.lower() for word in ['how', 'what', 'where', 'when', 'show', 'list', 'give', 'find']))

async def suggest_visualization(question: str, data: List[Dict[str, Any]], columns: List[str]) -> Optional[VisualizationSuggestion]:
    """Suggests appropriate visualization based on data and question"""
    if not data or not columns:
        return None

    try:
        prompt = f"""
        Analyze this data and suggest the best visualization for C-level executives.
        
        Question: {question}
        Columns: {', '.join(columns)}
        Sample Data (first 3 rows): {str(data[:3])}
        Total Rows: {len(data)}

        Choose from these chart types:
        1. Bar Chart - For comparing categories
        2. Line Chart - For trends over time
        3. Pie Chart - For part-to-whole relationships (max 7 categories)
        4. Scatter Plot - For correlation between two metrics
        5. Table - For detailed raw data

        Return a JSON object with these fields:
        {{
            "type": "chart_type",
            "title": "chart_title",
            "x_axis": "column_name",
            "y_axis": "column_name",
            "series": ["column_names"],
            "aggregation": "sum/average/count",
            "color_by": "column_name",
            "description": "why this visualization is appropriate"
        }}
        """

        response = await generate_content_async(prompt)
        if not response or not response.text:
            return None

        viz_config = json.loads(response.text)
        return VisualizationSuggestion(**viz_config)

    except Exception as e:
        logger.error(f"Error suggesting visualization: {e}")
        return None

async def suggest_visualization_with_type(
    data: List[Dict[str, Any]], 
    columns: List[str],
    preferred_type: str
) -> Optional[VisualizationSuggestion]:
    """Suggests visualization with specified chart type"""
    try:
        # Analyze data types and select appropriate columns
        numeric_cols = []
        categorical_cols = []
        temporal_cols = []
        
        if not data or not columns:
            return None

        # Analyze first row to determine column types
        sample_row = data[0]
        for col in columns:
            values = [row[col] for row in data if row[col] is not None]
            if not values:
                continue
                
            # Try to determine if it's a numeric column
            try:
                if all(isinstance(row[col], (int, float)) or 
                      (isinstance(row[col], str) and float(row[col].replace(',', '')))
                      for row in data if row[col] is not None):
                    numeric_cols.append(col)
                    continue
            except (ValueError, TypeError):
                pass
                
            # Check for temporal data
            if any(isinstance(row[col], str) and 
                  any(term in col.lower() for term in ['date', 'year', 'month', 'time'])
                  for row in data):
                temporal_cols.append(col)
            else:
                categorical_cols.append(col)

        # Select appropriate columns based on chart type
        if preferred_type in ['bar', 'line']:
            x_axis = temporal_cols[0] if temporal_cols else categorical_cols[0] if categorical_cols else None
            y_axis = numeric_cols[0] if numeric_cols else None
            
            if not x_axis or not y_axis:
                return VisualizationSuggestion(
                    type="table",
                    title="Data Table View",
                    description="Data structure not suitable for visualization"
                )
                
            # Aggregate data if needed
            aggregated_data = {}
            for row in data:
                key = str(row[x_axis])
                if key not in aggregated_data:
                    aggregated_data[key] = 0
                try:
                    value = float(str(row[y_axis]).replace(',', ''))
                    aggregated_data[key] += value
                except (ValueError, TypeError):
                    continue

            # Convert back to list format
            processed_data = [{"x": k, "y": v} for k, v in aggregated_data.items()]
            
            return VisualizationSuggestion(
                type=preferred_type,
                title=f"{y_axis} by {x_axis}",
                x_axis="x",
                y_axis="y",
                series=[],
                aggregation="sum",
                color_by="",
                description=f"Showing {preferred_type} chart of {y_axis} grouped by {x_axis}",
                processedData=processed_data
            )

        elif preferred_type == 'pie':
            if not categorical_cols or not numeric_cols:
                return VisualizationSuggestion(
                    type="table",
                    title="Data Table View",
                    description="Data not suitable for pie chart"
                )
                
            category_col = categorical_cols[0]
            value_col = numeric_cols[0]
            
            # Aggregate data for pie chart
            aggregated_data = {}
            for row in data:
                key = str(row[category_col])
                if key not in aggregated_data:
                    aggregated_data[key] = 0
                try:
                    value = float(str(row[value_col]).replace(',', ''))
                    aggregated_data[key] += value
                except (ValueError, TypeError):
                    continue

            processed_data = [{"name": k, "value": v} for k, v in aggregated_data.items()]
            
            return VisualizationSuggestion(
                type="pie",
                title=f"Distribution of {value_col} by {category_col}",
                x_axis="name",
                y_axis="value",
                series=[],
                aggregation="sum",
                color_by=category_col,
                description=f"Showing distribution of {value_col} across different {category_col}",
                processedData=processed_data
            )

        return VisualizationSuggestion(
            type="table",
            title="Data Table View",
            description="Falling back to table view"
        )

    except Exception as e:
        logger.error(f"Error suggesting visualization: {e}")
        return VisualizationSuggestion(
            type="table",
            title="Data Table View",
            description=f"Error creating visualization: {str(e)}"
        )

from typing import Optional, Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)

class VisualizationSuggestion:
    def __init__(self, type: str, title: str, x_axis: str = None, y_axis: str = None, 
                 description: str = None, processedData: List[Dict] = None):
        self.type = type
        self.title = title
        self.x_axis = x_axis
        self.y_axis = y_axis
        self.description = description
        self.processedData = processedData

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "title": self.title,
            "x_axis": self.x_axis,
            "y_axis": self.y_axis,
            "description": self.description,
            "processedData": self.processedData
        }

async def suggest_visualization(data: List[Dict[str, Any]], columns: List[str]) -> Optional[Dict[str, Any]]:
    try:
        if not data or not columns:
            return None

        # Analyze data types
        numeric_cols = []
        temporal_cols = []
        categorical_cols = []

        sample_row = data[0]
        for col in columns:
            if col not in sample_row:
                continue
            
            value = sample_row[col]
            try:
                float(str(value).replace(',', ''))
                numeric_cols.append(col)
            except (ValueError, TypeError):
                if any(term in col.lower() for term in ['date', 'time', 'month', 'year']):
                    temporal_cols.append(col)
                else:
                    categorical_cols.append(col)

        # Choose appropriate visualization
        if temporal_cols and numeric_cols:
            # Time series data - use line chart
            x_axis = temporal_cols[0]
            y_axis = numeric_cols[0]
            
            # Process data
            processed_data = []
            for row in data:
                try:
                    processed_data.append({
                        x_axis: row[x_axis],
                        y_axis: float(str(row[y_axis]).replace(',', ''))
                    })
                except (ValueError, TypeError):
                    continue

            return VisualizationSuggestion(
                type="line",
                title=f"{y_axis} over {x_axis}",
                x_axis=x_axis,
                y_axis=y_axis,
                description=f"Showing trend of {y_axis} over {x_axis}",
                processedData=processed_data
            ).to_dict()

        elif categorical_cols and numeric_cols:
            # Categorical vs numeric - use bar chart
            x_axis = categorical_cols[0]
            y_axis = numeric_cols[0]
            
            # Aggregate data by category
            aggregated_data = {}
            for row in data:
                key = str(row[x_axis])
                if key not in aggregated_data:
                    aggregated_data[key] = 0
                try:
                    aggregated_data[key] += float(str(row[y_axis]).replace(',', ''))
                except (ValueError, TypeError):
                    continue

            processed_data = [
                {x_axis: k, y_axis: v}
                for k, v in aggregated_data.items()
            ]

            return VisualizationSuggestion(
                type="bar",
                title=f"{y_axis} by {x_axis}",
                x_axis=x_axis,
                y_axis=y_axis,
                description=f"Distribution of {y_axis} across different {x_axis}",
                processedData=processed_data
            ).to_dict()

        return None

    except Exception as e:
        logger.error(f"Error suggesting visualization: {e}")
        return None