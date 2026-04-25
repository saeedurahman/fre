from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_admin, get_current_client
from app.core.exceptions import BadRequestException, NotFoundException
from app.core.pagination import paginate
from app.core.response import success_response
from app.database import get_db_session
from app.orders.models import OrderStatus
from app.orders.schemas import OrderCreate, OrderResponse, OrderStatusUpdate
from app.orders.service import OrderService


router = APIRouter(tags=["Orders"])


@router.post("/orders", status_code=status.HTTP_201_CREATED)
async def place_order(
    payload: OrderCreate,
    client_id: UUID = Depends(get_current_client),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        order = await OrderService.place_order(session, client_id, payload)
    except ValueError as exc:
        raise BadRequestException(str(exc)) from exc
    return success_response(data=order.model_dump(), message="Order placed", status_code=201)


@router.get("/orders")
async def list_my_orders(
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    client_id: UUID = Depends(get_current_client),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    orders = await OrderService.get_client_orders(
        session=session,
        client_id=client_id,
        status=status_filter,
    )
    items = [OrderResponse.model_validate(order).model_dump() for order in orders]
    paged = paginate(items, page, limit)
    return success_response(data=paged.model_dump(), message="Orders fetched")


@router.get("/orders/{order_id}")
async def get_my_order(
    order_id: UUID,
    client_id: UUID = Depends(get_current_client),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    order = await OrderService.get_client_order_by_id(session, client_id, order_id)
    if order is None:
        raise NotFoundException("Order not found")
    return success_response(data=OrderResponse.model_validate(order).model_dump())


@router.get("/admin/orders")
async def list_admin_orders(
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    client_filter: UUID | None = Query(default=None, alias="client_id"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    _: UUID = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    orders = await OrderService.get_all_orders(
        session=session,
        status=status_filter,
        client_id=client_filter,
    )
    items = [OrderResponse.model_validate(order).model_dump() for order in orders]
    paged = paginate(items, page, limit)
    return success_response(data=paged.model_dump(), message="Orders fetched")


@router.get("/admin/orders/{order_id}")
async def get_admin_order(
    order_id: UUID,
    _: UUID = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    order = await OrderService.get_order_by_id(session, order_id)
    if order is None:
        raise NotFoundException("Order not found")
    return success_response(data=OrderResponse.model_validate(order).model_dump())


@router.patch("/admin/orders/{order_id}/status")
async def update_admin_order_status(
    order_id: UUID,
    payload: OrderStatusUpdate,
    _: UUID = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        updated = await OrderService.update_order_status(session, order_id, payload.status)
    except LookupError as exc:
        raise NotFoundException("Order not found") from exc
    except ValueError as exc:
        raise BadRequestException(str(exc)) from exc
    return success_response(data=updated.model_dump(), message="Order status updated")
