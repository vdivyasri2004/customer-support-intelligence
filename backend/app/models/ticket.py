from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Index
from app.core.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False, index=True)
    external_ticket_id = Column(String(100), nullable=True, index=True)
    customer_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    category = Column(String(100), nullable=True, index=True)
    subcategory = Column(String(100), nullable=True)
    priority = Column(String(50), nullable=True, index=True)
    status = Column(String(50), nullable=True, index=True)
    subject = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    channel = Column(String(50), nullable=True)
    agent = Column(String(100), nullable=True, index=True)
    first_response_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    response_time_minutes = Column(Float, nullable=True)
    resolution_time_minutes = Column(Float, nullable=True)
    satisfaction_score = Column(Float, nullable=True)
    sentiment = Column(String(20), nullable=True, index=True)
    sentiment_score = Column(Float, nullable=True)
    sla_met = Column(Boolean, nullable=True)
    ai_summary = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_dataset_category", "dataset_id", "category"),
        Index("idx_dataset_status", "dataset_id", "status"),
        Index("idx_dataset_priority", "dataset_id", "priority"),
    )
