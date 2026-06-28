"""Persistence for the audit log (F081)."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, *, actor: str, action: str, detail: str | None) -> AuditLog:
        entry = AuditLog(actor=actor, action=action, detail=detail)
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def list_recent(self, limit: int = 50) -> list[AuditLog]:
        result = await self._session.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())
