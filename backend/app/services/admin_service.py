"""Admin dashboard aggregation (F079)."""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Alert, Offer, Product, User
from app.domain.schemas import AdminOverview
from app.services.audit_service import AuditService
from app.sources import get_default_sources, health


class AdminService:
    def __init__(self, session: AsyncSession, audit: AuditService) -> None:
        self._session = session
        self._audit = audit

    async def _count(self, model, *where) -> int:
        stmt = select(func.count()).select_from(model)
        for clause in where:
            stmt = stmt.where(clause)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def overview(self) -> AdminOverview:
        snapshot = {h["source"]: h for h in health.snapshot()}
        sources = [
            snapshot.get(s.name, {"source": s.name, "status": "unknown", "ok_count": 0, "error_count": 0})
            for s in get_default_sources()
        ]
        return AdminOverview(
            products=await self._count(Product),
            offers=await self._count(Offer),
            alerts_active=await self._count(Alert, Alert.status == "active"),
            users=await self._count(User),
            sources=sources,
            recent_audit=await self._audit.list_recent(20),
        )
