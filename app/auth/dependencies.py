from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.utils import decode_token
from app.clients.models import Client
from app.database import get_db_session


admin_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/admin/login")
client_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/client/login")


def _unauthorized_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_admin(token: str = Depends(admin_oauth2_scheme)) -> UUID:
    try:
        payload = decode_token(token, expected_role="admin")
        role = payload.get("role")
        subject = payload.get("sub")
        if role != "admin" or not subject:
            raise _unauthorized_exception()
        return UUID(subject)
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise
        raise _unauthorized_exception() from exc


async def get_current_client(
    token: str = Depends(client_oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> UUID:
    try:
        payload = decode_token(token, expected_role="client")
        role = payload.get("role")
        subject = payload.get("sub")
        if role != "client" or not subject:
            raise _unauthorized_exception()
        client_id = UUID(subject)
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise
        raise _unauthorized_exception() from exc

    result = await session.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise _unauthorized_exception()
    if not client.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client account is inactive",
        )
    return client_id
