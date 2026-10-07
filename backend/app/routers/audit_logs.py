from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.audit_log import AuditLogResponse
from app.services.audit_service import get_audit_logs


router = APIRouter(
    prefix="/api/audit-logs",
    tags=["Audit Logs"],
)


@router.get(
    "",
    response_model=list[AuditLogResponse],
)
def get_audit_logs_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:
        return get_audit_logs(
            db,
            current_user,
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )