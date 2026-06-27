"""Persistence for historical price points."""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import PricePoint


class PriceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_point(
        self,
        *,
        product_id: int,
        source: str,
        price: float,
        currency: str,
        recorded_at: datetime | None = None,
    ) -> PricePoint:
        point = PricePoint(
            product_id=product_id,
            source=source,
            price=price,
            currency=currency,
        )
        if recorded_at is not None:
            point.recorded_at = recorded_at
        self._session.add(point)
        await self._session.flush()
        return point

    async def history_for_product(self, product_id: int) -> list[PricePoint]:
        result = await self._session.execute(
            select(PricePoint)
            .where(PricePoint.product_id == product_id)
            .order_by(PricePoint.recorded_at.asc())
        )
        return list(result.scalars().all())
