from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
)
from app.services.audit_service import (
    create_audit_log,
)


def register_user(
    db: Session,
    data: RegisterRequest,
):
    existing_user = db.scalar(
        select(User).where(
            User.email == data.email
        )
    )

    if existing_user:
        raise ValueError(
            "Email already registered"
        )

    customer_role = db.scalar(
        select(Role).where(
            Role.name == "CUSTOMER"
        )
    )

    if not customer_role:
        customer_role = Role(
            name="CUSTOMER"
        )

        db.add(customer_role)
        db.flush()

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(
            data.password
        ),
        role_id=customer_role.id,
        is_active=True,
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    return user


def login_user(
    db: Session,
    data: LoginRequest,
    ip_address: str | None = None,
):
    user = db.scalar(
        select(User).where(
            User.email == data.email
        )
    )

    # Failed login - user not found
    if not user:
        create_audit_log(
            db=db,
            user_id=None,
            action="FAILED_LOGIN",
            entity_type="AUTHENTICATION",
            ip_address=ip_address,
            metadata={
                "email": data.email,
                "reason": "USER_NOT_FOUND",
            },
        )

        db.commit()

        raise ValueError(
            "Invalid email or password"
        )

    # Failed login - inactive account
    if not user.is_active:
        create_audit_log(
            db=db,
            user_id=user.id,
            action="FAILED_LOGIN",
            entity_type="AUTHENTICATION",
            entity_id=user.id,
            ip_address=ip_address,
            metadata={
                "email": data.email,
                "reason": "ACCOUNT_INACTIVE",
            },
        )

        db.commit()

        raise ValueError(
            "User account is inactive"
        )

    # Failed login - wrong password
    if not verify_password(
        data.password,
        user.password_hash,
    ):
        create_audit_log(
            db=db,
            user_id=user.id,
            action="FAILED_LOGIN",
            entity_type="AUTHENTICATION",
            entity_id=user.id,
            ip_address=ip_address,
            metadata={
                "email": data.email,
                "reason": "INVALID_PASSWORD",
            },
        )

        db.commit()

        raise ValueError(
            "Invalid email or password"
        )

    access_token = create_access_token(
        user.id,
        user.role.name,
    )

    refresh_token, expires_at = (
        create_refresh_token(user.id)
    )

    refresh_token_record = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=expires_at.replace(
            tzinfo=None
        ),
        is_revoked=False,
    )

    db.add(refresh_token_record)

    # Successful login audit
    create_audit_log(
        db=db,
        user_id=user.id,
        action="LOGIN",
        entity_type="AUTHENTICATION",
        entity_id=user.id,
        ip_address=ip_address,
        metadata={
            "email": user.email,
            "role": user.role.name,
        },
    )

    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def refresh_access_token(
    db: Session,
    refresh_token: str,
):
    try:
        payload = decode_token(
            refresh_token
        )

    except Exception:
        raise ValueError(
            "Invalid or expired refresh token"
        )

    if payload.get("type") != "refresh":
        raise ValueError(
            "Invalid refresh token"
        )

    user_id = payload.get("sub")

    if not user_id:
        raise ValueError(
            "Invalid refresh token"
        )

    stored_token = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token
            == refresh_token
        )
    )

    if not stored_token:
        raise ValueError(
            "Refresh token not found"
        )

    if stored_token.is_revoked:
        raise ValueError(
            "Refresh token has been revoked"
        )

    if (
        stored_token.expires_at
        < datetime.utcnow()
    ):
        raise ValueError(
            "Refresh token has expired"
        )

    user = db.get(
        User,
        int(user_id),
    )

    if not user:
        raise ValueError(
            "User not found"
        )

    if not user.is_active:
        raise ValueError(
            "User account is inactive"
        )

    new_access_token = create_access_token(
        user.id,
        user.role.name,
    )

    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def logout_user(
    db: Session,
    refresh_token: str,
    user: User,
    ip_address: str | None = None,
):
    stored_token = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token
            == refresh_token
        )
    )

    if not stored_token:
        raise ValueError(
            "Refresh token not found"
        )

    stored_token.is_revoked = True

    create_audit_log(
        db=db,
        user_id=user.id,
        action="LOGOUT",
        entity_type="AUTHENTICATION",
        entity_id=user.id,
        ip_address=ip_address,
        metadata={
            "email": user.email,
        },
    )

    db.commit()

    return {
        "message": "Logged out successfully"
    }


def change_password(
    db: Session,
    user: User,
    current_password: str,
    new_password: str,
    ip_address: str | None = None,
):
    if not verify_password(
        current_password,
        user.password_hash,
    ):
        create_audit_log(
            db=db,
            user_id=user.id,
            action="FAILED_PASSWORD_CHANGE",
            entity_type="AUTHENTICATION",
            entity_id=user.id,
            ip_address=ip_address,
            metadata={
                "reason": "CURRENT_PASSWORD_INCORRECT",
            },
        )

        db.commit()

        raise ValueError(
            "Current password is incorrect"
        )

    if current_password == new_password:
        raise ValueError(
            "New password must be different from current password"
        )

    user.password_hash = hash_password(
        new_password
    )

    create_audit_log(
        db=db,
        user_id=user.id,
        action="PASSWORD_CHANGED",
        entity_type="AUTHENTICATION",
        entity_id=user.id,
        ip_address=ip_address,
        metadata={
            "email": user.email,
        },
    )

    db.commit()

    return {
        "message": "Password changed successfully"
    }