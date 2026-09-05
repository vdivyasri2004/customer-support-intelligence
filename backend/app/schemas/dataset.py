from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DatasetResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    source_type: str
    original_filename: Optional[str] = None
    row_count: int
    created_at: datetime
    updated_at: datetime


class DatasetListResponse(BaseModel):
    datasets: List[DatasetResponse]
    total: int


class DatasetUploadResponse(BaseModel):
    dataset: DatasetResponse
    message: str
    columns_found: List[str]
    rows_processed: int
    warnings: List[str] = []
