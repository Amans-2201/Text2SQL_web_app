# backend/services/validation_service.py
import sqlparse
import logging

logger = logging.getLogger(__name__)

# List of potentially harmful keywords/statements (expand as needed)
FORBIDDEN_KEYWORDS = {
    'DELETE', 'UPDATE', 'INSERT', 'DROP', 'TRUNCATE', 'ALTER', 'GRANT', 'REVOKE',
    'EXEC', 'EXECUTE', 'CREATE', 'MERGE', 'UPSERT'
    # Add any other keywords specific to your DB that could modify data or structure
}

def validate_sql(sql_query: str) -> str:
    """
    Validates the generated SQL query.
    - Ensures it's a SELECT statement.
    - Checks against a list of forbidden keywords.
    Returns the validated query or raises ValueError.
    """
    if not sql_query or not sql_query.strip():
        raise ValueError("SQL query cannot be empty.")

    try:
        # Normalize and remove potential comments (basic)
        cleaned_query = sqlparse.format(sql_query, strip_comments=True).strip()
        if not cleaned_query:
             raise ValueError("SQL query is empty after cleaning.")

        # Parse the SQL query
        parsed = sqlparse.parse(cleaned_query)
        if not parsed:
            raise ValueError("Invalid SQL: Could not parse the query.")

        # Expecting only one statement
        if len(parsed) > 1:
            # Allow multiple SELECTs if joined by UNION/INTERSECT etc. if needed,
            # but simpler to restrict to one main statement initially.
            logger.warning(f"Multiple SQL statements detected: {cleaned_query}")
            # For now, let's allow multiple statements but check each one
            # raise ValueError("Invalid SQL: Multiple statements are not allowed.")


        for statement in parsed:
             # Check statement type - must be SELECT
            stmt_type = statement.get_type()
            if stmt_type != 'SELECT':
                logger.error(f"SQL Validation Failed: Statement type is not SELECT. Type: {stmt_type}. Query: {cleaned_query}")
                raise ValueError(f"Invalid SQL: Only SELECT statements are allowed. Found: {stmt_type}")

            # Check for forbidden keywords within the statement tokens
            for token in statement.flatten():
                 # Check token value (uppercase) and if it's a keyword type
                if token.value.upper() in FORBIDDEN_KEYWORDS and token.is_keyword:
                     logger.error(f"SQL Validation Failed: Forbidden keyword '{token.value}' found. Query: {cleaned_query}")
                     raise ValueError(f"Invalid SQL: Forbidden keyword '{token.value}' found.")

        # If all checks pass, return the cleaned query
        logger.info(f"SQL Validation Successful: {cleaned_query}")
        return cleaned_query # Return the parsed/cleaned version

    except Exception as e:
        logger.error(f"SQL Validation Error: {e}. Original Query: {sql_query}")
        # Re-raise or raise a more specific validation error
        if isinstance(e, ValueError): # Keep original ValueError messages
            raise e
        raise ValueError(f"SQL validation failed: {e}")