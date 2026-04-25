from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.models import Admin
from app.auth.utils import create_access_token, verify_password
from app.clients.models import Client


class AuthService:
    @staticmethod
    async def authenticate_admin(*, session: AsyncSession, email: str, password: str) -> str:
        result = await session.execute(select(Admin).where(Admin.email == email))
        admin = result.scalar_one_or_none()

        if admin is None or not verify_password(password, admin.password_hash):
            raise ValueError("Invalid credentials")

        return create_access_token(subject=str(admin.id), role="admin")

    @staticmethod
    async def authenticate_client(
        *, session: AsyncSession, client_code: str, password: str
    ) -> tuple[str, bool]:
        result = await session.execute(select(Client).where(Client.client_code == client_code))
        client = result.scalar_one_or_none()

        if client is None or not verify_password(password, client.password_hash):
            raise ValueError("Invalid credentials")

        if not client.is_active:
            return "", False

        token = create_access_token(subject=str(client.id), role="client")
        return token, True
