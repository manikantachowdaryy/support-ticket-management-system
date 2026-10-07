import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def create_audit_log(
    db: Session,
    user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    ip_address: str | None = None,
    metadata: dict | None = None,
):
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        metadata_json=(
            json.dumps(metadata)
            if metadata
            else None
        ),
    )

    db.add(audit_log)
    db.flush()

    return audit_log


def get_audit_logs(
    db: Session,
    current_user,
):
    # Only administrators can view audit logs.
    if current_user.role.name != "ADMIN":
        raise PermissionError(
            "Only administrators can view audit logs"
        )

    return db.scalars(
        select(AuditLog)
        .order_by(
            AuditLog.created_at.desc()
        )
    ).all()