from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.dashboard import (
    AdminDashboardResponse,
    AgentDashboardResponse,
    AgentTicketStats,
    CustomerDashboardResponse,
    TicketStats,
)


def get_ticket_stats(
    db: Session,
    ticket_query,
) -> TicketStats:

    tickets = db.scalars(ticket_query).all()

    total = len(tickets)

    open_count = sum(
        1 for ticket in tickets
        if ticket.status == "OPEN"
    )

    in_progress_count = sum(
        1 for ticket in tickets
        if ticket.status == "IN_PROGRESS"
    )

    resolved_count = sum(
        1 for ticket in tickets
        if ticket.status == "RESOLVED"
    )

    closed_count = sum(
        1 for ticket in tickets
        if ticket.status == "CLOSED"
    )

    overdue_count = sum(
        1
        for ticket in tickets
        if (
            ticket.status not in {
                "RESOLVED",
                "CLOSED",
            }
            and datetime.utcnow() > ticket.due_date
        )
    )

    critical_count = sum(
        1
        for ticket in tickets
        if ticket.priority == "CRITICAL"
    )

    return TicketStats(
        total=total,
        open=open_count,
        in_progress=in_progress_count,
        resolved=resolved_count,
        closed=closed_count,
        overdue=overdue_count,
        critical=critical_count,
    )


def get_admin_dashboard(
    db: Session,
) -> AdminDashboardResponse:

    all_tickets_query = select(Ticket)

    ticket_stats = get_ticket_stats(
        db,
        all_tickets_query,
    )

    customer_role = db.scalar(
        select(Role).where(
            Role.name == "CUSTOMER"
        )
    )

    agent_role = db.scalar(
        select(Role).where(
            Role.name == "SUPPORT_AGENT"
        )
    )

    total_customers = 0

    if customer_role:

        total_customers = db.scalar(
            select(func.count(User.id)).where(
                User.role_id == customer_role.id
            )
        ) or 0

    total_support_agents = 0
    active_support_agents = 0

    if agent_role:

        total_support_agents = db.scalar(
            select(func.count(User.id)).where(
                User.role_id == agent_role.id
            )
        ) or 0

        active_support_agents = db.scalar(
            select(func.count(User.id)).where(
                User.role_id == agent_role.id,
                User.is_active.is_(True),
            )
        ) or 0

    tickets_per_agent = []

    if agent_role:

        agents = db.scalars(
            select(User)
            .where(
                User.role_id == agent_role.id
            )
            .order_by(User.name.asc())
        ).all()

        for agent in agents:

            agent_tickets = db.scalars(
                select(Ticket).where(
                    Ticket.assigned_agent_id
                    == agent.id
                )
            ).all()

            tickets_per_agent.append(
                AgentTicketStats(
                    agent_id=agent.id,
                    agent_name=agent.name,
                    total_tickets=len(
                        agent_tickets
                    ),
                    open_tickets=sum(
                        1
                        for ticket in agent_tickets
                        if ticket.status == "OPEN"
                    ),
                    in_progress_tickets=sum(
                        1
                        for ticket in agent_tickets
                        if ticket.status
                        == "IN_PROGRESS"
                    ),
                    resolved_tickets=sum(
                        1
                        for ticket in agent_tickets
                        if ticket.status
                        == "RESOLVED"
                    ),
                    closed_tickets=sum(
                        1
                        for ticket in agent_tickets
                        if ticket.status == "CLOSED"
                    ),
                )
            )

    return AdminDashboardResponse(
        role="ADMIN",
        tickets=ticket_stats,
        total_customers=total_customers,
        total_support_agents=total_support_agents,
        active_support_agents=active_support_agents,
        tickets_per_agent=tickets_per_agent,
    )


def get_agent_dashboard(
    db: Session,
    current_user: User,
) -> AgentDashboardResponse:

    query = select(Ticket).where(
        Ticket.assigned_agent_id
        == current_user.id
    )

    ticket_stats = get_ticket_stats(
        db,
        query,
    )

    return AgentDashboardResponse(
        role="SUPPORT_AGENT",
        tickets=ticket_stats,
    )


def get_customer_dashboard(
    db: Session,
    current_user: User,
) -> CustomerDashboardResponse:

    query = select(Ticket).where(
        Ticket.customer_id
        == current_user.id
    )

    ticket_stats = get_ticket_stats(
        db,
        query,
    )

    return CustomerDashboardResponse(
        role="CUSTOMER",
        tickets=ticket_stats,
    )


def get_dashboard(
    db: Session,
    current_user: User,
):

    role = current_user.role.name

    if role == "ADMIN":

        return get_admin_dashboard(
            db
        )

    if role == "SUPPORT_AGENT":

        return get_agent_dashboard(
            db,
            current_user,
        )

    if role == "CUSTOMER":

        return get_customer_dashboard(
            db,
            current_user,
        )

    raise PermissionError(
        "Invalid user role"
    )