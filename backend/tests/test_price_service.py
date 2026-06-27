"""Unit tests for PriceService detail/comparison/history."""
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
