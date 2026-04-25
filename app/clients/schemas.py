from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ClientCreate(BaseModel):
    client_code: str
    name: str
    tax_id: str
    image_url: str | None = None


class ClientUpdate(BaseModel):
    name: str | None = None
    tax_id: str | None = None
    image_url: str | None = None
    is_active: bool | None = None


class ClientResponse(BaseModel):
    id: UUID
    client_code: str
    name: str
    tax_id: str
    image_url: str | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LocationCreate(BaseModel):
    label: str
    address: str
    is_default: bool


class LocationUpdate(BaseModel):
    label: str | None = None
    address: str | None = None
    is_default: bool | None = None


class LocationResponse(BaseModel):
    id: UUID
    client_id: UUID
    label: str
    address: str
    is_default: bool

    model_config = ConfigDict(from_attributes=True)
