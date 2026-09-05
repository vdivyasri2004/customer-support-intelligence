from pydantic import BaseModel
from typing import Optional, List


class AIInsight(BaseModel):
    title: str
    description: str
    category: str  # observation, problem, recommendation
    severity: str = "info"  # info, warning, critical


class AIInsightsResponse(BaseModel):
    insights: List[AIInsight]
    summary: str
    available: bool = True
    message: Optional[str] = None


class CommonIssue(BaseModel):
    title: str
    frequency: int
    affected_category: str
    avg_satisfaction: Optional[float] = None
    sentiment: str
    example_tickets: List[int]


class CommonIssuesResponse(BaseModel):
    issues: List[CommonIssue]
    available: bool = True
    message: Optional[str] = None


class AIQuestionRequest(BaseModel):
    question: str


class AIQuestionResponse(BaseModel):
    question: str
    answer: str
    calculated_facts: dict = {}
    ai_interpretation: Optional[str] = None
    available: bool = True
    message: Optional[str] = None


class TicketSummaryResponse(BaseModel):
    ticket_id: int
    summary: str
    available: bool = True
    message: Optional[str] = None
