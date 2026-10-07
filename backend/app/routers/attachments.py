import os

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.attachment import AttachmentResponse
from app.services.attachment_service import (
    create_attachment,
    delete_attachment,
    get_attachment,
    list_attachments,
)

router = APIRouter(
    prefix="/api/tickets",
    tags=["Ticket Attachments"],
)


@router.post(
    "/{ticket_id}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment_endpoint(
    ticket_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:
        return await create_attachment(
            db,
            ticket_id,
            file,
            current_user,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )


@router.get(
    "/{ticket_id}/attachments",
    response_model=list[AttachmentResponse],
)
def list_attachments_endpoint(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:
        return list_attachments(
            db,
            ticket_id,
            current_user,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )


@router.get(
    "/attachments/{attachment_id}/download",
)
def download_attachment_endpoint(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:
        attachment = get_attachment(
            db,
            attachment_id,
            current_user,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )

    if not os.path.exists(
        attachment.storage_path
    ):
        raise HTTPException(
            status_code=404,
            detail="Attachment file not found",
        )

    return FileResponse(
        path=attachment.storage_path,
        media_type=attachment.file_type,
        filename=attachment.original_filename,
    )


@router.delete(
    "/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_attachment_endpoint(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:
        delete_attachment(
            db,
            attachment_id,
            current_user,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )