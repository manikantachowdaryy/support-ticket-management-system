from datetime import datetime

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    comment: str = Field(
        min_length=1,
        max_length=5000,
    )


class CommentUpdate(BaseModel):
    comment: str = Field(
        min_length=1,
        max_length=5000,
    )


class CommentResponse(BaseModel):
    id: int
    ticket_id: int
    user_id: int
    comment: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True