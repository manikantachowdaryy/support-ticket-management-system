from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.authorization import require_roles
from app.core.database import get_db
from app.models.category import TicketCategory
from app.models.user import User
from app.schemas.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)
from app.services.category_service import (
    create_category,
    get_categories,
    get_category_by_id,
    set_category_status,
    update_category,
)


router = APIRouter(
    prefix="/api/categories",
    tags=["Categories"],
)


def get_client_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category_endpoint(
    data: CategoryCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    try:
        category = create_category(
            db,
            data,
            actor_user_id=current_user.id,
            ip_address=get_client_ip(request),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    return category


@router.get(
    "",
    response_model=list[CategoryResponse],
)
def list_categories(
    db: Session = Depends(get_db),
    _: User = Depends(
        require_roles(
            "ADMIN",
            "SUPPORT_AGENT",
            "CUSTOMER",
        )
    ),
):
    return get_categories(db)


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(
        require_roles(
            "ADMIN",
            "SUPPORT_AGENT",
            "CUSTOMER",
        )
    ),
):
    category = get_category_by_id(db, category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return category


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
)
def update_category_endpoint(
    category_id: int,
    data: CategoryUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    category = get_category_by_id(db, category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    try:
        return update_category(
            db,
            category,
            data,
            actor_user_id=current_user.id,
            ip_address=get_client_ip(request),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.patch(
    "/{category_id}/activate",
    response_model=CategoryResponse,
)
def activate_category(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    category = get_category_by_id(db, category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return set_category_status(
        db,
        category,
        True,
        actor_user_id=current_user.id,
        ip_address=get_client_ip(request),
    )


@router.patch(
    "/{category_id}/deactivate",
    response_model=CategoryResponse,
)
def deactivate_category(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    category = get_category_by_id(db, category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return set_category_status(
        db,
        category,
        False,
        actor_user_id=current_user.id,
        ip_address=get_client_ip(request),
    )