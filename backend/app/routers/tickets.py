from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.authorization import require_roles
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.status_history import TicketStatusHistoryResponse
from app.schemas.ticket import (
    TicketAssignRequest,
    TicketCreate,
    TicketListResponse,
    TicketResponse,
    TicketStatusUpdate,
    TicketUpdate,
)
from app.services.sla_service import process_sla_breaches
from app.services.ticket_service import (
    assign_ticket,
    create_ticket,
    get_ticket,
    get_ticket_status_history,
    list_tickets,
    update_ticket,
    update_ticket_status,
)


router = APIRouter(
    prefix="/api/tickets",
    tags=["Tickets"],
)


# ============================================================
# CREATE TICKET
# ============================================================

@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_endpoint(
    data: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role.name != "CUSTOMER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only customers can create tickets",
        )

    try:
        return create_ticket(
            db,
            data,
            current_user,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ============================================================
# SLA BREACH CHECK
# ============================================================

@router.post(
    "/sla/check",
)
def check_sla_breaches(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("ADMIN")),
):
    try:
        breached_count = process_sla_breaches(db)

        return {
            "success": True,
            "message": "SLA breach check completed",
            "breached_tickets": breached_count,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ============================================================
# LIST TICKETS
# ============================================================

@router.get(
    "",
    response_model=TicketListResponse,
)
def list_tickets_endpoint(
    page: int = Query(
        1,
        ge=1,
    ),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
    ),
    search: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    category_id: int | None = None,
    assigned_agent_id: int | None = None,
    customer_id: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return list_tickets(
            db=db,
            current_user=current_user,
            page=page,
            page_size=page_size,
            search=search,
            status=status,
            priority=priority,
            category_id=category_id,
            assigned_agent_id=assigned_agent_id,
            customer_id=customer_id,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ============================================================
# GET SINGLE TICKET
# ============================================================

@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
)
def get_ticket_endpoint(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return get_ticket(
            db,
            ticket_id,
            current_user,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )


# ============================================================
# UPDATE TICKET
# ============================================================

@router.put(
    "/{ticket_id}",
    response_model=TicketResponse,
)
def update_ticket_endpoint(
    ticket_id: int,
    data: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return update_ticket(
            db,
            ticket_id,
            data,
            current_user,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )


# ============================================================
# ASSIGN / REASSIGN TICKET
# ============================================================

@router.patch(
    "/{ticket_id}/assign",
    response_model=TicketResponse,
)
def assign_ticket_endpoint(
    ticket_id: int,
    data: TicketAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return assign_ticket(
            db,
            ticket_id,
            data,
            current_user,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )


# ============================================================
# UPDATE TICKET STATUS
# ============================================================

@router.patch(
    "/{ticket_id}/status",
    response_model=TicketResponse,
)
def update_ticket_status_endpoint(
    ticket_id: int,
    data: TicketStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return update_ticket_status(
            db,
            ticket_id,
            data,
            current_user,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )


# ============================================================
# TICKET STATUS HISTORY
# ============================================================

@router.get(
    "/{ticket_id}/status-history",
    response_model=list[TicketStatusHistoryResponse],
)
def get_ticket_status_history_endpoint(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return get_ticket_status_history(
            db,
            ticket_id,
            current_user,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )