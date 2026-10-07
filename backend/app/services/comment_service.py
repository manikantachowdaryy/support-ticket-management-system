from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.models.ticket_comment import TicketComment
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentUpdate
from app.services.notification_service import notify_new_comment


def check_ticket_access(
    ticket: Ticket,
    current_user: User,
) -> None:

    role = current_user.role.name

    if role == "ADMIN":
        return

    if role == "CUSTOMER":

        if ticket.customer_id != current_user.id:
            raise PermissionError(
                "You do not have access to this ticket"
            )

        return

    if role == "SUPPORT_AGENT":

        if ticket.assigned_agent_id != current_user.id:
            raise PermissionError(
                "You do not have access to this ticket"
            )

        return

    raise PermissionError(
        "You do not have permission to access this ticket"
    )


def get_ticket(
    db: Session,
    ticket_id: int,
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

    return ticket


def create_comment(
    db: Session,
    ticket_id: int,
    data: CommentCreate,
    current_user: User,
) -> TicketComment:

    ticket = get_ticket(
        db,
        ticket_id,
    )

    check_ticket_access(
        ticket,
        current_user,
    )

    if ticket.status == "CLOSED":
        raise ValueError(
            "Closed tickets cannot receive comments"
        )

    new_comment = TicketComment(
        ticket_id=ticket.id,
        user_id=current_user.id,
        comment=data.comment.strip(),
    )

    db.add(new_comment)

    notify_new_comment(
        db,
        ticket,
        current_user,
    )

    db.commit()
    db.refresh(new_comment)

    return new_comment


def list_comments(
    db: Session,
    ticket_id: int,
    current_user: User,
):

    ticket = get_ticket(
        db,
        ticket_id,
    )

    check_ticket_access(
        ticket,
        current_user,
    )

    comments = db.scalars(
        select(TicketComment)
        .where(
            TicketComment.ticket_id
            == ticket_id
        )
        .order_by(
            TicketComment.created_at.asc()
        )
    ).all()

    return comments


def update_comment(
    db: Session,
    comment_id: int,
    data: CommentUpdate,
    current_user: User,
) -> TicketComment:

    comment = db.scalar(
        select(TicketComment).where(
            TicketComment.id == comment_id
        )
    )

    if not comment:
        raise ValueError(
            "Comment not found"
        )

    ticket = get_ticket(
        db,
        comment.ticket_id,
    )

    check_ticket_access(
        ticket,
        current_user,
    )

    if ticket.status == "CLOSED":
        raise ValueError(
            "Comments on closed tickets cannot be edited"
        )

    if (
        current_user.role.name != "ADMIN"
        and comment.user_id != current_user.id
    ):
        raise PermissionError(
            "You can only edit your own comments"
        )

    comment.comment = data.comment.strip()

    db.commit()
    db.refresh(comment)

    return comment


def delete_comment(
    db: Session,
    comment_id: int,
    current_user: User,
) -> None:

    comment = db.scalar(
        select(TicketComment).where(
            TicketComment.id == comment_id
        )
    )

    if not comment:
        raise ValueError(
            "Comment not found"
        )

    ticket = get_ticket(
        db,
        comment.ticket_id,
    )

    check_ticket_access(
        ticket,
        current_user,
    )

    if (
        current_user.role.name != "ADMIN"
        and comment.user_id != current_user.id
    ):
        raise PermissionError(
            "You can only delete your own comments"
        )

    db.delete(comment)
    db.commit()