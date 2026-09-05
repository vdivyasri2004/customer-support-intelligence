from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.analytics.engine import AnalyticsService
from app.schemas.analytics import AnalyticsResponse, AnalyticsFilters, AnalyticsFiltersResponse

router = APIRouter(prefix="/api/datasets/{dataset_id}/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsResponse)
def get_analytics(
    dataset_id: int,
    date_from: str = Query(None),
    date_to: str = Query(None),
    category: str = Query(None),
    priority: str = Query(None),
    status: str = Query(None),
    channel: str = Query(None),
    agent: str = Query(None),
    sentiment: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = AnalyticsFilters(
        date_from=date_from, date_to=date_to, category=category,
        priority=priority, status=status, channel=channel,
        agent=agent, sentiment=sentiment,
    )
    service = AnalyticsService(db)
    return service.get_full_analytics(dataset_id, filters)


@router.get("/filters", response_model=AnalyticsFiltersResponse)
def get_filter_options(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AnalyticsService(db)
    return service.get_filter_options(dataset_id)
