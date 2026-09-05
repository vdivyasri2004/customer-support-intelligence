from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.dataset import Dataset
from app.models.ticket import Ticket
from app.schemas.ticket import TicketResponse, TicketListResponse, TicketDetailResponse
from app.schemas.analytics import AnalyticsFilters

router = APIRouter(tags=["tickets"])


def verify_dataset_access(dataset_id: int, user_id: int, db: Session) -> Dataset:
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == user_id,
    ).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset


@router.get("/api/datasets/{dataset_id}/tickets", response_model=TicketListResponse)
def list_tickets(
    dataset_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    channel: Optional[str] = None,
    agent: Optional[str] = None,
    sentiment: Optional[str] = None,
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_dataset_access(dataset_id, current_user.id, db)

    query = db.query(Ticket).filter(Ticket.dataset_id == dataset_id)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Ticket.subject.ilike(search_term)) |
            (Ticket.description.ilike(search_term)) |
            (Ticket.external_ticket_id.ilike(search_term))
        )
    if category:
        query = query.filter(Ticket.category == category)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if status_filter:
        query = query.filter(Ticket.status == status_filter)
    if channel:
        query = query.filter(Ticket.channel == channel)
    if agent:
        query = query.filter(Ticket.agent == agent)
    if sentiment:
        query = query.filter(Ticket.sentiment == sentiment)

    total = query.count()

    sort_col = getattr(Ticket, sort_by, Ticket.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    offset = (page - 1) * page_size
    tickets = query.offset(offset).limit(page_size).all()

    return TicketListResponse(
        tickets=[TicketResponse.model_validate(t) for t in tickets],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/api/tickets/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    verify_dataset_access(ticket.dataset_id, current_user.id, db)
    return TicketDetailResponse.model_validate(ticket)
