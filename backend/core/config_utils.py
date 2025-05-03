import os
import logging
import json
from dotenv import load_dotenv, set_key

logger = logging.getLogger(__name__)

# Define an ABSOLUTE path for the .env file to ensure consistency
ENV_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env'))

# Also create a JSON config file for more reliable storage
CONFIG_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app_config.json'))

def get_config_paths():
    """Return the absolute paths to the config files for debugging"""
    return {
        "env_file": ENV_FILE_PATH,
        "config_file": CONFIG_FILE_PATH
    }

def load_config():
    """Load configuration from both .env and JSON config file"""
    # Load from .env
    logger.info(f"Loading configuration from .env: {ENV_FILE_PATH}")
    env_exists = os.path.exists(ENV_FILE_PATH)
    
    if env_exists:
        load_dotenv(ENV_FILE_PATH)
        logger.info("Loaded .env file")
    else:
        logger.warning(f".env file not found at {ENV_FILE_PATH}")
    
    # Load from JSON config (more reliable)
    config = {}
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded JSON config: {config}")
        except Exception as e:
            logger.error(f"Error loading JSON config: {e}")
    
    # If no JSON config but .env exists, convert .env to JSON
    if not config and env_exists:
        config = {
            "DB_TYPE": os.environ.get("DB_TYPE", "mysql"),
            "DB_HOST": os.environ.get("DB_HOST", "localhost"),
            "DB_PORT": os.environ.get("DB_PORT", "3306"),
            "DB_NAME": os.environ.get("DB_NAME", ""),
            "DB_USER": os.environ.get("DB_USER", ""),
            "DB_PASSWORD": os.environ.get("DB_PASSWORD", "")
        }
        # Save to JSON
        save_config_json(config)
    
    return config

def save_config(config):
    """Save configuration to both .env and JSON config file"""
    try:
        # Save to .env file
        logger.info(f"Saving configuration to .env: {ENV_FILE_PATH}")
        env_content = "\n".join([f"{key}={val}" for key, val in config.items()])
        
        with open(ENV_FILE_PATH, 'w') as f:
            f.write(env_content)
        
        # Also save to JSON (more reliable)
        save_config_json(config)
        
        # Force os.environ to update
        for key, val in config.items():
            os.environ[key] = str(val)
        
        logger.info(f"Configuration saved successfully: {config}")
        return True
    except Exception as e:
        logger.exception(f"Error saving configuration: {e}")
        return False

def save_config_json(config):
    """Save configuration to JSON file"""
    try:
        logger.info(f"Saving configuration to JSON: {CONFIG_FILE_PATH}")
        with open(CONFIG_FILE_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logger.exception(f"Error saving JSON config: {e}")
        return False

def get_current_config():
    """Get the current configuration, prioritizing the JSON config file"""
    # First check if JSON config exists
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded current config from JSON: DB_TYPE={config.get('DB_TYPE')}, DB_NAME={config.get('DB_NAME')}")
            return config
        except Exception as e:
            logger.error(f"Error reading JSON config: {e}")
    
    # Fallback to .env/environ
    config = {
        "DB_TYPE": os.environ.get("DB_TYPE", "mysql"),
        "DB_HOST": os.environ.get("DB_HOST", "localhost"),
        "DB_PORT": os.environ.get("DB_PORT", "3306"),
        "DB_NAME": os.environ.get("DB_NAME", ""),
        "DB_USER": os.environ.get("DB_USER", ""),
        "DB_PASSWORD": os.environ.get("DB_PASSWORD", "")
    }
    logger.info(f"Using config from environment: DB_TYPE={config.get('DB_TYPE')}, DB_NAME={config.get('DB_NAME')}")
    return config
