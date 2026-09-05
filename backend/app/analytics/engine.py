from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, case, extract
from datetime import datetime, timezone
from app.models.ticket import Ticket
from app.models.dataset import Dataset
from app.schemas.analytics import (
    AnalyticsResponse, KPIMetrics, TrendData, CategoryData, StatusData,
    PriorityData, ChannelData, SentimentData, SatisfactionByCategory,
    AgentData, TimeAnalysis, AnalyticsFilters, AnalyticsFiltersResponse
)


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def _build_base_query(self, dataset_id: int, filters: Optional[AnalyticsFilters] = None):
        query = self.db.query(Ticket).filter(Ticket.dataset_id == dataset_id)
        if not filters:
            return query

        if filters.date_from:
            try:
                dt = datetime.fromisoformat(filters.date_from.replace('Z', '+00:00'))
                query = query.filter(Ticket.created_at >= dt)
            except (ValueError, AttributeError):
                pass
        if filters.date_to:
            try:
                dt = datetime.fromisoformat(filters.date_to.replace('Z', '+00:00'))
                query = query.filter(Ticket.created_at <= dt)
            except (ValueError, AttributeError):
                pass
        if filters.category:
            query = query.filter(Ticket.category == filters.category)
        if filters.priority:
            query = query.filter(Ticket.priority == filters.priority)
        if filters.status:
            query = query.filter(Ticket.status == filters.status)
        if filters.channel:
            query = query.filter(Ticket.channel == filters.channel)
        if filters.agent:
            query = query.filter(Ticket.agent == filters.agent)
        if filters.sentiment:
            query = query.filter(Ticket.sentiment == filters.sentiment)
        return query

    def get_kpis(self, dataset_id: int, filters: Optional[AnalyticsFilters] = None) -> KPIMetrics:
        q = self._build_base_query(dataset_id, filters)
        total = q.count()
        if total == 0:
            return KPIMetrics(
                total_tickets=0, open_tickets=0, resolved_tickets=0,
                closed_tickets=0, avg_response_time=None, avg_resolution_time=None,
                avg_satisfaction=None, sla_compliance=None,
                high_priority_pct=None, negative_sentiment_pct=None
            )

        open_tickets = self._build_base_query(dataset_id, filters).filter(Ticket.status == "Open").count()
        resolved_tickets = self._build_base_query(dataset_id, filters).filter(Ticket.status == "Resolved").count()
        closed_tickets = self._build_base_query(dataset_id, filters).filter(Ticket.status == "Closed").count()

        avg_resp = self._build_base_query(dataset_id, filters).with_entities(
            func.avg(Ticket.response_time_minutes)
        ).scalar()
        avg_res = self._build_base_query(dataset_id, filters).with_entities(
            func.avg(Ticket.resolution_time_minutes)
        ).scalar()
        avg_sat = self._build_base_query(dataset_id, filters).with_entities(
            func.avg(Ticket.satisfaction_score)
        ).scalar()

        sla_met_count = self._build_base_query(dataset_id, filters).filter(Ticket.sla_met == True).count()
        sla_pct = (sla_met_count / total * 100) if total > 0 else None

        high_prio = self._build_base_query(dataset_id, filters).filter(
            Ticket.priority.in_(["High", "Critical"])
        ).count()
        high_prio_pct = (high_prio / total * 100) if total > 0 else None

        neg_sent = self._build_base_query(dataset_id, filters).filter(
            Ticket.sentiment == "Negative"
        ).count()
        neg_pct = (neg_sent / total * 100) if total > 0 else None

        return KPIMetrics(
            total_tickets=total,
            open_tickets=open_tickets,
            resolved_tickets=resolved_tickets,
            closed_tickets=closed_tickets,
            avg_response_time=round(avg_resp, 1) if avg_resp else None,
            avg_resolution_time=round(avg_res, 1) if avg_res else None,
            avg_satisfaction=round(avg_sat, 2) if avg_sat else None,
            sla_compliance=round(sla_pct, 1) if sla_pct is not None else None,
            high_priority_pct=round(high_prio_pct, 1) if high_prio_pct is not None else None,
            negative_sentiment_pct=round(neg_pct, 1) if neg_pct is not None else None,
        )

    def get_tickets_over_time(self, dataset_id: int, filters: Optional[AnalyticsFilters] = None) -> List[TrendData]:
        q = self._build_base_query(dataset_id, filters)
        rows = q.with_entities(
            func.date(Ticket.created_at).label("day"),
            func.count(Ticket.id).label("count")
        ).group_by(func.date(Ticket.created_at)).order_by(func.date(Ticket.created_at)).all()

        return [TrendData(date=str(r.day), count=r.count) for r in rows]

    def get_tickets_by_category(self, dataset_id: int, filters: Optional[AnalyticsFilters] = None) -> List[CategoryData]:
        q = self._build_base_query(dataset_id, filters)
        rows = q.with_entities(Ticket.category, func.count(Ticket.id)).group_by(Ticket.category).order_by(func.count(Ticket.id).desc()).all()
        return [CategoryData(category=r[0] or "Unknown", count=r[1]) for r in rows]

    def get_tickets_by_status(self, dataset_id: int, filters: Optional[AnalyticsFilters] = None) -> List[StatusData]:
        q = self._build_base_query(dataset_id, filters)
        rows = q.with_entities(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all()
        return [StatusData(status=r[0] or "Unknown", count=r[1]) for r in rows]

    def get_tickets_by_priority(self, dataset_id: int, filters: Optional[AnalyticsFilters] = None) -> List[PriorityData]:
        q = self._build_base_query(dataset_id, filters)
        rows = q.with_entities(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority).all()
        return [PriorityData(priority=r[0] or "Unknown", count=r[1]) for r in rows]

    def get_tickets_by_channel(self, dataset_id: int, filters: Optional[AnalyticsFilters] = None) -> List[ChannelData]:
        q = self._build_base_query(dataset_id, filters)
        rows = q.with_entities(Ticket.channel, func.count(Ticket.id)).group_by(Ticket.channel).all()
        return [ChannelData(channel=r[0] or "Unknown", count=r[1]) for r in rows]

    def get_sentiment_distribution(self, dataset_id: int, filters: Optional[AnalyticsFilters] = None) -> List[SentimentData]:
        q = self._build_base_query(dataset_id, filters)
        rows = q.with_entities(Ticket.sentiment, func.count(Ticket.id)).group_by(Ticket.sentiment).all()
        return [SentimentData(sentiment=r[0] or "Unknown", count=r[1]) for r in rows]

    def get_satisfaction_by_category(self, dataset_id: int, filters: Optional[AnalyticsFilters] = None) -> List[SatisfactionByCategory]:
        q = self._build_base_query(dataset_id, filters)
        rows = q.with_entities(
            Ticket.category, func.avg(Ticket.satisfaction_score), func.count(Ticket.id)
        ).group_by(Ticket.category).all()
        return [SatisfactionByCategory(category=r[0] or "Unknown", avg_satisfaction=round(r[1], 2) if r[1] else None, count=r[2]) for r in rows]

    def get_agent_performance(self, dataset_id: int, filters: Optional[AnalyticsFilters] = None) -> List[AgentData]:
        q = self._build_base_query(dataset_id, filters)
        rows = q.with_entities(
            Ticket.agent,
            func.count(Ticket.id),
            func.sum(case((Ticket.status.in_(["Resolved", "Closed"]), 1), else_=0)),
            func.avg(Ticket.satisfaction_score),
            func.avg(Ticket.response_time_minutes),
            func.avg(Ticket.resolution_time_minutes),
        ).group_by(Ticket.agent).all()

        return [AgentData(
            agent=r[0] or "Unknown",
            total=r[1],
            resolved=int(r[2] or 0),
            avg_satisfaction=round(r[3], 2) if r[3] else None,
            avg_response_time=round(r[4], 1) if r[4] else None,
            avg_resolution_time=round(r[5], 1) if r[5] else None,
        ) for r in rows]

    def get_time_analysis(self, dataset_id: int, filters: Optional[AnalyticsFilters] = None) -> List[TimeAnalysis]:
        q = self._build_base_query(dataset_id, filters)
        rows = q.with_entities(
            Ticket.category,
            func.avg(Ticket.response_time_minutes),
            func.avg(Ticket.resolution_time_minutes),
            func.count(Ticket.id),
        ).group_by(Ticket.category).all()

        return [TimeAnalysis(
            category=r[0] or "Unknown",
            avg_response_time=round(r[1], 1) if r[1] else None,
            avg_resolution_time=round(r[2], 1) if r[2] else None,
            count=r[3],
        ) for r in rows]

    def get_full_analytics(self, dataset_id: int, filters: Optional[AnalyticsFilters] = None) -> AnalyticsResponse:
        return AnalyticsResponse(
            kpis=self.get_kpis(dataset_id, filters),
            tickets_over_time=self.get_tickets_over_time(dataset_id, filters),
            tickets_by_category=self.get_tickets_by_category(dataset_id, filters),
            tickets_by_status=self.get_tickets_by_status(dataset_id, filters),
            tickets_by_priority=self.get_tickets_by_priority(dataset_id, filters),
            tickets_by_channel=self.get_tickets_by_channel(dataset_id, filters),
            sentiment_distribution=self.get_sentiment_distribution(dataset_id, filters),
            satisfaction_by_category=self.get_satisfaction_by_category(dataset_id, filters),
            agent_performance=self.get_agent_performance(dataset_id, filters),
            time_analysis=self.get_time_analysis(dataset_id, filters),
        )

    def get_filter_options(self, dataset_id: int) -> AnalyticsFiltersResponse:
        base = self.db.query(Ticket).filter(Ticket.dataset_id == dataset_id)

        def distinct_col(col):
            return [r[0] for r in base.with_entities(col).distinct().all() if r[0]]

        date_range = base.with_entities(
            func.min(Ticket.created_at), func.max(Ticket.created_at)
        ).first()

        return AnalyticsFiltersResponse(
            categories=distinct_col(Ticket.category),
            priorities=distinct_col(Ticket.priority),
            statuses=distinct_col(Ticket.status),
            channels=distinct_col(Ticket.channel),
            agents=distinct_col(Ticket.agent),
            sentiments=distinct_col(Ticket.sentiment),
            date_min=str(date_range[0].date()) if date_range and date_range[0] else None,
            date_max=str(date_range[1].date()) if date_range and date_range[1] else None,
        )
