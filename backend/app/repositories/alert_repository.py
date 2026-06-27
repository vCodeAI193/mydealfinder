"""Persistence for price alerts."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Alert


class AlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(
        self,
        *,
        product_id: int,
        email: str,
        threshold_price: float,
        currency: str,
    ) -> Alert:
        alert = Alert(
            product_id=product_id,
            email=email,
            threshold_price=threshold_price,
            currency=currency,
        )
        self._session.add(alert)
        await self._session.flush()
        return alert

    async def get(self, alert_id: int) -> Alert | None:
        result = await self._session.execute(select(Alert).where(Alert.id == alert_id))
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Alert]:
        result = await self._session.execute(select(Alert).where(Alert.active.is_(True)))
        return list(result.scalars().all())

    async def list_for_email(self, email: str) -> list[Alert]:
        result = await self._session.execute(
            select(Alert).where(Alert.email == email).order_by(Alert.created_at.desc())
        )
        return list(result.scalars().all())
