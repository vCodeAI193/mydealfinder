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


@pytest.mark.asyncio
async def test_percentage_alert_uses_creation_price_as_reference(alert_repo, product_repo):
    product = await _make_product(product_repo, price=100.0)
    service = AlertService(alert_repo, product_repo)

    # 10% drop alert created at price 100 → effective threshold 90.
    out = await service.create_alert(
        AlertCreate(
            product_id=product.id,
            email="b@example.com",
            alert_type="percentage",
            threshold_pct=10,
        )
    )
    assert out.reference_price == 100.0
    assert out.effective_threshold == 90.0

    # Price drops to 95 → above 90 → no trigger.
    await product_repo.upsert_offer(
        product_id=product.id, source="a", url="http://a", price=95.0, currency="USD", in_stock=True
    )
    assert (await service.check_alerts()).triggered == []

    # Price drops to 88 → below 90 → trigger.
    await product_repo.upsert_offer(
        product_id=product.id, source="a", url="http://a", price=88.0, currency="USD", in_stock=True
    )
    assert len((await service.check_alerts()).triggered) == 1


@pytest.mark.asyncio
async def test_recurring_alert_refires_after_price_recovers(alert_repo, product_repo):
    product = await _make_product(product_repo, price=80.0)
    service = AlertService(alert_repo, product_repo)
    await service.create_alert(
        AlertCreate(
            product_id=product.id, email="b@example.com", threshold_price=100.0, recurring=True
        )
    )

    # First drop fires.
    assert len((await service.check_alerts()).triggered) == 1
    # Still below threshold but disarmed → no repeat notification.
    assert (await service.check_alerts()).triggered == []

    # Price recovers above threshold → silently re-arms (no trigger).
    await product_repo.upsert_offer(
        product_id=product.id, source="a", url="http://a", price=120.0, currency="USD", in_stock=True
    )
    assert (await service.check_alerts()).triggered == []

    # Drops again → fires a second time.
    await product_repo.upsert_offer(
        product_id=product.id, source="a", url="http://a", price=90.0, currency="USD", in_stock=True
    )
    assert len((await service.check_alerts()).triggered) == 1


@pytest.mark.asyncio
async def test_pause_and_resume_alert(alert_repo, product_repo):
    product = await _make_product(product_repo, price=50.0)
    service = AlertService(alert_repo, product_repo)
    created = await service.create_alert(
        AlertCreate(product_id=product.id, email="b@example.com", threshold_price=100.0)
    )

    paused = await service.pause_alert(created.id)
    assert paused.status == "paused"
    # Paused alert is not evaluated.
    assert (await service.check_alerts()).checked == 0

    resumed = await service.resume_alert(created.id)
    assert resumed.status == "active"
    assert len((await service.check_alerts()).triggered) == 1


@pytest.mark.asyncio
async def test_per_product_alert_limit(alert_repo, product_repo, monkeypatch):
    from app.services import alert_service as mod

    product = await _make_product(product_repo, price=100.0)
    service = AlertService(alert_repo, product_repo)

    # Cap at 1 alert per product/email (F025).
    monkeypatch.setattr(mod.get_settings(), "max_alerts_per_product", 1)

    await service.create_alert(
        AlertCreate(product_id=product.id, email="b@example.com", threshold_price=90.0)
    )
    with pytest.raises(mod.AlertLimitError):
        await service.create_alert(
            AlertCreate(product_id=product.id, email="b@example.com", threshold_price=80.0)
        )


@pytest.mark.asyncio
async def test_suggest_threshold(product_repo, price_repo):
    from app.services.price_service import PriceService

    product = await product_repo.upsert_product(
        slug="w", name="W", brand=None, category=None, description=None, image_url=None
    )
    await product_repo.upsert_offer(
        product_id=product.id, source="a", url="http://a", price=100.0, currency="USD", in_stock=True
    )
    for price in (120.0, 100.0):
        await price_repo.add_point(product_id=product.id, source="a", price=price, currency="USD")

    suggestion = await PriceService(product_repo, price_repo).suggest_threshold(product.id)

    # min(current=100, avg=110) * 0.97 = 97.0
    assert suggestion.suggested_threshold == 97.0
