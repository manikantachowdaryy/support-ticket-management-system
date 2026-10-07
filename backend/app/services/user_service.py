from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User
from app.schemas.user import (
    ChangeRoleRequest,
    CreateUserRequest,
    UpdateUserRequest,
)
from app.services.audit_service import create_audit_log


VALID_ROLES = {
    "ADMIN",
    "SUPPORT_AGENT",
    "CUSTOMER",
}


def create_user(
    db: Session,
    data: CreateUserRequest,
    actor_user_id: int | None = None,
    ip_address: str | None = None,
) -> User:

    if data.role not in VALID_ROLES:
        raise ValueError("Invalid role")

    existing_user = db.scalar(
        select(User).where(User.email == data.email)
    )

    if existing_user:
        raise ValueError("Email already registered")

    role = db.scalar(
        select(Role).where(Role.name == data.role)
    )

    if not role:
        role = Role(name=data.role)
        db.add(role)
        db.flush()

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role_id=role.id,
        is_active=True,
    )

    db.add(user)
    db.flush()

    create_audit_log(
        db=db,
        user_id=actor_user_id,
        action="USER_CREATED",
        entity_type="USER",
        entity_id=user.id,
        ip_address=ip_address,
        metadata={
            "name": user.name,
            "email": user.email,
            "role": data.role,
        },
    )

    db.commit()
    db.refresh(user)

    return user


def get_users(db: Session) -> list[User]:
    return list(
        db.scalars(
            select(User).order_by(User.id)
        ).all()
    )


def get_user_by_id(
    db: Session,
    user_id: int,
) -> User | None:

    return db.scalar(
        select(User).where(User.id == user_id)
    )


def update_user(
    db: Session,
    user: User,
    data: UpdateUserRequest,
    actor_user_id: int | None = None,
    ip_address: str | None = None,
) -> User:

    changes = {}

    if data.name is not None:
        if data.name != user.name:
            changes["name"] = {
                "old": user.name,
                "new": data.name,
            }

        user.name = data.name

    if data.email is not None:
        existing_user = db.scalar(
            select(User).where(
                User.email == data.email,
                User.id != user.id,
            )
        )

        if existing_user:
            raise ValueError("Email already registered")

        if data.email != user.email:
            changes["email"] = {
                "old": user.email,
                "new": data.email,
            }

        user.email = data.email

    create_audit_log(
        db=db,
        user_id=actor_user_id,
        action="USER_UPDATED",
        entity_type="USER",
        entity_id=user.id,
        ip_address=ip_address,
        metadata={
            "changes": changes,
        },
    )

    db.commit()
    db.refresh(user)

    return user


def change_user_role(
    db: Session,
    user: User,
    data: ChangeRoleRequest,
    actor_user_id: int | None = None,
    ip_address: str | None = None,
) -> User:

    if data.role not in VALID_ROLES:
        raise ValueError("Invalid role")

    old_role = user.role.name

    role = db.scalar(
        select(Role).where(Role.name == data.role)
    )

    if not role:
        role = Role(name=data.role)
        db.add(role)
        db.flush()

    user.role_id = role.id

    create_audit_log(
        db=db,
        user_id=actor_user_id,
        action="USER_ROLE_CHANGED",
        entity_type="USER",
        entity_id=user.id,
        ip_address=ip_address,
        metadata={
            "old_role": old_role,
            "new_role": data.role,
        },
    )

    db.commit()
    db.refresh(user)

    return user


def set_user_status(
    db: Session,
    user: User,
    is_active: bool,
    actor_user_id: int | None = None,
    ip_address: str | None = None,
) -> User:

    old_status = user.is_active

    user.is_active = is_active

    action = (
        "USER_ACTIVATED"
        if is_active
        else "USER_DEACTIVATED"
    )

    create_audit_log(
        db=db,
        user_id=actor_user_id,
        action=action,
        entity_type="USER",
        entity_id=user.id,
        ip_address=ip_address,
        metadata={
            "old_status": old_status,
            "new_status": is_active,
        },
    )

    db.commit()
    db.refresh(user)

    return user