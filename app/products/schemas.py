from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    internal_code: str
    name: str
    image_url: str | None = None
    price_per_carton: Decimal
    items_per_carton: int


class ProductUpdate(BaseModel):
    name: str | None = None
    image_url: str | None = None
    price_per_carton: Decimal | None = None
    items_per_carton: int | None = None
    is_active: bool | None = None


class ProductResponse(BaseModel):
    id: UUID
    internal_code: str
    name: str
    image_url: str | None
    price_per_carton: Decimal
    items_per_carton: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
