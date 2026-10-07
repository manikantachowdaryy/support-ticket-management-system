from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    ip_address: str | None
    metadata_json: str | None
    created_at: datetime

    class Config:
        from_attributes = True