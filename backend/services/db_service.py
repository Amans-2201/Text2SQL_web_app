# backend/services/db_service.py
from typing import Tuple, List, Dict, Any
import mysql.connector
from mysql.connector import pooling
import logging
from backend.core.config import settings

logger = logging.getLogger(__name__)

class MySQLPool:
    _instance = None
    _pool = None
    _current_db = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        # Attempt to initialize pool only if DB_TYPE is mysql or not set (legacy default)
        # Or adjust logic based on how initial setup works
        if settings.DB_TYPE == "mysql":
             try:
                 self.initialize_pool()
             except Exception as e:
                 logger.warning(f"Initial MySQL pool initialization failed (DB settings might not be ready): {e}")
        else:
             logger.info("DB_TYPE is not MySQL, skipping initial MySQL pool creation.")


    def initialize_pool(self, database_name=None):
        """Initialize or reinitialize the connection pool with a new database"""
        # Read current .env values *within this method* if relying on it
        # from backend.services.db_factory import get_current_env_config
        # current_config = get_current_env_config()
        # Or better: accept full config dictionary if called externally

        # Use passed 'database_name' or read DB_NAME from current settings/env
        # Let's assume settings object might be updated by reload_settings
        # If not reliable, pass full config dict here.
        from backend.core.config import settings # Local import might get updated settings

        target_db = database_name or settings.DB_NAME
        current_host = settings.DB_HOST
        current_port = settings.DB_PORT
        current_user = settings.DB_USER
        current_password = settings.DB_PASSWORD

        # Ensure required settings are available
        if not all([current_host, current_user, current_password, target_db]):
             # Construct a detailed error message
             missing = [k for k, v in {
                 "DB_HOST": current_host, "DB_USER": current_user,
                 "DB_PASSWORD": current_password, "DB_NAME": target_db
             }.items() if not v]
             err_msg = f"Cannot initialize MySQL pool: Missing settings: {', '.join(missing)}"
             logger.error(err_msg)
             raise ConnectionError(err_msg) # Raise specific error

        self._current_db = target_db

        # Close existing pool if it exists
        if self._pool:
            logger.info("Resetting existing MySQL pool.")
            self._pool = None

        logger.info(f"Initializing MySQL connection pool for database: {self._current_db} on {current_host}:{current_port}")
        try:
            self._pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="mypool",
                pool_size=5, # Consider making configurable
                host=current_host,
                port=current_port,
                user=current_user,
                password=current_password,
                database=self._current_db,
                # Add connection timeout?
                # connection_timeout=10
            )
            # Test connection
            conn = self._pool.get_connection()
            conn.close()
            logger.info(f"MySQL connection pool initialized successfully for {self._current_db}.")
        except mysql.connector.Error as err:
            logger.error(f"Failed to initialize MySQL connection pool for database '{self._current_db}': {err}")
            self._pool = None # Ensure pool is None if initialization failed
            raise ConnectionError(f"Failed to initialize MySQL pool: {err}") from err # Propagate


    def switch_database(self, new_database):
        """Switch to a different database by reinitializing the pool"""
        logger.info(f"Switching MySQL database pool to: {new_database}")
        # Reinitialize pool for the new database
        try:
             self.initialize_pool(new_database)
        except ConnectionError as e:
             # Handle or log the error if switching fails
             logger.error(f"Failed to switch MySQL pool to database '{new_database}': {e}")
             # Optionally raise the error again
             raise


    def get_connection(self):
         """Gets a connection from the pool, raises error if pool not initialized."""
         if not self._pool:
             # Maybe try to initialize it here?
             logger.warning("MySQL pool not initialized when getting connection. Attempting init.")
             try:
                 self.initialize_pool() # Try default init
                 if not self._pool: # Check again
                      raise ConnectionError("MySQL Pool could not be initialized on demand.")
             except Exception as e:
                  logger.error(f"On-demand initialization failed: {e}")
                  raise ConnectionError("MySQL pool is not initialized and initialization failed.") from e

         # Proceed to get connection if pool exists
         try:
             return self._pool.get_connection()
         except mysql.connector.Error as err:
             logger.error(f"Failed to get connection from MySQL pool: {err}")
             raise ConnectionError(f"Failed to get MySQL connection: {err}") from err