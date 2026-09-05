from pydantic import BaseModel
from typing import Optional, List, Any, Dict


class AnalyticsFilters(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    channel: Optional[str] = None
    agent: Optional[str] = None
    sentiment: Optional[str] = None


class KPIMetrics(BaseModel):
    total_tickets: int
    open_tickets: int
    resolved_tickets: int
    closed_tickets: int
    avg_response_time: Optional[float] = None
    avg_resolution_time: Optional[float] = None
    avg_satisfaction: Optional[float] = None
    sla_compliance: Optional[float] = None
    high_priority_pct: Optional[float] = None
    negative_sentiment_pct: Optional[float] = None


class TrendData(BaseModel):
    date: str
    count: int


class CategoryData(BaseModel):
    category: str
    count: int


class StatusData(BaseModel):
    status: str
    count: int


class PriorityData(BaseModel):
    priority: str
    count: int


class ChannelData(BaseModel):
    channel: str
    count: int


class AgentData(BaseModel):
    agent: str
    total: int
    resolved: int
    avg_satisfaction: Optional[float] = None
    avg_response_time: Optional[float] = None
    avg_resolution_time: Optional[float] = None


class SentimentData(BaseModel):
    sentiment: str
    count: int


class SatisfactionByCategory(BaseModel):
    category: str
    avg_satisfaction: Optional[float] = None
    count: int


class TimeAnalysis(BaseModel):
    category: str
    avg_response_time: Optional[float] = None
    avg_resolution_time: Optional[float] = None
    count: int


class AnalyticsResponse(BaseModel):
    kpis: KPIMetrics
    tickets_over_time: List[TrendData]
    tickets_by_category: List[CategoryData]
    tickets_by_status: List[StatusData]
    tickets_by_priority: List[PriorityData]
    tickets_by_channel: List[ChannelData]
    sentiment_distribution: List[SentimentData]
    satisfaction_by_category: List[SatisfactionByCategory]
    agent_performance: List[AgentData]
    time_analysis: List[TimeAnalysis]


class AnalyticsFiltersResponse(BaseModel):
    categories: List[str]
    priorities: List[str]
    statuses: List[str]
    channels: List[str]
    agents: List[str]
    sentiments: List[str]
    date_min: Optional[str] = None
    date_max: Optional[str] = None
