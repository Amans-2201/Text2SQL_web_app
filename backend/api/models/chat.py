# backend/api/models/chat.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ChatQuestion(BaseModel):
    question: str

class VisualizationSuggestion(BaseModel):
    type: Optional[str] = None # e.g., 'line', 'bar', 'table', 'number'
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    # Add other chart-specific config as needed

class ChatResponse(BaseModel):
    query: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    summary: Optional[str] = None
    visualization: Optional[VisualizationSuggestion] = None
    error: Optional[str] = None # To pass errors back to frontend