# schemas.py
from pydantic import BaseModel, Field
from typing import List

class AnalysisResult(BaseModel):
    findings: str = Field(..., description="Summary of visual or textual findings")
    potential_diagnosis: str = Field(..., description="The AI's medical hypothesis")
    remedies: List[str] = Field(..., description="List of home remedies")
    diet_plan: List[str] = Field(..., description="Suggested dietary changes")
    is_emergency: bool = Field(..., description="True if immediate doctor visit is needed")

class ErrorResponse(BaseModel):
    error: str
    details: str