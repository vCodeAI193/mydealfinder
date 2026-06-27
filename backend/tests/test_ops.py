"""Unit tests for ops/automation: metrics, cache, and scheduled refresh."""
import pytest

from app.core import metrics
from app.services.cache import Cache, make_key
from app.services.refresh_service import RefreshService
from app.sources.mock_sources import MockAmazonSource, MockEbaySource


# ── F083 metrics ──

def test_metrics_counter_and_render():
    metrics.reset()
    metrics.inc("mydealfinder_searches_total")
    metrics.inc("mydealfinder_searches_total", 2)

    out = metrics.render()
    assert "# TYPE mydealfinder_searches_total counter" in out
    assert "mydealfinder_searches_total 3.0" in out


# ── F085/F086 cache ──

def test_cache_key_is_stable_and_order_independent():
    a = make_key("search", {"q": "x", "opts": {"a": 1, "b": 2}})
    b = make_key("search", {"opts": {"b": 2, "a": 1}, "q": "x"})
    assert a == b
    assert a != make_key("search", {"q": "y"})


@pytest.mark.asyncio
async def test_cache_without_redis_is_noop():
    cache = Cache(redis_url=None, ttl_seconds=60)
    assert cache.enabled is False
    assert await cache.get("k") is None
    await cache.set("k", "v")  # must not raise


# ── F046 scheduled refresh ──

@pytest.mark.asyncio
async def test_refresh_all_grows_history(product_repo, price_repo):
    # Seed a known product via one search so it exists in the DB.
    from app.services.search_service import SearchService

    search = SearchService([MockAmazonSource(), MockEbaySource()], product_repo, price_repo)
    await search.search("sony")
    product = (await product_repo.search_by_name("sony"))[0]
    before = len(await price_repo.history_for_product(product.id))

    metrics.reset()
    refresh = RefreshService([MockAmazonSource(), MockEbaySource()], product_repo, price_repo)
    count = await refresh.refresh_all()

    after = len(await price_repo.history_for_product(product.id))
    assert count >= 1
    assert after > before  # refresh appended new history points
    assert "mydealfinder_price_refreshes_total" in metrics.render()
