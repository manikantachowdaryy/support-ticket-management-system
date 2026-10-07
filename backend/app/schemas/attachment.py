from datetime import datetime

from pydantic import BaseModel


class AttachmentResponse(BaseModel):
    id: int
    ticket_id: int
    uploaded_by: int
    original_filename: str
    file_type: str
    file_size: int
    storage_path: str
    created_at: datetime

    class Config:
        from_attributes = True