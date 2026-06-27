"""Seed the database with demo products, current offers, and 30 days of history.

Idempotent: running it twice will not duplicate products (offers are upserted),
though it will append fresh history points. It is intended to run once at first
startup when the database is empty.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Product
from app.repositories.price_repository import PriceRepository
from app.repositories.product_repository import ProductRepository
from app.sources import get_default_sources
from app.sources.catalog import CATALOG

HISTORY_DAYS = 30


async def _already_seeded(session: AsyncSession) -> bool:
    result = await session.execute(select(func.count()).select_from(Product))
    return int(result.scalar_one()) > 0


def _historical_factor(day_offset: int, slug: str) -> float:
    """A smooth, deterministic price curve: a gentle downward trend toward today
    with a stable per-product wobble, scaled to roughly +/-12% of base price."""
    # Trend: older days are a bit pricier (factor closer to 1.12), today ~1.0.
    trend = 1.0 + (day_offset / HISTORY_DAYS) * 0.12
    # Wobble: deterministic per product+day so it looks organic but is stable.
    wobble = (abs(hash(f"{slug}:{day_offset}")) % 60 - 30) / 1000.0  # -0.03..+0.03
    return trend + wobble


async def seed_database(session: AsyncSession) -> bool:
    """Populate demo data. Returns True if seeding ran, False if skipped."""
    if await _already_seeded(session):
        return False

    products = ProductRepository(session)
    prices = PriceRepository(session)
    sources = get_default_sources()
    now = datetime.now(timezone.utc)

    for item in CATALOG:
        product = await products.upsert_product(
            slug=item.slug,
            name=item.name,
            brand=item.brand,
            category=item.category,
            description=item.description,
            image_url=item.image_url,
        )

        for source in sources:
            offers = await source.search(item.name)
            offer = next((o for o in offers if o.slug == item.slug), None)
            if offer is None:
                continue

            # Current offer.
            await products.upsert_offer(
                product_id=product.id,
                source=source.name,
                url=offer.url,
                price=offer.price,
                currency=offer.currency,
                in_stock=offer.in_stock,
                shipping_cost=offer.shipping_cost,
                coupon_code=offer.coupon_code,
                coupon_savings=offer.coupon_savings,
            )

            # Backfilled history: oldest -> newest, ending at the current price.
            for day_offset in range(HISTORY_DAYS, -1, -1):
                factor = _historical_factor(day_offset, f"{item.slug}:{source.name}")
                price = round(item.base_price * factor, 2)
                await prices.add_point(
                    product_id=product.id,
                    source=source.name,
                    price=price,
                    currency=offer.currency,
                    recorded_at=now - timedelta(days=day_offset),
                )

    await session.commit()
    return True


async def seed_on_startup() -> None:
    """Open a session and seed if needed. Called from the app lifespan."""
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        seeded = await seed_database(session)
        if seeded:
            print("[seed] Demo catalog seeded.")
        else:
            print("[seed] Database already contains data; skipping seed.")
