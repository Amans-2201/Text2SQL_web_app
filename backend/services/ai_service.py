# backend/services/ai_service.py
import google.generativeai as genai
from backend.core.config import settings
from backend.services.db_factory import get_db_connection
from backend.api.models.chat import VisualizationSuggestion
from typing import List, Dict, Any, Optional
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import re
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from backend.core.config_utils import get_current_config

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

print(f"API Key: {settings.GOOGLE_API_KEY}")

def _generate_content(prompt: str):
    """Synchronous wrapper for model.generate_content"""
    try:
        return model.generate_content(prompt)
    except Exception as e:
        logger.error(f"Error in generate_content: {e}")
        raise

async def generate_content_async(prompt: str):
    """Generate content using Gemini model async wrapper"""
    try:
        # Configure the genai library (ensure the API key is set in settings)
        if not hasattr(genai, '_configured') or not genai._configured:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
            genai._configured = True
        
        # Set up the model
        generation_config = {
            "temperature": 0.2,  # Lower for more focused, analytical responses
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 1024,
        }

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config=generation_config,
            safety_settings=safety_settings
        )

        # Run asynchronously using asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: model.generate_content(prompt)
        )
        
        return response
    except Exception as e:
        logger.exception(f"Error generating content with Gemini: {e}")
        return None

async def generate_sql_from_prompt(question: str, db_type: str = None) -> str:
    """Generates SQL query from natural language"""
    if not model:
        raise RuntimeError("AI model not configured")
    
    try:
        logger.info(f"generate_sql_from_prompt: Getting DB connection. Current settings.DB_TYPE: {settings.DB_TYPE}")
        db = get_db_connection()
        logger.info("generate_sql_from_prompt: Fetching schema...")
        schema = await db.get_schema()
        logger.info("generate_sql_from_prompt: Schema fetched successfully.")
        
        current_db_type = db_type or settings.DB_TYPE
        
        prompt = f"""
        You are a SQL query generator for {current_db_type.upper()}. Follow these instructions precisely:
        
        Database Schema:
        {schema}

        Rules:
        1. Use ONLY the columns exactly as they appear in the schema
        2. Tables and columns are case-sensitive - use exact names
        3. Always return a complete, executable SQL query
        4. Do not include any explanations, just the SQL query
        5. Ensure the query starts with SELECT
        
        User Question: "{question}"
        
        Generate a {current_db_type.upper()} query that:
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
    """Generates AI-powered query suggestions based on schema analysis"""
    try:
        # Get current db config and a fresh connection
        config = get_current_config()
        db_name = config.get("DB_NAME", "")
        db_type = config.get("DB_TYPE", "").lower()
        
        logger.info(f"Generating Gemini-powered suggestions for {db_type}:{db_name}")
        
        # Get a fresh DB connection
        db = get_db_connection(use_cache=False)
        
        # Get detailed schema information
        schema = await db.get_schema()
        
        # Also get table list and sample column info for better context
        table_info = {}
        
        if db_type == "postgresql":
            query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';"
            data, _ = await db.execute_query(query)
            tables = [row['table_name'] for row in data] if data else []
            
            # Get column info for each table
            for table in tables:
                col_query = f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' AND table_name = '{table}' 
                ORDER BY ordinal_position;
                """
                cols_data, _ = await db.execute_query(col_query)
                table_info[table] = [
                    {"name": row['column_name'], "type": row['data_type']} 
                    for row in cols_data
                ]
                
                # Get row count for context
                count_query = f"SELECT COUNT(*) AS count FROM {table};"
                try:
                    count_data, _ = await db.execute_query(count_query)
                    if count_data and count_data[0].get('count'):
                        table_info[table].append({"row_count": count_data[0]['count']})
                except:
                    pass
                    
        else:  # MySQL
            query = "SELECT TABLE_NAME FROM information_schema.tables WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE';"
            data, _ = await db.execute_query(query)
            tables = [row['TABLE_NAME'] for row in data] if data else []
            
            # Get column info for each table
            for table in tables:
                col_query = f"""
                SELECT COLUMN_NAME, DATA_TYPE 
                FROM information_schema.columns 
                WHERE table_schema = DATABASE() AND table_name = '{table}' 
                ORDER BY ORDINAL_POSITION;
                """
                cols_data, _ = await db.execute_query(col_query)
                table_info[table] = [
                    {"name": row['COLUMN_NAME'], "type": row['DATA_TYPE']} 
                    for row in cols_data
                ]
                
                # Get row count for context
                count_query = f"SELECT COUNT(*) AS count FROM {table};"
                try:
                    count_data, _ = await db.execute_query(count_query)
                    if count_data and count_data[0].get('count'):
                        table_info[table].append({"row_count": count_data[0]['count']})
                except:
                    pass
        
        # Create an advanced analytics prompt for Gemini
        prompt = f"""
        You are an expert SQL data analyst tasked with helping users explore a database through natural language questions.
        
        Database Name: {db_name}
        Database Type: {db_type}
        
        This database contains the following tables with their respective columns:
        
        {json.dumps(table_info, indent=2)}
        
        Based on this schema, generate 5 insightful analytical questions that would help a data analyst understand the data better.
        These questions should:
        
        1. Explore relationships between tables where foreign keys exist
        2. Identify trends, patterns, or anomalies that might be present
        3. Analyze distributions or aggregations of data
        4. Uncover business insights specific to this domain
        5. Be answerable with SQL queries against this schema
        
        Focus on questions that would provide genuine business value and insights, not just basic counts or listings.
        Think about what a data analyst would want to know about this data to make informed decisions.
        
        Consider the table relationships and domain. For example:
        - If this appears to be a film/movie database: focus on popularity, ratings, categories, actor performances
        - If this is e-commerce: focus on sales patterns, product performance, customer behavior
        - If this is geographic: focus on regional patterns and distributions
        
        Return EXACTLY 5 natural language questions, one per line, with no numbering or extra text.
        """

        logger.info("Sending advanced suggestion prompt to Gemini")
        response = await generate_content_async(prompt)
        
        if not response or not response.text:
            logger.warning("No response from Gemini for suggestions")
            return await get_default_suggestions(list(table_info.keys()))
        
        # Process the response into individual questions
        raw_suggestions = response.text.strip().split("\n")
        
        # Clean up suggestions (remove numbers, extra whitespace, etc.)
        suggestions = []
        for suggestion in raw_suggestions:
            # Remove numbering like "1. " or "Question 1: "
            cleaned = re.sub(r'^\d+[\.\)\:]?\s*', '', suggestion.strip())
            cleaned = re.sub(r'^Question \d+[\.\)\:]?\s*', '', cleaned)
            
            if cleaned and len(cleaned) > 10:  # Ensure it's a valid question
                suggestions.append(cleaned)
        
        # Limit to 5 questions
        valid_suggestions = suggestions[:5]
        
        if len(valid_suggestions) < 3:  # If we didn't get enough good questions
            logger.warning(f"Not enough valid suggestions ({len(valid_suggestions)}), using fallbacks")
            return await get_default_suggestions(list(table_info.keys()))
            
        logger.info(f"Generated {len(valid_suggestions)} Gemini-powered suggestions")
        return valid_suggestions
        
    except Exception as e:
        logger.exception(f"Error generating Gemini suggestions: {e}")
        tables = await get_table_list() 
        return await get_default_suggestions(tables)

async def get_table_list() -> list[str]:
    """Get list of tables for fallback suggestions"""
    try:
        config = get_current_config()
        db_type = config.get("DB_TYPE", "").lower()
        db = get_db_connection(use_cache=False)
        
        if db_type == "postgresql":
            query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';"
            data, _ = await db.execute_query(query)
            return [row['table_name'] for row in data] if data else []
        else:  # mysql
            query = "SELECT TABLE_NAME FROM information_schema.tables WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE';"
            data, _ = await db.execute_query(query)
            return [row['TABLE_NAME'] for row in data] if data else []
    except:
        return []

async def get_default_suggestions(tables=None) -> list[str]:
    """Get default suggestions based on available tables"""
    if not tables:
        try:
            tables = await get_table_list()
        except Exception as e:
            logger.error(f"Failed to get table list for default suggestions: {e}")
            tables = [] # Default to empty list if fetch fails

    # Ensure tables is a list (it might be None if get_table_list fails)
    if tables is None:
        tables = []

    # If we have film-related tables (sakila)
    if any(t in ["film", "actor", "rental", "store", "inventory"] for t in tables):
        return [
            "Which films have been rented the most frequently?",
            "Who are our top 10 customers by rental count?",
            "What is the average rental duration for each film category?",
            "Which actors appear in the most films?",
            "How does rental revenue compare across different store locations?"
        ]

    # If we have e-commerce related tables
    elif any(t in ["order", "product", "customer", "sale", "website_session", "website_pageview"] for t in tables):
        return [
            "What are our best-selling products by revenue?",
            "Which customers have made the most purchases?",
            "What is the average order value by month?",
            "Which products are frequently purchased together?",
            "What is our customer retention rate?",
            "Analyze website traffic sources and conversion rates.",
            "Identify the most common user paths on the website."
        ]
    
    # Generic suggestions
    else:
        return [
            "How many records are in each table?", 
            "Show me a sample of data from each table",
            "What are the relationships between the main tables?",
            "Summarize the data distribution in the primary tables",
            "What interesting patterns exist in this dataset?"
        ]

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