from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.products.models import Product
from app.products.schemas import ProductCreate, ProductResponse, ProductUpdate


class ProductService:
    @staticmethod
    async def create_product(session: AsyncSession, data: ProductCreate) -> ProductResponse:
        existing_query = select(Product).where(Product.internal_code == data.internal_code)
        existing_result = await session.execute(existing_query)
        if existing_result.scalar_one_or_none() is not None:
            raise ValueError("internal_code_exists")

        product = Product(
            internal_code=data.internal_code,
            name=data.name,
            image_url=data.image_url,
            price_per_carton=data.price_per_carton,
            items_per_carton=data.items_per_carton,
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return ProductResponse.model_validate(product)

    @staticmethod
    async def get_all_products(
        session: AsyncSession, is_active: bool | None = None
    ) -> list[Product]:
        query = select(Product)
        if is_active is not None:
            query = query.where(Product.is_active == is_active)
        result = await session.execute(query.order_by(Product.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def get_product_by_id(session: AsyncSession, product_id: UUID) -> Product | None:
        result = await session.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_product(
        session: AsyncSession, product_id: UUID, data: ProductUpdate
    ) -> ProductResponse:
        product = await ProductService.get_product_by_id(session, product_id)
        if product is None:
            raise LookupError("product_not_found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        await session.commit()
        await session.refresh(product)
        return ProductResponse.model_validate(product)

    @staticmethod
    async def deactivate_product(session: AsyncSession, product_id: UUID) -> bool:
        product = await ProductService.get_product_by_id(session, product_id)
        if product is None:
            return False

        product.is_active = False
        await session.commit()
        return True

    @staticmethod
    async def get_active_products(
        session: AsyncSession, search: str | None = None
    ) -> list[Product]:
        query = select(Product).where(Product.is_active.is_(True))
        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Product.name.ilike(term),
                    Product.internal_code.ilike(term),
                )
            )
        result = await session.execute(query.order_by(Product.created_at.desc()))
        return list(result.scalars().all())
