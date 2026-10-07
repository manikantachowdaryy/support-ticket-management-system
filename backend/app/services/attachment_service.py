import os
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.models.ticket_attachment import TicketAttachment
from app.models.user import User


UPLOAD_DIR = Path("uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "text/plain",
}


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
        raise ValueError("Ticket not found")

    return ticket


def validate_file_content(
    content_type: str,
    file_bytes: bytes,
) -> None:

    if content_type not in ALLOWED_MIME_TYPES:
        raise ValueError(
            "Unsupported file type. Allowed types: PDF, PNG, JPG/JPEG, TXT"
        )

    if content_type == "application/pdf":
        if not file_bytes.startswith(b"%PDF"):
            raise ValueError(
                "Invalid PDF file"
            )

    elif content_type == "image/png":
        png_signature = b"\x89PNG\r\n\x1a\n"

        if not file_bytes.startswith(png_signature):
            raise ValueError(
                "Invalid PNG file"
            )

    elif content_type == "image/jpeg":
        if not file_bytes.startswith(b"\xff\xd8\xff"):
            raise ValueError(
                "Invalid JPEG file"
            )


async def save_uploaded_file(
    file: UploadFile,
) -> tuple[str, int]:

    if not file.filename:
        raise ValueError(
            "Filename is required"
        )

    if not file.content_type:
        raise ValueError(
            "File MIME type is required"
        )

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise ValueError(
            "Unsupported file type. Allowed types: PDF, PNG, JPG/JPEG, TXT"
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise ValueError(
            "Uploaded file is empty"
        )

    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError(
            "File size cannot exceed 10 MB"
        )

    validate_file_content(
        file.content_type,
        file_bytes,
    )

    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_filename = (
        Path(file.filename).name
    )

    unique_filename = (
        f"{uuid.uuid4().hex}_{safe_filename}"
    )

    storage_path = (
        UPLOAD_DIR / unique_filename
    )

    with open(storage_path, "wb") as output_file:
        output_file.write(file_bytes)

    return str(storage_path), len(file_bytes)


async def create_attachment(
    db: Session,
    ticket_id: int,
    file: UploadFile,
    current_user: User,
) -> TicketAttachment:

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
            "Closed tickets cannot receive attachments"
        )

    storage_path, file_size = await save_uploaded_file(
        file
    )

    attachment = TicketAttachment(
        ticket_id=ticket.id,
        uploaded_by=current_user.id,
        original_filename=Path(
            file.filename
        ).name,
        file_type=file.content_type,
        file_size=file_size,
        storage_path=storage_path,
    )

    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return attachment


def list_attachments(
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

    return db.scalars(
        select(TicketAttachment)
        .where(
            TicketAttachment.ticket_id == ticket_id
        )
        .order_by(
            TicketAttachment.created_at.asc()
        )
    ).all()


def get_attachment(
    db: Session,
    attachment_id: int,
    current_user: User,
) -> TicketAttachment:

    attachment = db.scalar(
        select(TicketAttachment).where(
            TicketAttachment.id == attachment_id
        )
    )

    if not attachment:
        raise ValueError(
            "Attachment not found"
        )

    ticket = get_ticket(
        db,
        attachment.ticket_id,
    )

    check_ticket_access(
        ticket,
        current_user,
    )

    return attachment


def delete_attachment(
    db: Session,
    attachment_id: int,
    current_user: User,
) -> None:

    attachment = get_attachment(
        db,
        attachment_id,
        current_user,
    )

    if (
        current_user.role.name != "ADMIN"
        and attachment.uploaded_by != current_user.id
    ):
        raise PermissionError(
            "You can only delete your own attachments"
        )

    if os.path.exists(
        attachment.storage_path
    ):
        os.remove(
            attachment.storage_path
        )

    db.delete(attachment)
    db.commit()