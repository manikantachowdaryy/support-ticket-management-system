from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import TicketCategory
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.audit_service import create_audit_log


def create_category(
    db: Session,
    data: CategoryCreate,
    actor_user_id: int | None = None,
    ip_address: str | None = None,
) -> TicketCategory:

    existing_category = db.scalar(
        select(TicketCategory).where(
            TicketCategory.name == data.name
        )
    )

    if existing_category:
        raise ValueError("Category already exists")

    category = TicketCategory(
        name=data.name,
        description=data.description,
        is_active=True,
    )

    db.add(category)
    db.flush()

    create_audit_log(
        db=db,
        user_id=actor_user_id,
        action="CATEGORY_CREATED",
        entity_type="CATEGORY",
        entity_id=category.id,
        ip_address=ip_address,
        metadata={
            "name": category.name,
            "description": category.description,
        },
    )

    db.commit()
    db.refresh(category)

    return category


def get_categories(
    db: Session,
) -> list[TicketCategory]:

    return list(
        db.scalars(
            select(TicketCategory)
            .order_by(TicketCategory.id)
        ).all()
    )


def get_category_by_id(
    db: Session,
    category_id: int,
) -> TicketCategory | None:

    return db.scalar(
        select(TicketCategory).where(
            TicketCategory.id == category_id
        )
    )


def update_category(
    db: Session,
    category: TicketCategory,
    data: CategoryUpdate,
    actor_user_id: int | None = None,
    ip_address: str | None = None,
) -> TicketCategory:

    changes = {}

    if data.name is not None:
        existing_category = db.scalar(
            select(TicketCategory).where(
                TicketCategory.name == data.name,
                TicketCategory.id != category.id,
            )
        )

        if existing_category:
            raise ValueError("Category already exists")

        if data.name != category.name:
            changes["name"] = {
                "old": category.name,
                "new": data.name,
            }

        category.name = data.name

    if data.description is not None:
        if data.description != category.description:
            changes["description"] = {
                "old": category.description,
                "new": data.description,
            }

        category.description = data.description

    create_audit_log(
        db=db,
        user_id=actor_user_id,
        action="CATEGORY_UPDATED",
        entity_type="CATEGORY",
        entity_id=category.id,
        ip_address=ip_address,
        metadata={
            "changes": changes,
        },
    )

    db.commit()
    db.refresh(category)

    return category


def set_category_status(
    db: Session,
    category: TicketCategory,
    is_active: bool,
    actor_user_id: int | None = None,
    ip_address: str | None = None,
) -> TicketCategory:

    old_status = category.is_active

    category.is_active = is_active

    action = (
        "CATEGORY_ACTIVATED"
        if is_active
        else "CATEGORY_DEACTIVATED"
    )

    create_audit_log(
        db=db,
        user_id=actor_user_id,
        action=action,
        entity_type="CATEGORY",
        entity_id=category.id,
        ip_address=ip_address,
        metadata={
            "old_status": old_status,
            "new_status": is_active,
        },
    )

    db.commit()
    db.refresh(category)

    return category