"""Unit tests for AlertService registration and evaluation."""
import pytest

from app.domain.schemas import AlertCreate
from app.services.alert_service import AlertNotifier, AlertService
from app.services.price_service import ProductNotFoundError


class _RecordingNotifier(AlertNotifier):
    def __init__(self):
        self.sent: list[tuple[str, float]] = []

    async def notify(self, alert, current_price):  # type: ignore[override]
        self.sent.append((alert.email, current_price))


async def _make_product(product_repo, price: float):
    product = await product_repo.upsert_product(
        slug="widget", name="Widget", brand=None, category=None, description=None, image_url=None
    )
    await product_repo.upsert_offer(
        product_id=product.id, source="a", url="http://a", price=price, currency="USD", in_stock=True
    )
    return product


@pytest.mark.asyncio
async def test_create_alert_for_missing_product_raises(alert_repo, product_repo):
    service = AlertService(alert_repo, product_repo)
    with pytest.raises(ProductNotFoundError):
        await service.create_alert(
            AlertCreate(product_id=123, email="x@example.com", threshold_price=50.0)
        )


@pytest.mark.asyncio
async def test_check_alerts_triggers_when_price_below_threshold(alert_repo, product_repo):
    product = await _make_product(product_repo, price=80.0)
    notifier = _RecordingNotifier()
    service = AlertService(alert_repo, product_repo, notifier=notifier)

    await service.create_alert(
        AlertCreate(product_id=product.id, email="buyer@example.com", threshold_price=100.0)
    )

    result = await service.check_alerts()

    assert result.checked == 1
    assert len(result.triggered) == 1
    assert result.triggered[0].triggered_price == 80.0
    assert notifier.sent == [("buyer@example.com", 80.0)]


@pytest.mark.asyncio
async def test_check_alerts_does_not_trigger_above_threshold(alert_repo, product_repo):
    product = await _make_product(product_repo, price=120.0)
    service = AlertService(alert_repo, product_repo)
    await service.create_alert(
        AlertCreate(product_id=product.id, email="buyer@example.com", threshold_price=100.0)
    )

    result = await service.check_alerts()

    assert result.checked == 1
    assert result.triggered == []


@pytest.mark.asyncio
async def test_alert_triggers_only_once(alert_repo, product_repo):
    product = await _make_product(product_repo, price=50.0)
    service = AlertService(alert_repo, product_repo)
    await service.create_alert(
        AlertCreate(product_id=product.id, email="buyer@example.com", threshold_price=100.0)
    )

    first = await service.check_alerts()
    second = await service.check_alerts()

    assert len(first.triggered) == 1
    # Deactivated after firing, so the second pass sees no active alerts.
    assert second.checked == 0
    assert second.triggered == []


@pytest.mark.asyncio
async def test_threshold_boundary_is_inclusive(alert_repo, product_repo):
    product = await _make_product(product_repo, price=100.0)
    service = AlertService(alert_repo, product_repo)
    await service.create_alert(
        AlertCreate(product_id=product.id, email="buyer@example.com", threshold_price=100.0)
    )

    result = await service.check_alerts()

    # Price exactly at threshold should trigger (<=).
    assert len(result.triggered) == 1
