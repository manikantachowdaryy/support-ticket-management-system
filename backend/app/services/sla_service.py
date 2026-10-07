from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.services.notification_service import notify_sla_breached


def process_sla_breaches(db: Session) -> int:
    """
    Find all open/in-progress tickets whose SLA has expired
    and create SLA breach notifications.

    Returns the number of tickets that are currently breached.
    """

    now = datetime.utcnow()

    breached_tickets = db.scalars(
        select(Ticket).where(
            Ticket.due_date <= now,
            Ticket.status.notin_(
                {"RESOLVED", "CLOSED"}
            ),
        )
    ).all()

    for ticket in breached_tickets:
        notify_sla_breached(
            db=db,
            ticket=ticket,
        )

    db.commit()

    return len(breached_tickets)