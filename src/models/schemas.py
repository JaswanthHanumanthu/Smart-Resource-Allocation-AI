from pydantic import BaseModel, Field
from typing import Optional, List

class NeedReport(BaseModel):
    urgency: int = Field(..., ge=1, le=10)
    category: str
    latitude: float
    longitude: float
    description: str
    status: str = "Pending"
    verified: bool = False
    detected_language: str = "English"
    report_count: int = 1
    people_affected: int = 1
    human_context_summary: Optional[str] = None
    depends_on: Optional[int] = None # New: Index of the task this depends on
    
class Volunteer(BaseModel):
    name: str
    skills: list[str]
    latitude: float
    longitude: float
    availability: bool = True
