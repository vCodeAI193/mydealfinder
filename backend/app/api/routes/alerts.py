"""Price-alert endpoints."""
from fastapi import APIRouter, HTTPException, Query

from app.api.deps import AlertServiceDep
from app.domain.schemas import AlertCheckResult, AlertCreate, AlertOut
from app.services.price_service import ProductNotFoundError

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post(
    "",
    response_model=AlertOut,
    status_code=201,
    summary="Create a price alert for a product",
)
async def create_alert(payload: AlertCreate, service: AlertServiceDep) -> AlertOut:
    try:
        return await service.create_alert(payload)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_model=list[AlertOut], summary="List alerts for an email")
async def list_alerts(
    service: AlertServiceDep,
    email: str = Query(..., description="Email the alerts were registered with"),
) -> list[AlertOut]:
    return await service.list_for_email(email)


@router.post(
    "/check",
    response_model=AlertCheckResult,
    summary="Evaluate active alerts against current prices",
)
async def check_alerts(service: AlertServiceDep) -> AlertCheckResult:
    """Trigger any alerts whose product is now at or below the threshold.

    In production a scheduler calls this; the MVP exposes it so behaviour is
    easy to demonstrate and test.
    """
    return await service.check_alerts()
