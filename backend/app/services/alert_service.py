"""Price-alert business logic: registration and evaluation."""
from datetime import datetime, timezone

from app.domain.models import Alert
from app.domain.schemas import AlertCheckResult, AlertCreate, AlertOut
from app.repositories.alert_repository import AlertRepository
from app.repositories.product_repository import ProductRepository
from app.services.price_service import ProductNotFoundError


class AlertNotifier:
    """Delivers a triggered alert. The MVP just logs; swap for SMTP/push later."""

    async def notify(self, alert: Alert, current_price: float) -> None:
        print(
            f"[ALERT] {alert.email}: product {alert.product_id} dropped to "
            f"{current_price} {alert.currency} (threshold {alert.threshold_price})"
        )


class AlertService:
    def __init__(
        self,
        alert_repo: AlertRepository,
        product_repo: ProductRepository,
        notifier: AlertNotifier | None = None,
    ) -> None:
        self._alerts = alert_repo
        self._products = product_repo
        self._notifier = notifier or AlertNotifier()

    async def create_alert(self, payload: AlertCreate) -> AlertOut:
        """Register an alert, validating that the product exists."""
        product = await self._products.get_with_offers(payload.product_id)
        if product is None:
            raise ProductNotFoundError(f"Product {payload.product_id} not found")

        alert = await self._alerts.add(
            product_id=payload.product_id,
            email=str(payload.email),
            threshold_price=payload.threshold_price,
            currency=payload.currency,
        )
        return AlertOut.model_validate(alert)

    async def list_for_email(self, email: str) -> list[AlertOut]:
        alerts = await self._alerts.list_for_email(email)
        return [AlertOut.model_validate(a) for a in alerts]

    async def check_alerts(self) -> AlertCheckResult:
        """Evaluate all active alerts against current best prices.

        An alert triggers when the cheapest in-stock offer is at or below the
        threshold. Triggered alerts are deactivated so they fire only once.
        """
        active = await self._alerts.list_active()
        triggered: list[AlertOut] = []

        for alert in active:
            best = await self._products.best_offer(alert.product_id)
            if best is None or best.price > alert.threshold_price:
                continue

            alert.active = False
            alert.triggered_at = datetime.now(timezone.utc)
            alert.triggered_price = best.price
            await self._notifier.notify(alert, best.price)
            triggered.append(AlertOut.model_validate(alert))

        return AlertCheckResult(checked=len(active), triggered=triggered)
