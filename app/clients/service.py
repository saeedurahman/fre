from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.utils import hash_password
from app.clients.models import Client, Location
from app.clients.schemas import (
    ClientCreate,
    ClientResponse,
    ClientUpdate,
    LocationCreate,
    LocationResponse,
    LocationUpdate,
)
from app.orders.models import Order


class ClientService:
    @staticmethod
    async def create_client(
        session: AsyncSession, data: ClientCreate, password: str
    ) -> ClientResponse:
        existing = await session.execute(
            select(Client).where(Client.client_code == data.client_code)
        )
        if existing.scalar_one_or_none() is not None:
            raise ValueError("client_code_exists")

        client = Client(
            client_code=data.client_code,
            name=data.name,
            tax_id=data.tax_id,
            image_url=data.image_url,
            password_hash=hash_password(password),
        )
        session.add(client)
        await session.commit()
        await session.refresh(client)
        return ClientResponse.model_validate(client)

    @staticmethod
    async def get_all_clients(
        session: AsyncSession, is_active: bool | None = None
    ) -> list[Client]:
        query = select(Client)
        if is_active is not None:
            query = query.where(Client.is_active == is_active)
        result = await session.execute(query.order_by(Client.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def get_client_by_id(session: AsyncSession, client_id: UUID) -> Client | None:
        result = await session.execute(select(Client).where(Client.id == client_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_client_with_locations(session: AsyncSession, client_id: UUID) -> dict:
        query = (
            select(Client)
            .where(Client.id == client_id)
            .options(selectinload(Client.locations))
        )
        result = await session.execute(query)
        client = result.scalar_one_or_none()
        if client is None:
            raise LookupError("client_not_found")
        return {
            "client": ClientResponse.model_validate(client),
            "locations": [LocationResponse.model_validate(loc) for loc in client.locations],
        }

    @staticmethod
    async def update_client(
        session: AsyncSession, client_id: UUID, data: ClientUpdate
    ) -> ClientResponse:
        client = await ClientService.get_client_by_id(session, client_id)
        if client is None:
            raise LookupError("client_not_found")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(client, field, value)

        await session.commit()
        await session.refresh(client)
        return ClientResponse.model_validate(client)

    @staticmethod
    async def add_location(
        session: AsyncSession, client_id: UUID, data: LocationCreate
    ) -> LocationResponse:
        client = await ClientService.get_client_by_id(session, client_id)
        if client is None:
            raise LookupError("client_not_found")

        if data.is_default:
            locations = (
                await session.execute(select(Location).where(Location.client_id == client_id))
            ).scalars().all()
            for loc in locations:
                loc.is_default = False

        location = Location(
            client_id=client_id,
            label=data.label,
            address=data.address,
            is_default=data.is_default,
        )
        session.add(location)
        await session.commit()
        await session.refresh(location)
        return LocationResponse.model_validate(location)

    @staticmethod
    async def update_location(
        session: AsyncSession,
        client_id: UUID,
        location_id: UUID,
        data: LocationUpdate,
    ) -> LocationResponse:
        client = await ClientService.get_client_by_id(session, client_id)
        if client is None:
            raise LookupError("client_not_found")

        location_result = await session.execute(
            select(Location).where(
                Location.id == location_id,
                Location.client_id == client_id,
            )
        )
        location = location_result.scalar_one_or_none()
        if location is None:
            raise LookupError("location_not_found")

        update_data = data.model_dump(exclude_unset=True)
        if update_data.get("is_default") is True:
            locations = (
                await session.execute(select(Location).where(Location.client_id == client_id))
            ).scalars().all()
            for loc in locations:
                if loc.id != location_id:
                    loc.is_default = False

        for field, value in update_data.items():
            setattr(location, field, value)

        await session.commit()
        await session.refresh(location)
        return LocationResponse.model_validate(location)

    @staticmethod
    async def delete_location(
        session: AsyncSession, client_id: UUID, location_id: UUID
    ) -> bool:
        client = await ClientService.get_client_by_id(session, client_id)
        if client is None:
            raise LookupError("client_not_found")

        location_result = await session.execute(
            select(Location).where(
                Location.id == location_id,
                Location.client_id == client_id,
            )
        )
        location = location_result.scalar_one_or_none()
        if location is None:
            raise LookupError("location_not_found")

        all_locations = (
            await session.execute(select(Location).where(Location.client_id == client_id))
        ).scalars().all()
        if len(all_locations) <= 1:
            raise ValueError("only_location")

        order_result = await session.execute(
            select(Order.id).where(Order.location_id == location_id).limit(1)
        )
        if order_result.scalar_one_or_none() is not None:
            raise ValueError("has_orders")

        await session.delete(location)
        await session.commit()
        return True

    @staticmethod
    async def get_client_locations(session: AsyncSession, client_id: UUID) -> list[Location]:
        result = await session.execute(
            select(Location)
            .where(Location.client_id == client_id)
            .order_by(Location.is_default.desc(), Location.label.asc())
        )
        return list(result.scalars().all())
