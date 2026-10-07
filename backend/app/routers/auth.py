from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
)
from app.services.auth_service import (
    change_password,
    login_user,
    logout_user,
    refresh_access_token,
    register_user,
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post("/register")
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    try:
        user = register_user(
            db,
            data,
        )

        return {
            "message": "User registered successfully",
            "user_id": user.id,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post("/login")
def login(
    request: Request,
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    try:
        ip_address = (
            request.client.host
            if request.client
            else None
        )

        return login_user(
            db,
            data,
            ip_address,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        )


@router.post("/refresh")
def refresh(
    refresh_token: str,
    db: Session = Depends(get_db),
):
    try:
        return refresh_access_token(
            db,
            refresh_token,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        )


@router.post("/logout")
def logout(
    request: Request,
    refresh_token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    try:
        ip_address = (
            request.client.host
            if request.client
            else None
        )

        return logout_user(
            db,
            refresh_token,
            current_user,
            ip_address,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post("/change-password")
def change_password_endpoint(
    request: Request,
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):
    try:
        ip_address = (
            request.client.host
            if request.client
            else None
        )

        return change_password(
            db,
            current_user,
            data.current_password,
            data.new_password,
            ip_address,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get("/me")
def get_me(
    current_user: User = Depends(
        get_current_user
    ),
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role.name,
        "is_active": current_user.is_active,
    }