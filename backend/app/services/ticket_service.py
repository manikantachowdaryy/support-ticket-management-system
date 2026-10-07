from datetime import datetime
from math import ceil

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.category import TicketCategory
from app.models.ticket import Ticket
from app.models.ticket_status_history import TicketStatusHistory
from app.models.user import User
from app.schemas.ticket import (
    TicketAssignRequest,
    TicketCreate,
    TicketStatusUpdate,
    TicketUpdate,
)
from app.services.notification_service import (
    notify_status_changed,
    notify_ticket_assigned,
    notify_ticket_created,
)
from app.utils.sla import calculate_due_date
from app.utils.status import validate_status_transition


def generate_ticket_number(db: Session) -> str:
    last_ticket = db.scalar(
        select(Ticket)
        .order_by(Ticket.id.desc())
        .limit(1)
    )

    next_id = 1 if not last_ticket else last_ticket.id + 1

    return f"TKT-{next_id:06d}"


def create_ticket(
    db: Session,
    data: TicketCreate,
    customer: User,
) -> Ticket:

    category = db.scalar(
        select(TicketCategory).where(
            TicketCategory.id == data.category_id,
            TicketCategory.is_active.is_(True),
        )
    )

    if not category:
        raise ValueError(
            "Category not found or inactive"
        )

    priority = data.priority.upper()

    if priority not in {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }:
        raise ValueError(
            "Invalid priority"
        )

    created_at = datetime.utcnow()

    ticket = Ticket(
        ticket_number=generate_ticket_number(db),
        title=data.title,
        description=data.description,
        customer_id=customer.id,
        category_id=data.category_id,
        priority=priority,
        status="OPEN",
        due_date=calculate_due_date(
            priority,
            created_at,
        ),
        created_at=created_at,
        updated_at=created_at,
    )

    db.add(ticket)
    db.flush()

    notify_ticket_created(
        db,
        ticket,
    )

    db.commit()
    db.refresh(ticket)

    return ticket


def get_ticket(
    db: Session,
    ticket_id: int,
    current_user: User,
) -> Ticket:

    ticket = db.scalar(
        select(Ticket).where(
            Ticket.id == ticket_id
        )
    )

    if not ticket:
        raise ValueError(
            "Ticket not found"
        )

    role = current_user.role.name

    if role == "ADMIN":
        return ticket

    if role == "CUSTOMER":

        if ticket.customer_id != current_user.id:
            raise PermissionError(
                "You do not have access to this ticket"
            )

    elif role == "SUPPORT_AGENT":

        if ticket.assigned_agent_id != current_user.id:
            raise PermissionError(
                "You do not have access to this ticket"
            )

    else:
        raise PermissionError(
            "You do not have permission to access this ticket"
        )

    return ticket


def update_ticket(
    db: Session,
    ticket_id: int,
    data: TicketUpdate,
    current_user: User,
) -> Ticket:

    ticket = get_ticket(
        db,
        ticket_id,
        current_user,
    )

    if data.title is not None:
        ticket.title = data.title

    if data.description is not None:
        ticket.description = data.description

    if data.category_id is not None:

        category = db.scalar(
            select(TicketCategory).where(
                TicketCategory.id == data.category_id,
                TicketCategory.is_active.is_(True),
            )
        )

        if not category:
            raise ValueError(
                "Category not found or inactive"
            )

        ticket.category_id = data.category_id

    if data.priority is not None:

        priority = data.priority.upper()

        if priority not in {
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        }:
            raise ValueError(
                "Invalid priority"
            )

        ticket.priority = priority

        ticket.due_date = calculate_due_date(
            priority,
            ticket.created_at,
        )

    db.commit()
    db.refresh(ticket)

    return ticket


def list_tickets(
    db: Session,
    current_user: User,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    category_id: int | None = None,
    assigned_agent_id: int | None = None,
    customer_id: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):

    query = select(Ticket)

    role = current_user.role.name

    if role == "CUSTOMER":

        query = query.where(
            Ticket.customer_id == current_user.id
        )

    elif role == "SUPPORT_AGENT":

        query = query.where(
            Ticket.assigned_agent_id == current_user.id
        )

    elif role != "ADMIN":

        raise PermissionError(
            "You do not have permission to list tickets"
        )

    if search:

        search_pattern = f"%{search}%"

        query = query.where(
            or_(
                Ticket.ticket_number.ilike(
                    search_pattern
                ),
                Ticket.title.ilike(
                    search_pattern
                ),
                Ticket.description.ilike(
                    search_pattern
                ),
            )
        )

    if status:
        query = query.where(
            Ticket.status == status.upper()
        )

    if priority:
        query = query.where(
            Ticket.priority == priority.upper()
        )

    if category_id:
        query = query.where(
            Ticket.category_id == category_id
        )

    if assigned_agent_id:
        query = query.where(
            Ticket.assigned_agent_id
            == assigned_agent_id
        )

    if customer_id:
        query = query.where(
            Ticket.customer_id == customer_id
        )

    if start_date:
        query = query.where(
            Ticket.created_at >= start_date
        )

    if end_date:
        query = query.where(
            Ticket.created_at <= end_date
        )

    allowed_sort_fields = {
        "created_at": Ticket.created_at,
        "updated_at": Ticket.updated_at,
        "priority": Ticket.priority,
        "status": Ticket.status,
        "title": Ticket.title,
        "due_date": Ticket.due_date,
    }

    sort_column = allowed_sort_fields.get(
        sort_by,
        Ticket.created_at,
    )

    if sort_order.lower() == "asc":
        query = query.order_by(
            sort_column.asc()
        )
    else:
        query = query.order_by(
            sort_column.desc()
        )

    total = db.scalar(
        select(func.count()).select_from(
            query.subquery()
        )
    )

    offset = (page - 1) * page_size

    tickets = db.scalars(
        query
        .offset(offset)
        .limit(page_size)
    ).all()

    total_pages = (
        ceil(total / page_size)
        if total
        else 0
    )

    return {
        "items": tickets,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
    }


def assign_ticket(
    db: Session,
    ticket_id: int,
    data: TicketAssignRequest,
    current_user: User,
) -> Ticket:

    if current_user.role.name not in {
        "ADMIN",
        "SUPPORT_AGENT",
    }:
        raise PermissionError(
            "You do not have permission to assign tickets"
        )

    ticket = db.scalar(
        select(Ticket).where(
            Ticket.id == ticket_id
        )
    )

    if not ticket:
        raise ValueError(
            "Ticket not found"
        )

    if ticket.status == "CLOSED":
        raise ValueError(
            "Closed tickets cannot be reassigned"
        )

    agent = db.scalar(
        select(User)
        .join(User.role)
        .where(
            User.id == data.agent_id,
            User.is_active.is_(True),
        )
    )

    if not agent:
        raise ValueError(
            "Agent not found or inactive"
        )

    if agent.role.name != "SUPPORT_AGENT":
        raise ValueError(
            "Selected user is not a support agent"
        )

    is_reassignment = (
        ticket.assigned_agent_id is not None
        and ticket.assigned_agent_id != agent.id
    )

    ticket.assigned_agent_id = agent.id

    notify_ticket_assigned(
        db,
        ticket,
        agent,
        reassigned=is_reassignment,
    )

    db.commit()
    db.refresh(ticket)

    return ticket


def update_ticket_status(
    db: Session,
    ticket_id: int,
    data: TicketStatusUpdate,
    current_user: User,
) -> Ticket:

    if current_user.role.name not in {
        "ADMIN",
        "SUPPORT_AGENT",
    }:
        raise PermissionError(
            "Only admins and support agents can change ticket status"
        )

    ticket = db.scalar(
        select(Ticket).where(
            Ticket.id == ticket_id
        )
    )

    if not ticket:
        raise ValueError(
            "Ticket not found"
        )

    if (
        current_user.role.name == "SUPPORT_AGENT"
        and ticket.assigned_agent_id
        != current_user.id
    ):
        raise PermissionError(
            "You can only change status of tickets assigned to you"
        )

    new_status = data.status.upper()

    try:
        validate_status_transition(
            ticket.status,
            new_status,
        )
    except ValueError as exc:
        raise ValueError(
            str(exc)
        )

    old_status = ticket.status

    ticket.status = new_status

    history = TicketStatusHistory(
        ticket_id=ticket.id,
        old_status=old_status,
        new_status=new_status,
        changed_by=current_user.id,
    )

    db.add(history)

    notify_status_changed(
        db,
        ticket,
        old_status,
        new_status,
        current_user,
    )

    db.commit()
    db.refresh(ticket)

    return ticket


def get_ticket_status_history(
    db: Session,
    ticket_id: int,
    current_user: User,
):

    ticket = get_ticket(
        db,
        ticket_id,
        current_user,
    )

    history = db.scalars(
        select(TicketStatusHistory)
        .where(
            TicketStatusHistory.ticket_id
            == ticket.id
        )
        .order_by(
            TicketStatusHistory.created_at.asc()
        )
    ).all()

    return history