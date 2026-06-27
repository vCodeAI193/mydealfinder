"""Unit tests for the comparison cluster (F011–F015)."""
import pytest

from app.services import currency as fx
from app.services.price_service import PriceService


async def _product_with_offers(product_repo, offers):
    """offers: list of dicts with source/price/shipping/coupon fields."""
    product = await product_repo.upsert_product(
        slug="w", name="W", brand="Acme", category="C", description=None, image_url=None
    )
    for o in offers:
        await product_repo.upsert_offer(
            product_id=product.id,
            source=o["source"],
            url=f"http://{o['source']}",
            price=o["price"],
            currency="USD",
            in_stock=True,
            shipping_cost=o.get("shipping", 0.0),
            coupon_code=o.get("coupon"),
            coupon_savings=o.get("savings", 0.0),
        )
    return product.id


# ── F012: currency conversion ──────────────────────────────────────────────

def test_convert_known_currencies():
    assert fx.convert(100, "USD", "EUR") == 92.0
    assert fx.convert(92, "EUR", "USD") == 100.0


def test_convert_same_or_unknown_is_noop():
    assert fx.convert(50, "USD", "USD") == 50.0
    assert fx.convert(50, "USD", "XYZ") == 50.0


@pytest.mark.asyncio
async def test_detail_converts_currency(product_repo, price_repo):
    pid = await _product_with_offers(product_repo, [{"source": "amazon", "price": 100.0}])
    service = PriceService(product_repo, price_repo)

    detail = await service.get_product_detail(pid, currency="EUR")

    assert detail.currency == "EUR"
    assert detail.offers[0].price == 92.0
    assert detail.best_price == 92.0


# ── F011: shipping-aware "true price" ──────────────────────────────────────

@pytest.mark.asyncio
async def test_true_price_changes_ranking(product_repo, price_repo, monkeypatch):
    from app.services import price_service as mod

    # A: 100 + 0 shipping = 100 ; B: 95 + 10 shipping = 105
    pid = await _product_with_offers(
        product_repo,
        [{"source": "a", "price": 100.0}, {"source": "b", "price": 95.0, "shipping": 10.0}],
    )
    service = PriceService(product_repo, price_repo)

    # Without the flag, B (lower sticker) wins.
    monkeypatch.setattr(mod.get_settings(), "true_price", False)
    by_sticker = await service.get_product_detail(pid)
    assert by_sticker.offers[0].source == "b"
    assert by_sticker.best_price == 95.0

    # With true_price, A (lower total) wins.
    monkeypatch.setattr(mod.get_settings(), "true_price", True)
    by_total = await service.get_product_detail(pid)
    assert by_total.offers[0].source == "a"
    assert by_total.best_price == 100.0
    assert by_total.offers[0].total_price == 100.0


# ── F013: pinned sources ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pinned_source_sorts_first(product_repo, price_repo):
    pid = await _product_with_offers(
        product_repo,
        [{"source": "cheap", "price": 10.0}, {"source": "fav", "price": 99.0}],
    )
    service = PriceService(product_repo, price_repo)

    detail = await service.get_product_detail(pid, pinned=["fav"])

    assert detail.offers[0].source == "fav"
    assert detail.offers[0].pinned is True
    # Best price still reflects the genuinely cheapest offer, not the pin.
    assert detail.best_price == 10.0


# ── F014: source ratings ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_source_rating_respects_flag(product_repo, price_repo, monkeypatch):
    from app.services import price_service as mod

    pid = await _product_with_offers(product_repo, [{"source": "amazon", "price": 100.0}])
    service = PriceService(product_repo, price_repo)

    monkeypatch.setattr(mod.get_settings(), "show_source_ratings", False)
    assert (await service.get_product_detail(pid)).offers[0].source_rating is None

    monkeypatch.setattr(mod.get_settings(), "show_source_ratings", True)
    assert (await service.get_product_detail(pid)).offers[0].source_rating == 4.6


# ── F015: coupons ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_coupon_respects_flag(product_repo, price_repo, monkeypatch):
    from app.services import price_service as mod

    pid = await _product_with_offers(
        product_repo, [{"source": "a", "price": 100.0, "coupon": "SAVE10", "savings": 10.0}]
    )
    service = PriceService(product_repo, price_repo)

    monkeypatch.setattr(mod.get_settings(), "show_coupons", False)
    assert (await service.get_product_detail(pid)).offers[0].coupon_code is None

    monkeypatch.setattr(mod.get_settings(), "show_coupons", True)
    offer = (await service.get_product_detail(pid)).offers[0]
    assert offer.coupon_code == "SAVE10"
    assert offer.coupon_savings == 10.0
