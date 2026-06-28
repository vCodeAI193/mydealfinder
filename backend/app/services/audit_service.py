"""Audit-log business logic (F081)."""
import json

from app.domain.schemas import AuditEntry
from app.repositories.audit_repository import AuditRepository


class AuditService:
    def __init__(self, repo: AuditRepository) -> None:
        self._repo = repo

    async def record(self, *, actor: str, action: str, detail: dict | None = None) -> None:
        """Record an action. Best-effort: never raise into the caller's flow."""
        try:
            await self._repo.add(
                actor=actor or "anonymous",
                action=action,
                detail=json.dumps(detail) if detail else None,
            )
        except Exception:
            pass

    async def list_recent(self, limit: int = 50) -> list[AuditEntry]:
        entries = await self._repo.list_recent(limit)
        return [
            AuditEntry(
                id=e.id,
                created_at=e.created_at,
                actor=e.actor,
                action=e.action,
                detail=e.detail,
            )
            for e in entries
        ]
