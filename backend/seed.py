#!/usr/bin/env python3
"""Seed the database with a demo user and sample dataset."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine, Base
from app.core.security import hash_password
from app.models.user import User
from app.models.dataset import Dataset
from app.models.ticket import Ticket
from app.data.sample_generator import generate_sample_dataset
from app.data.processor import parse_datetime, parse_float
from app.ml.sentiment import analyze_ticket_sentiment
from app.ml.classifier import classify_ticket


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        existing = db.query(User).filter(User.email == "demo@example.com").first()
        if existing:
            print("Demo user already exists. Skipping seed.")
            return

        user = User(email="demo@example.com", password_hash=hash_password("DemoPassword123!"))
        db.add(user)
        db.flush()
        print(f"Created demo user: demo@example.com (id={user.id})")

        tickets_data = generate_sample_dataset(400)

        dataset = Dataset(
            user_id=user.id,
            name="Sample Support Tickets",
            source_type="sample",
            original_filename="sample_support_tickets.csv",
            row_count=0,
        )
        db.add(dataset)
        db.flush()

        tickets = []
        for t in tickets_data:
            created = parse_datetime(t["created_at"])
            updated = parse_datetime(t["updated_at"])
            first_resp = parse_datetime(t.get("first_response_at"))
            resolved = parse_datetime(t.get("resolved_at"))

            resp_time = (first_resp - created).total_seconds() / 60 if first_resp and created else None
            res_time = (resolved - created).total_seconds() / 60 if resolved and created else None
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
                created_at=created, updated_at=updated,
                category=t.get("category") or cls.category,
                subcategory=t.get("subcategory") or cls.subcategory or "",
                priority=t.get("priority", "Medium"),
                status=t.get("status", "Open"),
                subject=subject, description=description,
                channel=t.get("channel", "Email"),
                agent=t.get("agent", "Unassigned"),
                first_response_at=first_resp, resolved_at=resolved,
                response_time_minutes=round(resp_time, 1) if resp_time else None,
                resolution_time_minutes=round(res_time, 1) if res_time else None,
                satisfaction_score=sat,
                sentiment=sent.sentiment, sentiment_score=sent.score,
                sla_met=sla_met,
            )
            tickets.append(ticket)

        db.bulk_save_objects(tickets)
        dataset.row_count = len(tickets)
        db.commit()
        print(f"Loaded {len(tickets)} sample tickets")
        print("Seed complete!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
