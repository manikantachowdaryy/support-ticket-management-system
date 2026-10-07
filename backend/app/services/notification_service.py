from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.ticket import Ticket
from app.models.user import User


def create_notification(
    db: Session,
    user_id: int,
    notification_type: str,
    title: str,
    message: str,
    ticket_id: int | None = None,
) -> Notification:

    notification = Notification(
        user_id=user_id,
        ticket_id=ticket_id,
        notification_type=notification_type,
        title=title,
        message=message,
        is_read=False,
    )

    db.add(notification)

    return notification


def notify_ticket_created(
    db: Session,
    ticket: Ticket,
) -> None:

    admin_users = db.scalars(
        select(User)
        .join(User.role)
        .where(
            User.role.has(name="ADMIN"),
            User.is_active.is_(True),
        )
    ).all()

    for admin in admin_users:
        create_notification(
            db=db,
            user_id=admin.id,
            ticket_id=ticket.id,
            notification_type="TICKET_CREATED",
            title="New Ticket Created",
            message=(
                f"Ticket {ticket.ticket_number} "
                f"has been created."
            ),
        )


def notify_ticket_assigned(
    db: Session,
    ticket: Ticket,
    agent: User,
    reassigned: bool = False,
) -> None:

    notification_type = (
        "TICKET_REASSIGNED"
        if reassigned
        else "TICKET_ASSIGNED"
    )

    title = (
        "Ticket Reassigned"
        if reassigned
        else "Ticket Assigned"
    )

    message = (
        f"Ticket {ticket.ticket_number} "
        f"has been assigned to you."
    )

    create_notification(
        db=db,
        user_id=agent.id,
        ticket_id=ticket.id,
        notification_type=notification_type,
        title=title,
        message=message,
    )


def notify_status_changed(
    db: Session,
    ticket: Ticket,
    old_status: str,
    new_status: str,
    current_user: User,
) -> None:

    recipients = set()

    if ticket.customer_id != current_user.id:
        recipients.add(ticket.customer_id)

    if (
        ticket.assigned_agent_id
        and ticket.assigned_agent_id != current_user.id
    ):
        recipients.add(ticket.assigned_agent_id)

    for user_id in recipients:

        create_notification(
            db=db,
            user_id=user_id,
            ticket_id=ticket.id,
            notification_type="STATUS_CHANGED",
            title="Ticket Status Changed",
            message=(
                f"Ticket {ticket.ticket_number} "
                f"changed from {old_status} to {new_status}."
            ),
        )

        if new_status == "RESOLVED":

            create_notification(
                db=db,
                user_id=user_id,
                ticket_id=ticket.id,
                notification_type="TICKET_RESOLVED",
                title="Ticket Resolved",
                message=(
                    f"Ticket {ticket.ticket_number} "
                    f"has been resolved."
                ),
            )

        elif new_status == "CLOSED":

            create_notification(
                db=db,
                user_id=user_id,
                ticket_id=ticket.id,
                notification_type="TICKET_CLOSED",
                title="Ticket Closed",
                message=(
                    f"Ticket {ticket.ticket_number} "
                    f"has been closed."
                ),
            )


def notify_new_comment(
    db: Session,
    ticket: Ticket,
    commenter: User,
) -> None:

    recipients = set()

    if ticket.customer_id != commenter.id:
        recipients.add(ticket.customer_id)

    if (
        ticket.assigned_agent_id
        and ticket.assigned_agent_id != commenter.id
    ):
        recipients.add(ticket.assigned_agent_id)

    for user_id in recipients:

        create_notification(
            db=db,
            user_id=user_id,
            ticket_id=ticket.id,
            notification_type="NEW_COMMENT",
            title="New Ticket Comment",
            message=(
                f"A new comment was added to "
                f"ticket {ticket.ticket_number}."
            ),
        )


def notify_sla_breached(
    db: Session,
    ticket: Ticket,
) -> None:

    recipients = set()

    if ticket.assigned_agent_id:
        assigned_agent = db.scalar(
            select(User).where(
                User.id == ticket.assigned_agent_id,
                User.is_active.is_(True),
            )
        )

        if assigned_agent:
            recipients.add(assigned_agent.id)

    admin_users = db.scalars(
        select(User)
        .join(User.role)
        .where(
            User.role.has(name="ADMIN"),
            User.is_active.is_(True),
        )
    ).all()

    for admin in admin_users:
        recipients.add(admin.id)

    for user_id in recipients:

        existing_notification = db.scalar(
            select(Notification).where(
                and_(
                    Notification.user_id == user_id,
                    Notification.ticket_id == ticket.id,
                    Notification.notification_type == "SLA_BREACHED",
                )
            )
        )

        if existing_notification:
            continue

        create_notification(
            db=db,
            user_id=user_id,
            ticket_id=ticket.id,
            notification_type="SLA_BREACHED",
            title="SLA Breached",
            message=(
                f"Ticket {ticket.ticket_number} "
                f"has breached its SLA."
            ),
        )

def get_user_notifications(
    db: Session,
    current_user: User,
):

    return db.scalars(
        select(Notification)
        .where(
            Notification.user_id == current_user.id
        )
        .order_by(
            Notification.created_at.desc()
        )
    ).all()


def mark_notification_read(
    db: Session,
    notification_id: int,
    current_user: User,
) -> Notification:

    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )

    if not notification:
        raise ValueError(
            "Notification not found"
        )

    notification.is_read = True

    db.commit()
    db.refresh(notification)

    return notification


def mark_all_notifications_read(
    db: Session,
    current_user: User,
) -> int:

    notifications = db.scalars(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
    ).all()

    for notification in notifications:
        notification.is_read = True

    db.commit()

    return len(notifications)