from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

class MCPContext(BaseModel):
    user_query: str = ""
    companies: List[str] = Field(default_factory=list)
    tickers: List[str] = Field(default_factory=list)
    extracted_terms: Dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0"

class MCPRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    context: MCPContext

class MCPResponse(BaseModel):
    request_id: str
    data: Dict[str, Any] = Field(default_factory=dict)
    context_updates: Optional[Dict[str, Any]] = Field(default_factory=dict)
    status: str = "success"
    timestamp: datetime = Field(default_factory=datetime.now)