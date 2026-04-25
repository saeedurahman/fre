from __future__ import annotations

from typing import Any

from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import AuthService
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.response import success_response
from app.database import get_db_session


router = APIRouter(prefix="/auth", tags=["Auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class ClientLoginRequest(BaseModel):
    client_code: str
    password: str


@router.post("/admin/login")
async def admin_login(
    payload: AdminLoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        token = await AuthService.authenticate_admin(
            session=session,
            email=payload.email,
            password=payload.password,
        )
    except ValueError as exc:
        raise UnauthorizedException("Invalid credentials") from exc

    return success_response(
        data=TokenResponse(access_token=token).model_dump(),
        message="Admin login successful",
        status_code=200,
    )


@router.post("/client/login")
async def client_login(
    payload: ClientLoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        token, is_active = await AuthService.authenticate_client(
            session=session,
            client_code=payload.client_code,
            password=payload.password,
        )
    except ValueError as exc:
        raise UnauthorizedException("Invalid credentials") from exc

    if not is_active:
        raise ForbiddenException("Client account is inactive")

    return success_response(
        data=TokenResponse(access_token=token).model_dump(),
        message="Client login successful",
        status_code=200,
    )
