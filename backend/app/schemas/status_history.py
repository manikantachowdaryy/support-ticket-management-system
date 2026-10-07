from datetime import datetime

from pydantic import BaseModel


class TicketStatusHistoryResponse(BaseModel):
    id: int
    ticket_id: int
    old_status: str
    new_status: str
    changed_by: int
    created_at: datetime

    class Config:
        from_attributes = True