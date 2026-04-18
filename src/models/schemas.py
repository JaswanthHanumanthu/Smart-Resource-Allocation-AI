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

class StrategicAllocation(BaseModel):
    need_id: int
    volunteer_name: str
    reasoning: str
    impact_projection: str

class TacticalInsight(BaseModel):
    strategic_summary: str = Field(..., description="High-level overview of the current resource landscape.")
    allocations: List[StrategicAllocation]
    chart_labels: List[str] = Field(..., description="Categories for Plotly charts (e.g., sectors).")
    chart_values: List[float] = Field(..., description="Numerical values corresponding to chart_labels.")
    social_roi_score: int = Field(..., ge=0, le=100)
    reasoning_log: str = Field(..., description="Detailed AI logic for the suggested distribution.")
