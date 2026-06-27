"""Unit tests for PriceService detail/comparison/history."""
from datetime import datetime, timedelta, timezone

import pytest

from app.services.price_service import PriceService, ProductNotFoundError


async def _seed_product(product_repo, price_repo):
    product = await product_repo.upsert_product(
        slug="widget",
        name="Widget",
        brand="Acme",
        category="Tools",
        description="A widget",
        image_url=None,
    )
    await product_repo.upsert_offer(
        product_id=product.id, source="a", url="http://a", price=100.0, currency="USD", in_stock=True
    )
    await product_repo.upsert_offer(
        product_id=product.id, source="b", url="http://b", price=80.0, currency="USD", in_stock=True
    )
    await price_repo.add_point(product_id=product.id, source="a", price=110.0, currency="USD")
    await price_repo.add_point(product_id=product.id, source="a", price=100.0, currency="USD")
    return product.id


@pytest.mark.asyncio
async def test_get_product_detail_sorts_offers_cheapest_first(product_repo, price_repo):
    product_id = await _seed_product(product_repo, price_repo)
    service = PriceService(product_repo, price_repo)

    detail = await service.get_product_detail(product_id)

    assert detail.offer_count == 2
    assert [o.price for o in detail.offers] == [80.0, 100.0]
    assert detail.best_price == 80.0


@pytest.mark.asyncio
async def test_get_product_detail_missing_raises(product_repo, price_repo):
    service = PriceService(product_repo, price_repo)
    with pytest.raises(ProductNotFoundError):
        await service.get_product_detail(99999)


@pytest.mark.asyncio
async def test_get_price_history_returns_points_in_order(product_repo, price_repo):
    product_id = await _seed_product(product_repo, price_repo)
    service = PriceService(product_repo, price_repo)

    history = await service.get_price_history(product_id)

    assert history.product_id == product_id
    assert [p.price for p in history.points] == [110.0, 100.0]


async def _seed_history_over_days(product_repo, price_repo, prices_by_age_days):
    """Seed a product whose best in-stock offer is the cheapest of `prices`,
    with one history point per (age_in_days, price) entry."""
    product = await product_repo.upsert_product(
        slug="w", name="W", brand=None, category=None, description=None, image_url=None
    )
    now = datetime.now(timezone.utc)
    for age, price in prices_by_age_days:
        await price_repo.add_point(
            product_id=product.id, source="a", price=price, currency="USD",
            recorded_at=now - timedelta(days=age),
        )
    # Current live offer = the most recent (age 0) price.
    current = next(p for a, p in prices_by_age_days if a == 0)
    await product_repo.upsert_offer(
        product_id=product.id, source="a", url="http://a", price=current, currency="USD", in_stock=True
    )
    return product.id


@pytest.mark.asyncio
async def test_history_window_filters_old_points(product_repo, price_repo):
    pid = await _seed_history_over_days(
        product_repo, price_repo, [(60, 200.0), (10, 150.0), (0, 100.0)]
    )
    service = PriceService(product_repo, price_repo)

    all_pts = await service.get_price_history(pid)
    last_30 = await service.get_price_history(pid, days=30)

    assert len(all_pts.points) == 3
    assert [p.price for p in last_30.points] == [150.0, 100.0]  # 60-day-old dropped


@pytest.mark.asyncio
async def test_analytics_deal_score_and_pct(product_repo, price_repo):
    # History high=200, low=100, current=100 → at the low → score 100.
    pid = await _seed_history_over_days(
        product_repo, price_repo, [(20, 200.0), (10, 150.0), (0, 100.0)]
    )
    service = PriceService(product_repo, price_repo)

    a = await service.get_analytics(pid)

    assert a.sample_size == 3
    assert a.min_price == 100.0 and a.max_price == 200.0 and a.avg_price == 150.0
    assert a.current_price == 100.0
    assert a.deal_score == 100  # current sits at the historical low
    assert a.pct_vs_avg == round((100 - 150) / 150 * 100, 1)  # -33.3


@pytest.mark.asyncio
async def test_analytics_score_at_high_is_low(product_repo, price_repo):
    pid = await _seed_history_over_days(
        product_repo, price_repo, [(20, 100.0), (10, 150.0), (0, 200.0)]
    )
    service = PriceService(product_repo, price_repo)

    a = await service.get_analytics(pid)

    assert a.current_price == 200.0
    assert a.deal_score == 0  # current sits at the historical high


@pytest.mark.asyncio
async def test_analytics_empty_history(product_repo, price_repo):
    product = await product_repo.upsert_product(
        slug="empty", name="Empty", brand=None, category=None, description=None, image_url=None
    )
    service = PriceService(product_repo, price_repo)

    a = await service.get_analytics(product.id)

    assert a.sample_size == 0
    assert a.deal_score is None and a.avg_price is None
