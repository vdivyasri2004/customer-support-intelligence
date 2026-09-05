import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import get_settings
from app.models.user import User
from app.models.dataset import Dataset
from app.models.ticket import Ticket
from app.schemas.dataset import DatasetResponse, DatasetListResponse, DatasetUploadResponse
from app.data.processor import process_csv_upload
from app.data.sample_generator import generate_sample_dataset

router = APIRouter(prefix="/api/datasets", tags=["datasets"])
settings = get_settings()


@router.get("", response_model=DatasetListResponse)
def list_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    datasets = db.query(Dataset).filter(Dataset.user_id == current_user.id).order_by(Dataset.created_at.desc()).all()
    return DatasetListResponse(
        datasets=[DatasetResponse.model_validate(d) for d in datasets],
        total=len(datasets),
    )


@router.post("/upload", response_model=DatasetUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV files are accepted")

    content = await file.read()
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")

    try:
        dataset, row_count, warnings = process_csv_upload(db, content, file.filename, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return DatasetUploadResponse(
        dataset=DatasetResponse.model_validate(dataset),
        message=f"Successfully processed {row_count} tickets",
        columns_found=[],
        rows_processed=row_count,
        warnings=warnings,
    )


@router.post("/sample", response_model=DatasetUploadResponse, status_code=status.HTTP_201_CREATED)
def load_sample_dataset(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Dataset).filter(
        Dataset.user_id == current_user.id,
        Dataset.source_type == "sample",
    ).first()
    if existing:
        return DatasetUploadResponse(
            dataset=DatasetResponse.model_validate(existing),
            message="Sample dataset already loaded",
            columns_found=[],
            rows_processed=existing.row_count,
            warnings=[],
        )

    tickets_data = generate_sample_dataset(400)

    dataset = Dataset(
        user_id=current_user.id,
        name="Sample Support Tickets",
        source_type="sample",
        original_filename="sample_support_tickets.csv",
        row_count=0,
    )
    db.add(dataset)
    db.flush()

    from datetime import datetime, timezone
    from app.data.processor import parse_datetime, parse_float
    from app.ml.sentiment import analyze_ticket_sentiment
    from app.ml.classifier import classify_ticket

    tickets = []
    for t in tickets_data:
        created = parse_datetime(t["created_at"])
        updated = parse_datetime(t["updated_at"])
        first_resp = parse_datetime(t.get("first_response_at"))
        resolved = parse_datetime(t.get("resolved_at"))

        resp_time = None
        if first_resp and created:
            resp_time = (first_resp - created).total_seconds() / 60

        res_time = None
        if resolved and created:
            res_time = (resolved - created).total_seconds() / 60

        sat = parse_float(t.get("satisfaction_score"))
        subject = t.get("subject", "")
        description = t.get("description", "")

        sent = analyze_ticket_sentiment(subject, description)
        cls = classify_ticket(subject, description)

        sla_met = res_time is not None and res_time <= 480

        ticket = Ticket(
            dataset_id=dataset.id,
            external_ticket_id=t.get("ticket_id"),
            customer_id=t.get("customer_id"),
            created_at=created,
            updated_at=updated,
            category=t.get("category") or cls.category,
            subcategory=t.get("subcategory") or cls.subcategory or "",
            priority=t.get("priority", "Medium"),
            status=t.get("status", "Open"),
            subject=subject,
            description=description,
            channel=t.get("channel", "Email"),
            agent=t.get("agent", "Unassigned"),
            first_response_at=first_resp,
            resolved_at=resolved,
            response_time_minutes=round(resp_time, 1) if resp_time else None,
            resolution_time_minutes=round(res_time, 1) if res_time else None,
            satisfaction_score=sat,
            sentiment=sent.sentiment,
            sentiment_score=sent.score,
            sla_met=sla_met,
        )
        tickets.append(ticket)

    db.bulk_save_objects(tickets)
    dataset.row_count = len(tickets)
    db.commit()
    db.refresh(dataset)

    return DatasetUploadResponse(
        dataset=DatasetResponse.model_validate(dataset),
        message=f"Loaded {len(tickets)} sample tickets",
        columns_found=[],
        rows_processed=len(tickets),
        warnings=[],
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id,
    ).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return DatasetResponse.model_validate(dataset)


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id,
    ).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    db.query(Ticket).filter(Ticket.dataset_id == dataset_id).delete()
    db.delete(dataset)
    db.commit()
