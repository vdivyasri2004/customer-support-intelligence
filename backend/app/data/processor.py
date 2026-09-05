import csv
import io
import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.dataset import Dataset
from app.models.ticket import Ticket
from app.ml.sentiment import analyze_ticket_sentiment
from app.ml.classifier import classify_ticket


COLUMN_ALIASES = {
    "ticket_id": ["ticket_id", "id", "ticket", "ticketid", "ticket_number", "number", "ticket #"],
    "customer_id": ["customer_id", "customer", "customerid", "client_id", "client", "user_id", "user"],
    "created_at": ["created_at", "created", "date", "created_date", "submitted_at", "submitted", "open_date", "opened_at", "timestamp", "date_created"],
    "updated_at": ["updated_at", "updated", "last_updated", "modified_at", "modified"],
    "category": ["category", "issue_type", "type", "issue_category", "ticket_type", "department"],
    "subcategory": ["subcategory", "sub_category", "sub-category", "issue_subtype"],
    "priority": ["priority", "urgency", "importance", "severity", "level"],
    "status": ["status", "state", "ticket_status", "current_status"],
    "subject": ["subject", "title", "ticket_subject", "summary", "topic", "headline"],
    "description": ["description", "message", "complaint", "details", "body", "content", "text", "issue_description", "ticket_description", "notes"],
    "channel": ["channel", "source", "medium", "support_channel", "origin", "contact_method"],
    "agent": ["agent", "assigned_agent", "representative", "rep", "support_agent", "handler", "assignee", "agent_name"],
    "first_response_at": ["first_response_at", "first_response", "response_date", "responded_at", "first_reply_at"],
    "resolved_at": ["resolved_at", "resolved", "resolution_date", "closed_at", "resolved_date"],
    "satisfaction_score": ["satisfaction_score", "satisfaction", "csat", "csat_score", "rating", "score", "customer_satisfaction"],
}

PRIORITY_MAP = {
    "1": "Critical", "critical": "Critical", "urg": "Critical", "urgent": "Critical",
    "2": "High", "high": "High", "h": "High",
    "3": "Medium", "medium": "Medium", "m": "Medium", "normal": "Medium", "med": "Medium",
    "4": "Low", "low": "Low", "l": "Low",
    "5": "Low", "lowest": "Low",
}

STATUS_MAP = {
    "open": "Open", "new": "Open", "pending": "Open",
    "in progress": "In Progress", "in_progress": "In Progress", "inprogress": "In Progress", "working": "In Progress",
    "resolved": "Resolved", "done": "Resolved", "completed": "Resolved", "fixed": "Resolved",
    "closed": "Closed", "archive": "Closed", "archived": "Closed", "cancelled": "Closed", "canceled": "Closed",
}


def parse_datetime(val: Optional[str]) -> Optional[datetime]:
    if not val or not val.strip():
        return None
    val = val.strip()
    formats = [
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d",
        "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%m/%d/%Y",
        "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y",
        "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M", "%Y/%m/%d",
        "%b %d, %Y %H:%M", "%b %d, %Y", "%B %d, %Y %H:%M", "%B %d, %Y",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(val, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def parse_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip()
    if not val_str:
        return None
    val_str = re.sub(r'[^\d.\-]', '', val_str)
    try:
        return float(val_str)
    except (ValueError, TypeError):
        return None


def normalize_column_name(name: str) -> Optional[str]:
    cleaned = name.strip().lower().replace(" ", "_").replace("-", "_")
    cleaned = re.sub(r'[^a-z0-9_]', '', cleaned)
    for standard_name, aliases in COLUMN_ALIASES.items():
        if cleaned in aliases:
            return standard_name
    return None


def detect_columns(headers: List[str]) -> Dict[str, str]:
    mapping = {}
    for header in headers:
        normalized = normalize_column_name(header)
        if normalized:
            mapping[header] = normalized
    return mapping


def process_csv_upload(db: Session, file_content: bytes, filename: str, user_id: int) -> Tuple[Dataset, int, List[str]]:
    text = file_content.decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise ValueError("CSV file has no headers")

    column_mapping = detect_columns(reader.fieldnames)
    required_fields = ["ticket_id", "subject", "description"]
    mapped_fields = set(column_mapping.values())
    missing = [f for f in required_fields if f not in mapped_fields]
    if len(mapped_fields) < 3:
        raise ValueError(f"Too few recognizable columns. Found: {list(mapped_fields)}. Expected at least 3 supported columns.")

    dataset = Dataset(
        user_id=user_id,
        name=filename.replace(".csv", "").replace("_", " ").replace("-", " ").title(),
        source_type="upload",
        original_filename=filename,
        row_count=0,
    )
    db.add(dataset)
    db.flush()

    tickets = []
    warnings = []
    row_num = 0
    for row in reader:
        row_num += 1
        mapped = {}
        for original_key, standard_key in column_mapping.items():
            val = row.get(original_key, "").strip() if row.get(original_key) else ""
            mapped[standard_key] = val

        if not mapped.get("subject") and not mapped.get("description"):
            if row_num <= 5:
                warnings.append(f"Row {row_num}: no subject or description found, skipping")
            continue

        first_resp = parse_datetime(mapped.get("first_response_at"))
        resolved = parse_datetime(mapped.get("resolved_at"))
        created = parse_datetime(mapped.get("created_at"))
        updated = parse_datetime(mapped.get("updated_at"))

        resp_time = None
        if first_resp and created:
            resp_time = (first_resp - created).total_seconds() / 60

        res_time = None
        if resolved and created:
            res_time = (resolved - created).total_seconds() / 60

        sat_score = parse_float(mapped.get("satisfaction_score"))
        if sat_score is not None:
            if sat_score > 5:
                sat_score = min(sat_score / 20.0, 5.0) if sat_score > 5 else sat_score
            elif sat_score < 0:
                sat_score = None

        subject = mapped.get("subject", "")
        description = mapped.get("description", "")

        sentiment_result = analyze_ticket_sentiment(subject, description)
        classification = classify_ticket(subject, description)

        category = mapped.get("category") or classification.category
        subcategory = mapped.get("subcategory") or classification.subcategory
        priority_raw = mapped.get("priority", "")
        priority = PRIORITY_MAP.get(priority_raw.lower().strip(), priority_raw.title() if priority_raw else "Medium")
        status_raw = mapped.get("status", "")
        status = STATUS_MAP.get(status_raw.lower().strip(), status_raw.title() if status_raw else "Open")

        sla_met = res_time is not None and res_time <= 480 if res_time is not None else None

        ticket = Ticket(
            dataset_id=dataset.id,
            external_ticket_id=mapped.get("ticket_id"),
            customer_id=mapped.get("customer_id"),
            created_at=created,
            updated_at=updated,
            category=category,
            subcategory=subcategory,
            priority=priority,
            status=status,
            subject=subject,
            description=description,
            channel=mapped.get("channel", "Email"),
            agent=mapped.get("agent", "Unassigned"),
            first_response_at=first_resp,
            resolved_at=resolved,
            response_time_minutes=round(resp_time, 1) if resp_time else None,
            resolution_time_minutes=round(res_time, 1) if res_time else None,
            satisfaction_score=sat_score,
            sentiment=sentiment_result.sentiment,
            sentiment_score=sentiment_result.score,
            sla_met=sla_met,
        )
        tickets.append(ticket)

    if not tickets:
        raise ValueError("No valid tickets found in the CSV file")

    db.bulk_save_objects(tickets)
    dataset.row_count = len(tickets)
    db.commit()

    return dataset, len(tickets), warnings
