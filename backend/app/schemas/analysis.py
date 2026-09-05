from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime


class AnalysisCreate(BaseModel):
    dataset_id: int
    analysis_name: str


class AnalysisResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    dataset_id: int
    analysis_name: str
    summary_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class AnalysisListResponse(BaseModel):
    analyses: List[AnalysisResponse]
    total: int
