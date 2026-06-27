"""Price-alert business logic: registration, evaluation, and lifecycle."""
from datetime import datetime, timezone

from app.core.config import get_settings
from app.domain.models import Alert
from app.domain.schemas import AlertCheckResult, AlertCreate, AlertOut
from app.repositories.alert_repository import AlertRepository
from app.repositories.product_repository import ProductRepository
from app.services.price_service import ProductNotFoundError


class AlertLimitError(Exception):
    """Raised when an email already has the maximum alerts for a product (F025)."""


class AlertNotFoundError(Exception):
    """Raised when an alert id does not exist."""


class AlertNotifier:
    """Delivers a triggered alert. The MVP just logs; swap for SMTP/push later."""

    async def notify(self, alert: Alert, current_price: float) -> None:
        print(
            f"[ALERT] {alert.email}: product {alert.product_id} dropped to "
            f"{current_price} {alert.currency} (threshold {alert.effective_threshold})"
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
        """Register an alert, validating the product exists and the per-product
        limit (F025) is not exceeded. Percentage alerts capture the current best
        price as their reference (F026)."""
        product = await self._products.get_with_offers(payload.product_id)
        if product is None:
            raise ProductNotFoundError(f"Product {payload.product_id} not found")

        cap = get_settings().max_alerts_per_product
        if cap > 0:
            open_count = await self._alerts.count_open_for(str(payload.email), payload.product_id)
            if open_count >= cap:
                raise AlertLimitError(
                    f"Maximum of {cap} alert(s) per product reached for {payload.email}"
                )

        reference_price = None
        if payload.alert_type == "percentage":
            best = await self._products.best_offer(payload.product_id)
            reference_price = best.price if best else None

        alert = await self._alerts.add(
            Alert(
                product_id=payload.product_id,
                email=str(payload.email),
                alert_type=payload.alert_type,
                threshold_price=payload.threshold_price,
                threshold_pct=payload.threshold_pct,
                reference_price=reference_price,
                recurring=payload.recurring,
                currency=payload.currency,
            )
        )
        return AlertOut.model_validate(alert)

    async def list_for_email(self, email: str) -> list[AlertOut]:
        alerts = await self._alerts.list_for_email(email)
        return [AlertOut.model_validate(a) for a in alerts]

    async def pause_alert(self, alert_id: int) -> AlertOut:
        """Snooze an alert so it is no longer evaluated (F032)."""
        alert = await self._require(alert_id)
        if alert.status != "triggered":
            alert.status = "paused"
        return AlertOut.model_validate(alert)

    async def resume_alert(self, alert_id: int) -> AlertOut:
        """Re-activate a paused alert (F032)."""
        alert = await self._require(alert_id)
        if alert.status == "paused":
            alert.status = "active"
            alert.armed = True
        return AlertOut.model_validate(alert)

    async def check_alerts(self) -> AlertCheckResult:
        """Evaluate all active alerts against current best prices.

        A one-shot alert fires once and moves to 'triggered'. A recurring alert
        (F033) fires, then disarms (stays active) until the price rises back
        above its threshold, at which point it silently re-arms.
        """
        active = await self._alerts.list_active()
        triggered: list[AlertOut] = []

        for alert in active:
            threshold = alert.effective_threshold
            best = await self._products.best_offer(alert.product_id)
            if best is None or threshold is None:
                continue
            price = best.price

            if alert.armed and price <= threshold:
                alert.triggered_at = datetime.now(timezone.utc)
                alert.triggered_price = price
                await self._notifier.notify(alert, price)
                if alert.recurring:
                    alert.armed = False  # stay active but quiet until price recovers
                else:
                    alert.status = "triggered"
                triggered.append(AlertOut.model_validate(alert))
            elif not alert.armed and price > threshold:
                alert.armed = True  # re-arm recurring alert; no notification

        return AlertCheckResult(checked=len(active), triggered=triggered)

    async def _require(self, alert_id: int) -> Alert:
        alert = await self._alerts.get(alert_id)
        if alert is None:
            raise AlertNotFoundError(f"Alert {alert_id} not found")
        return alert
