from datetime import datetime, timedelta


SLA_HOURS = {
    "LOW": 72,
    "MEDIUM": 48,
    "HIGH": 24,
    "CRITICAL": 4,
}


def calculate_due_date(
    priority: str,
    created_at: datetime | None = None,
) -> datetime:

    if priority not in SLA_HOURS:
        raise ValueError("Invalid priority")

    if created_at is None:
        created_at = datetime.utcnow()

    return created_at + timedelta(
        hours=SLA_HOURS[priority]
    )


def is_overdue(
    due_date: datetime,
    status: str,
) -> bool:

    if status in {"RESOLVED", "CLOSED"}:
        return False

    return datetime.utcnow() > due_date