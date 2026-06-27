"""Persistence for products and their current offers."""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import Offer, Product


class ProductRepository:
    """The only place that issues SQL for products and offers."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_slug(self, slug: str) -> Product | None:
        result = await self._session.execute(select(Product).where(Product.slug == slug))
        return result.scalar_one_or_none()

    async def get_with_offers(self, product_id: int) -> Product | None:
        result = await self._session.execute(
            select(Product)
            .where(Product.id == product_id)
            .options(selectinload(Product.offers))
        )
        return result.scalar_one_or_none()

    async def upsert_product(
        self,
        *,
        slug: str,
        name: str,
        brand: str | None,
        category: str | None,
        description: str | None,
        image_url: str | None,
    ) -> Product:
        """Insert the product if new, otherwise return the existing row."""
        product = await self.get_by_slug(slug)
        if product is None:
            product = Product(
                slug=slug,
                name=name,
                brand=brand,
                category=category,
                description=description,
                image_url=image_url,
            )
            self._session.add(product)
            await self._session.flush()
        return product

    async def upsert_offer(
        self,
        *,
        product_id: int,
        source: str,
        url: str,
        price: float,
        currency: str,
        in_stock: bool,
    ) -> Offer:
        """Update the current offer for (product, source) or create it."""
        result = await self._session.execute(
            select(Offer).where(Offer.product_id == product_id, Offer.source == source)
        )
        offer = result.scalar_one_or_none()
        if offer is None:
            offer = Offer(
                product_id=product_id,
                source=source,
                url=url,
                price=price,
                currency=currency,
                in_stock=in_stock,
            )
            self._session.add(offer)
        else:
            offer.url = url
            offer.price = price
            offer.currency = currency
            offer.in_stock = in_stock
        await self._session.flush()
        return offer

    async def best_offer(self, product_id: int) -> Offer | None:
        """Return the cheapest in-stock offer for a product, if any."""
        result = await self._session.execute(
            select(Offer)
            .where(Offer.product_id == product_id, Offer.in_stock.is_(True))
            .order_by(Offer.price.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def offer_count(self, product_id: int) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(Offer).where(Offer.product_id == product_id)
        )
        return int(result.scalar_one())

    async def search_by_name(self, keyword: str, limit: int = 50) -> list[Product]:
        """Look up already-known products by name (used to serve cached results)."""
        pattern = f"%{keyword.strip().lower()}%"
        result = await self._session.execute(
            select(Product).where(func.lower(Product.name).like(pattern)).limit(limit)
        )
        return list(result.scalars().all())
