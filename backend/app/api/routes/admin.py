"""Admin dashboard, feature-flag management, and audit log (F079–F081)."""
from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AdminServiceDep, AdminUserDep, AuditServiceDep
from app.core import flags
from app.domain.schemas import AdminOverview, AuditEntry, FlagUpdate

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview", response_model=AdminOverview, summary="Admin dashboard data (F079)")
async def overview(admin: AdminUserDep, service: AdminServiceDep) -> AdminOverview:
    return await service.overview()


@router.get("/flags", summary="Current toggleable feature flags (F080)")
async def get_flags(admin: AdminUserDep) -> dict[str, bool]:
    return flags.current()


@router.put("/flags", summary="Toggle a feature flag at runtime (F080)")
async def set_flag(
    update: FlagUpdate, admin: AdminUserDep, audit: AuditServiceDep
) -> dict[str, bool]:
    try:
        flags.set_flag(update.name, update.value)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Unknown flag: {update.name}") from exc
    await audit.record(
        actor=admin.email,
        action="flag.update",
        detail={"name": update.name, "value": update.value},
    )
    return flags.current()


@router.get("/audit", response_model=list[AuditEntry], summary="Recent audit log (F081)")
async def audit_log(
    admin: AdminUserDep,
    service: AuditServiceDep,
    limit: int = Query(50, ge=1, le=500),
) -> list[AuditEntry]:
    return await service.list_recent(limit)
