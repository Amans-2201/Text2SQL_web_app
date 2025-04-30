# backend/api/models/chat.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ChatQuestion(BaseModel):
    question: str

class VisualizationSuggestion(BaseModel):
    type: str  # 'bar', 'line', 'pie', 'scatter', 'table'
    title: str
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    series: Optional[List[str]] = None
    aggregation: Optional[str] = None  # 'sum', 'average', 'count'
    color_by: Optional[str] = None
    description: Optional[str] = None
    processedData: Optional[List[Dict[str, Any]]] = None

class ChatResponse(BaseModel):
    query: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    summary: Optional[str] = None
    visualization: Optional[VisualizationSuggestion] = None
    error: Optional[str] = None  # To pass errors back to frontend

class QuerySuggestions(BaseModel):
    suggestions: List[str]