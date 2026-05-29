from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal


class QueryRequest(BaseModel):
    
    query: str = Field(..., min_length=1, max_length=500)
    model: Literal["gemini", "gpt"] = Field(default = "gemini")
    max_results: int = Field(default = 1000, ge = 1, le = 10000)
    
    
class ChartData(BaseModel):
    
    type: str = "line"
    x: List = []
    y: List = []
    ids: Optional[List[str]] = None # Added to map points to float_ids
    x_label: Optional[str] = None
    y_label: Optional[str] = None 
    title: Optional[str] = None 
    
class MapPoint(BaseModel):
    
    float_id: str
    latitude: float
    longitude: float 
    value: Optional[float] = None
    

class QueryResponse(BaseModel):
    
    answer: str
    chart_type: Optional[str] = None
    chart: Optional[ChartData] = None 
    map:   Optional[List[MapPoint]] = None 
    table:  Optional[List[Dict]] = None 
    source_info:  Dict = {}
    execution_time_ms: float = 0
    model_used: str = "gemini"
    
    
class FloatLocation(BaseModel):
    
    float_id: str 
    latitude: float
    longitude: float 
    last_date: Optional[str] = None 
        