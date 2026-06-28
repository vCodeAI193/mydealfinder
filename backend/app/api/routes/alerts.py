"""Price-alert endpoints."""
from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AlertServiceDep, AuditServiceDep, PriceServiceDep
from app.domain.schemas import (
    AlertCheckResult,
    AlertCreate,
    AlertOut,
    AlertSuggestion,
    DigestResult,
)
from app.services.alert_service import AlertLimitError, AlertNotFoundError
from app.services.price_service import ProductNotFoundError

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post(
    "",
    response_model=AlertOut,
    status_code=201,
    summary="Create a price alert (absolute or percentage, optionally recurring)",
)
async def create_alert(
    payload: AlertCreate, service: AlertServiceDep, audit: AuditServiceDep
) -> AlertOut:
    try:
        result = await service.create_alert(payload)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AlertLimitError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    await audit.record(
        actor=str(payload.email),
        action="alert.create",
        detail={"product_id": payload.product_id, "type": payload.alert_type},
    )
    return result


@router.get("", response_model=list[AlertOut], summary="List alerts for an email")
async def list_alerts(
    service: AlertServiceDep,
    email: str = Query(..., description="Email the alerts were registered with"),
) -> list[AlertOut]:
    return await service.list_for_email(email)


@router.get(
    "/suggestion",
    response_model=AlertSuggestion,
    summary="Suggest an alert threshold from price history (F034)",
)
async def suggest_threshold(
    service: PriceServiceDep,
    product_id: int = Query(..., description="Product to suggest a threshold for"),
    days: int | None = Query(30, ge=0, le=3650, description="History window in days"),
) -> AlertSuggestion:
    try:
        return await service.suggest_threshold(product_id, days=days)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{alert_id}/pause", response_model=AlertOut, summary="Snooze an alert (F032)")
async def pause_alert(alert_id: int, service: AlertServiceDep) -> AlertOut:
    try:
        return await service.pause_alert(alert_id)
    except AlertNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{alert_id}/resume", response_model=AlertOut, summary="Resume a paused alert (F032)")
async def resume_alert(alert_id: int, service: AlertServiceDep) -> AlertOut:
    try:
        return await service.resume_alert(alert_id)
    except AlertNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/check",
    response_model=AlertCheckResult,
    summary="Evaluate active alerts against current prices",
)
async def check_alerts(service: AlertServiceDep) -> AlertCheckResult:
    """Trigger any alerts whose product is now at or below the threshold, or is
    back in stock. Instant alerts notify immediately; daily/weekly ones are
    queued for the digest.

    In production a scheduler calls this; the MVP exposes it so behaviour is
    easy to demonstrate and test.
    """
    return await service.check_alerts()


@router.post(
    "/digest",
    response_model=DigestResult,
    summary="Deliver batched notifications for a frequency (F031)",
)
async def send_digest(
    service: AlertServiceDep,
    frequency: str = Query("daily", pattern="^(daily|weekly)$"),
) -> DigestResult:
    return await service.send_digest(frequency)
