from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.dataset import Dataset
from app.models.ticket import Ticket
from app.ai.service import AIService
from app.schemas.ai import (
    AIInsightsResponse, CommonIssuesResponse, AIQuestionRequest,
    AIQuestionResponse, TicketSummaryResponse
)

router = APIRouter(tags=["ai"])


def verify_dataset_access(dataset_id: int, user_id: int, db: Session):
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id, Dataset.user_id == user_id
    ).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.post("/api/tickets/{ticket_id}/summarize", response_model=TicketSummaryResponse)
def summarize_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    verify_dataset_access(ticket.dataset_id, current_user.id, db)

    ai_service = AIService(db)
    result = ai_service.summarize_ticket(ticket_id)
    return TicketSummaryResponse(
        ticket_id=ticket_id,
        summary=result.get("summary", ""),
        available=result.get("available", False),
        message=result.get("message"),
    )


@router.post("/api/datasets/{dataset_id}/ai/insights", response_model=AIInsightsResponse)
def get_ai_insights(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_dataset_access(dataset_id, current_user.id, db)

    ai_service = AIService(db)
    result = ai_service.generate_insights(dataset_id)

    insights = []
    if "insights_text" in result:
        for line in result["insights_text"].split("\n"):
            line = line.strip().lstrip("0123456789.- ").strip()
            if len(line) > 15:
                insights.append({
                    "title": line[:80],
                    "description": line,
                    "category": "observation",
                    "severity": "info",
                })
    elif isinstance(result.get("insights"), list):
        insights = result["insights"]

    return AIInsightsResponse(
        insights=insights[:10],
        summary=result.get("summary", ""),
        available=result.get("available", False),
        message=result.get("message"),
    )


@router.post("/api/datasets/{dataset_id}/ai/common-issues", response_model=CommonIssuesResponse)
def get_common_issues(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_dataset_access(dataset_id, current_user.id, db)

    ai_service = AIService(db)
    result = ai_service.detect_common_issues(dataset_id)

    return CommonIssuesResponse(
        issues=result.get("issues", []),
        available=result.get("available", True),
    )


@router.post("/api/datasets/{dataset_id}/ai/ask", response_model=AIQuestionResponse)
def ask_question(
    dataset_id: int,
    payload: AIQuestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    verify_dataset_access(dataset_id, current_user.id, db)

    ai_service = AIService(db)
    result = ai_service.answer_question(dataset_id, payload.question)

    return AIQuestionResponse(
        question=payload.question,
        answer=result.get("answer", ""),
        calculated_facts=result.get("calculated_facts", {}),
        available=result.get("available", False),
        message=result.get("message"),
    )
