"""Data-source status endpoints (F049)."""
from fastapi import APIRouter

from app.core.config import get_settings
from app.sources import get_default_sources, health

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", summary="List the active data sources")
async def list_sources() -> dict:
    return {"sources": [s.name for s in get_default_sources()]}


@router.get("/health", summary="Per-source health (F049)")
async def source_health() -> dict:
    """Return per-source success/error counts and timestamps.

    Sources that have not been queried yet appear with an 'unknown' status.
    """
    snapshot = {h["source"]: h for h in health.snapshot()}
    settings = get_settings()
    result = []
    for source in get_default_sources():
        result.append(
            snapshot.get(
                source.name,
                {"source": source.name, "status": "unknown", "ok_count": 0, "error_count": 0},
            )
        )
    return {"rate_limit_per_minute": settings.source_rate_limit_per_minute, "sources": result}
