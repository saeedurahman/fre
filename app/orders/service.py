from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.clients.models import Location
from app.orders.models import Order, OrderItem, OrderStatus
from app.orders.schemas import OrderCreate, OrderResponse
from app.products.models import Product


VALID_TRANSITIONS = {
    "pending": ["confirmed"],
    "confirmed": ["completed"],
    "completed": [],
}


class OrderService:
    @staticmethod
    async def place_order(
        session: AsyncSession, client_id: UUID, data: OrderCreate
    ) -> OrderResponse:
        if not data.items:
            raise ValueError("Order must have at least 1 item")

        product_ids = [item.product_id for item in data.items]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Duplicate products in order are not allowed")

        if any(item.quantity < 1 for item in data.items):
            raise ValueError("Quantity must be at least 1")

        location_result = await session.execute(
            select(Location).where(Location.id == data.location_id)
        )
        location = location_result.scalar_one_or_none()
        if location is None or location.client_id != client_id:
            raise ValueError("Invalid location for this client")

        products_result = await session.execute(
            select(Product).where(Product.id.in_(product_ids))
        )
        products = products_result.scalars().all()
        products_map = {product.id: product for product in products}

        if len(products_map) != len(product_ids):
            raise ValueError("One or more products do not exist")

        for item in data.items:
            product = products_map[item.product_id]
            if not product.is_active:
                raise ValueError("Inactive products cannot be ordered")

        try:
            order = Order(
                client_id=client_id,
                location_id=data.location_id,
                status=OrderStatus.pending,
            )
            session.add(order)
            await session.flush()

            for item in data.items:
                product = products_map[item.product_id]
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price_at_order=product.price_per_carton,
                )
                session.add(order_item)

            await session.commit()
        except Exception:
            await session.rollback()
            raise

        order_result = await session.execute(
            select(Order)
            .where(Order.id == order.id)
            .options(selectinload(Order.items))
        )
        created_order = order_result.scalar_one()
        return OrderResponse.model_validate(created_order)

    @staticmethod
    async def get_client_orders(
        session: AsyncSession,
        client_id: UUID,
        status: OrderStatus | None = None,
    ) -> list[Order]:
        query = (
            select(Order)
            .where(Order.client_id == client_id)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
        )
        if status is not None:
            query = query.where(Order.status == status)
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_client_order_by_id(
        session: AsyncSession,
        client_id: UUID,
        order_id: UUID,
    ) -> Order | None:
        result = await session.execute(
            select(Order)
            .where(Order.id == order_id, Order.client_id == client_id)
            .options(selectinload(Order.items))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_orders(
        session: AsyncSession,
        status: OrderStatus | None = None,
        client_id: UUID | None = None,
    ) -> list[Order]:
        query = select(Order).options(selectinload(Order.items))
        if status is not None:
            query = query.where(Order.status == status)
        if client_id is not None:
            query = query.where(Order.client_id == client_id)
        query = query.order_by(Order.created_at.desc())
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_order_by_id(session: AsyncSession, order_id: UUID) -> Order | None:
        result = await session.execute(
            select(Order).where(Order.id == order_id).options(selectinload(Order.items))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_order_status(
        session: AsyncSession,
        order_id: UUID,
        new_status: OrderStatus,
    ) -> OrderResponse:
        order = await OrderService.get_order_by_id(session, order_id)
        if order is None:
            raise LookupError("order_not_found")

        current_status = order.status.value
        target_status = new_status.value
        if target_status not in VALID_TRANSITIONS[current_status]:
            raise ValueError(
                f"Invalid status transition: {current_status} → {target_status}"
            )

        order.status = new_status
        await session.commit()
        await session.refresh(order)

        refreshed = await OrderService.get_order_by_id(session, order_id)
        return OrderResponse.model_validate(refreshed)
