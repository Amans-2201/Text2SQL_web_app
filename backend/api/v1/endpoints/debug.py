from fastapi import APIRouter
from backend.core.config_utils import get_current_config, get_config_paths

router = APIRouter()

@router.get("/config")
async def debug_config():
    """Get current configuration for debugging"""
    config = get_current_config()
    paths = get_config_paths()
    
    # Mask password
    safe_config = {**config}
    if "DB_PASSWORD" in safe_config:
        safe_config["DB_PASSWORD"] = "********"
    
    return {
        "config": safe_config,
        "paths": paths
    }
