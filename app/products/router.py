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
from app.products.service import ProductService
from app.products.schemas import ProductCreate, ProductResponse, ProductUpdate


router = APIRouter(tags=["Products"])


@router.post(
    "/admin/products",
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    data: ProductCreate,
    _: UUID = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        product = await ProductService.create_product(session, data)
    except ValueError as exc:
        raise BadRequestException("Product internal_code already exists") from exc
    return success_response(
        data=product.model_dump(),
        message="Product created",
        status_code=201,
    )


@router.get("/admin/products")
async def list_admin_products(
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    _: UUID = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    products = await ProductService.get_all_products(session, is_active=is_active)
    items = [ProductResponse.model_validate(product).model_dump() for product in products]
    paged = paginate(items, page, limit)
    return success_response(data=paged.model_dump(), message="Products fetched")


@router.get("/admin/products/{product_id}")
async def get_admin_product(
    product_id: UUID,
    _: UUID = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    product = await ProductService.get_product_by_id(session, product_id)
    if product is None:
        raise NotFoundException("Product not found")
    return success_response(data=ProductResponse.model_validate(product).model_dump())


@router.patch("/admin/products/{product_id}")
async def update_admin_product(
    product_id: UUID,
    data: ProductUpdate,
    _: UUID = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    try:
        updated = await ProductService.update_product(session, product_id, data)
    except LookupError as exc:
        raise NotFoundException("Product not found") from exc
    return success_response(data=updated.model_dump(), message="Product updated")


@router.delete("/admin/products/{product_id}")
async def deactivate_admin_product(
    product_id: UUID,
    _: UUID = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    deactivated = await ProductService.deactivate_product(session, product_id)
    if not deactivated:
        raise NotFoundException("Product not found")
    return success_response(
        data={"message": "Product deactivated"},
        message="Product deactivated",
    )


@router.get("/products")
async def list_client_products(
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    _: UUID = Depends(get_current_client),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    products = await ProductService.get_active_products(session, search=search)
    items = [ProductResponse.model_validate(product).model_dump() for product in products]
    paged = paginate(items, page, limit)
    return success_response(data=paged.model_dump(), message="Products fetched")


@router.get("/products/{product_id}")
async def get_client_product(
    product_id: UUID,
    _: UUID = Depends(get_current_client),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    product = await ProductService.get_product_by_id(session, product_id)
    if product is None or not product.is_active:
        raise NotFoundException("Product not found")
    return success_response(data=ProductResponse.model_validate(product).model_dump())
