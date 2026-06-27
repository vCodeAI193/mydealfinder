"""Persistence for price alerts."""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Alert


class AlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, alert: Alert) -> Alert:
        self._session.add(alert)
        await self._session.flush()
        return alert

    async def get(self, alert_id: int) -> Alert | None:
        result = await self._session.execute(select(Alert).where(Alert.id == alert_id))
        return result.scalar_one_or_none()

    async def list_active(self) -> list[Alert]:
        """Alerts currently being evaluated (status == 'active')."""
        result = await self._session.execute(select(Alert).where(Alert.status == "active"))
        return list(result.scalars().all())

    async def count_open_for(self, email: str, product_id: int) -> int:
        """Number of non-triggered (active or paused) alerts for this pair."""
        result = await self._session.execute(
            select(func.count())
            .select_from(Alert)
            .where(
                Alert.email == email,
                Alert.product_id == product_id,
                Alert.status != "triggered",
            )
        )
        return int(result.scalar_one())

    async def list_for_email(self, email: str) -> list[Alert]:
        result = await self._session.execute(
            select(Alert).where(Alert.email == email).order_by(Alert.created_at.desc())
        )
        return list(result.scalars().all())
