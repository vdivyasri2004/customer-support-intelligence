from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TicketResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    dataset_id: int
    external_ticket_id: Optional[str] = None
    customer_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    subject: Optional[str] = None
    description: Optional[str] = None
    channel: Optional[str] = None
    agent: Optional[str] = None
    first_response_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    response_time_minutes: Optional[float] = None
    resolution_time_minutes: Optional[float] = None
    satisfaction_score: Optional[float] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    sla_met: Optional[bool] = None
    ai_summary: Optional[str] = None


class TicketListResponse(BaseModel):
    tickets: List[TicketResponse]
    total: int
    page: int
    page_size: int


class TicketDetailResponse(TicketResponse):
    pass
