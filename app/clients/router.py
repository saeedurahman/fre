from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_admin, get_current_client
from app.core.exceptions import BadRequestException, NotFoundException
from app.core.pagination import paginate
from app.core.response import success_response
from app.clients.schemas import (
    ClientCreate,
    ClientResponse,
    ClientUpdate,
    LocationCreate,
    LocationResponse,
    LocationUpdate,
)
from app.clients.service import ClientService
from app.database import get_db_session


router = APIRouter(tags=["Clients"])


class AdminClientCreateRequest(ClientCreate):
    password: str


class ClientWithLocationsResponse(BaseModel):
    client: ClientResponse
    locations: list[LocationResponse]


@router.post(
    "/admin/clients",
    status_code=status.HTTP_201_CREATED,
)
async def create_client(
    payload: AdminClientCreateRequest,
    _: UUID = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    data = ClientCreate(
        client_code=payload.client_code,
        name=payload.name,
        tax_id=payload.tax_id,
        image_url=payload.image_url,
    )
    try:
        created = await ClientService.create_client(session, data, payload.password)
    except ValueError as exc:
        raise BadRequestException("Client code already exists") from exc
    return success_response(
        data=created.model_dump(),
        message="Client created",
        status_code=201,
    )


@router.get("/admin/clients")
async def list_clients(
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    _: UUID = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    clients = await ClientService.get_all_clients(session, is_active=is_active)
    items = [ClientResponse.model_validate(client).model_dump() for client in clients]
    paged = paginate(items, page, limit)
    return success_response(data=paged.model_dump(), message="Clients fetched")


@router.get("/admin/clients/{client_id}")
async def get_client_details(
    client_id: UUID,
    _: UUID = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        data = await ClientService.get_client_with_locations(session, client_id)
    except LookupError as exc:
        raise NotFoundException("Client not found") from exc
    return success_response(
        data=ClientWithLocationsResponse.model_validate(data).model_dump(),
        message="Client fetched",
    )


@router.patch("/admin/clients/{client_id}")
async def update_client(
    client_id: UUID,
    payload: ClientUpdate,
    _: UUID = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        updated = await ClientService.update_client(session, client_id, payload)
    except LookupError as exc:
        raise NotFoundException("Client not found") from exc
    return success_response(data=updated.model_dump(), message="Client updated")


@router.post(
    "/admin/clients/{client_id}/locations",
    status_code=status.HTTP_201_CREATED,
)
async def add_client_location(
    client_id: UUID,
    payload: LocationCreate,
    _: UUID = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        location = await ClientService.add_location(session, client_id, payload)
    except LookupError as exc:
        raise NotFoundException("Client not found") from exc
    return success_response(
        data=location.model_dump(),
        message="Location added",
        status_code=201,
    )


@router.patch(
    "/admin/clients/{client_id}/locations/{location_id}",
)
async def update_client_location(
    client_id: UUID,
    location_id: UUID,
    payload: LocationUpdate,
    _: UUID = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        updated = await ClientService.update_location(session, client_id, location_id, payload)
    except LookupError as exc:
        if str(exc) == "client_not_found":
            detail = "Client not found"
        else:
            detail = "Location not found"
        raise NotFoundException(detail) from exc
    return success_response(data=updated.model_dump(), message="Location updated")


@router.delete("/admin/clients/{client_id}/locations/{location_id}")
async def delete_client_location(
    client_id: UUID,
    location_id: UUID,
    _: UUID = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        await ClientService.delete_location(session, client_id, location_id)
    except LookupError as exc:
        if str(exc) == "client_not_found":
            detail = "Client not found"
        else:
            detail = "Location not found"
        raise NotFoundException(detail) from exc
    except ValueError as exc:
        if str(exc) == "only_location":
            detail = "Cannot delete the only location"
        else:
            detail = "Location has existing orders"
        raise BadRequestException(detail) from exc

    return success_response(data={"message": "Location deleted"}, message="Location deleted")


@router.get("/me")
async def get_my_profile(
    client_id: UUID = Depends(get_current_client),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    client = await ClientService.get_client_by_id(session, client_id)
    if client is None:
        raise NotFoundException("Client not found")
    return success_response(data=ClientResponse.model_validate(client).model_dump())


@router.get("/me/locations")
async def get_my_locations(
    client_id: UUID = Depends(get_current_client),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    locations = await ClientService.get_client_locations(session, client_id)
    items = [LocationResponse.model_validate(location).model_dump() for location in locations]
    return success_response(data=items, message="Locations fetched")
