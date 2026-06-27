"""Price-alert business logic: registration, evaluation, and lifecycle."""
from datetime import datetime, timezone

from app.core import metrics
from app.core.config import get_settings
from app.domain.models import Alert
from app.domain.schemas import (
    AlertCheckResult,
    AlertCreate,
    AlertOut,
    DigestResult,
)
from app.repositories.alert_repository import AlertRepository
from app.repositories.product_repository import ProductRepository
from app.services.notifications import AlertNotifier, ChannelNotifier, build_message
from app.services.price_service import ProductNotFoundError

# Re-exported so existing imports (and tests) keep working.
__all__ = ["AlertService", "AlertNotifier", "AlertLimitError", "AlertNotFoundError"]


class AlertLimitError(Exception):
    """Raised when an email already has the maximum alerts for a product (F025)."""


class AlertNotFoundError(Exception):
    """Raised when an alert id does not exist."""


class AlertService:
    def __init__(
        self,
        alert_repo: AlertRepository,
        product_repo: ProductRepository,
        notifier: AlertNotifier | None = None,
    ) -> None:
        self._alerts = alert_repo
        self._products = product_repo
        self._notifier = notifier or ChannelNotifier()

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
                channel=payload.channel,
                webhook_url=payload.webhook_url,
                frequency=payload.frequency,
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
        """Evaluate all active alerts against current prices/stock.

        Price alerts fire when the best in-stock price is at or below the
        threshold; restock alerts (F027) fire when a product is back in stock.
        Instant alerts notify immediately; daily/weekly ones (F031) are recorded
        and delivered later via :meth:`send_digest`.
        """
        active = await self._alerts.list_active()
        triggered: list[AlertOut] = []
        metrics.inc("mydealfinder_alert_checks_total")

        for alert in active:
            condition_met, price = await self._evaluate(alert)

            if alert.armed and condition_met:
                alert.triggered_at = datetime.now(timezone.utc)
                alert.triggered_price = price
                if alert.frequency == "instant":
                    await self._notifier.notify(alert, price)
                    alert.notified_at = alert.triggered_at
                if alert.recurring:
                    alert.armed = False  # quiet until the condition clears
                else:
                    alert.status = "triggered"
                metrics.inc("mydealfinder_alerts_triggered_total")
                triggered.append(AlertOut.model_validate(alert))
            elif not alert.armed and not condition_met:
                alert.armed = True  # re-arm recurring alert; no notification

        return AlertCheckResult(checked=len(active), triggered=triggered)

    async def send_digest(self, frequency: str) -> DigestResult:
        """Deliver one batched message per recipient for the given frequency (F031)."""
        pending = await self._alerts.list_pending_digest(frequency)
        by_email: dict[str, list[Alert]] = {}
        for alert in pending:
            by_email.setdefault(alert.email, []).append(alert)

        now = datetime.now(timezone.utc)
        for email, alerts in by_email.items():
            lines = [build_message(a, a.triggered_price) for a in alerts]
            await self._notifier.notify_digest(email, lines)
            for a in alerts:
                a.notified_at = now

        return DigestResult(
            frequency=frequency, recipients=len(by_email), notifications=len(pending)
        )

    async def _evaluate(self, alert: Alert) -> tuple[bool, float | None]:
        """Return (condition_met, relevant_price) for an alert."""
        if alert.alert_type == "restock":
            best = await self._products.best_offer(alert.product_id, in_stock_only=True)
            return (best is not None, best.price if best else None)

        threshold = alert.effective_threshold
        best = await self._products.best_offer(alert.product_id, in_stock_only=True)
        if best is None or threshold is None:
            return (False, None)
        return (best.price <= threshold, best.price)

    async def _require(self, alert_id: int) -> Alert:
        alert = await self._alerts.get(alert_id)
        if alert is None:
            raise AlertNotFoundError(f"Alert {alert_id} not found")
        return alert
