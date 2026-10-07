from datetime import datetime

from pydantic import BaseModel, Field


VALID_PRIORITIES = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
}

VALID_STATUSES = {
    "OPEN",
    "IN_PROGRESS",
    "RESOLVED",
    "CLOSED",
}


class TicketCreate(BaseModel):
    title: str = Field(
        min_length=3,
        max_length=200,
    )

    description: str = Field(
        min_length=5,
    )

    category_id: int

    priority: str = "MEDIUM"


class TicketUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        min_length=5,
    )

    category_id: int | None = None

    priority: str | None = None


class TicketAssignRequest(BaseModel):
    agent_id: int


class TicketStatusUpdate(BaseModel):
    status: str


class TicketResponse(BaseModel):
    id: int
    ticket_number: str
    title: str
    description: str
    customer_id: int
    assigned_agent_id: int | None
    category_id: int
    priority: str
    status: str
    due_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TicketListResponse(BaseModel):
    items: list[TicketResponse]
    page: int
    page_size: int
    total: int
    total_pages: int