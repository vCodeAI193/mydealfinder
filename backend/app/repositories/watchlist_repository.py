"""Persistence for user watchlists (F037)."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import WatchlistItem


class WatchlistRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(self, user_id: int) -> list[WatchlistItem]:
        result = await self._session.execute(
            select(WatchlistItem)
            .where(WatchlistItem.user_id == user_id)
            .options(selectinload(WatchlistItem.product))
            .order_by(WatchlistItem.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, user_id: int, product_id: int) -> WatchlistItem | None:
        result = await self._session.execute(
            select(WatchlistItem).where(
                WatchlistItem.user_id == user_id, WatchlistItem.product_id == product_id
            )
        )
        return result.scalar_one_or_none()

    async def add(self, user_id: int, product_id: int) -> WatchlistItem:
        existing = await self.get(user_id, product_id)
        if existing is not None:
            return existing
        item = WatchlistItem(user_id=user_id, product_id=product_id)
        self._session.add(item)
        await self._session.flush()
        return item

    async def remove(self, user_id: int, product_id: int) -> bool:
        item = await self.get(user_id, product_id)
        if item is None:
            return False
        await self._session.delete(item)
        return True
