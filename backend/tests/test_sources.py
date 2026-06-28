"""Unit tests for the data-source layer (F044, F047, F049, F050)."""
import time

import pytest

from app.sources import health
from app.sources.base import PriceSource, SourceOffer
from app.sources.http_source import HttpJsonSource, RateLimitedSource


class _SpySource(PriceSource):
    def __init__(self, name="spy"):
        self.name = name
        self.calls = 0

    async def search(self, keyword):
        self.calls += 1
        return [SourceOffer(slug="x", name="X", price=1.0, currency="USD", url="http://x")]


# ── F044 HTTP/JSON mapping ──

def test_http_source_maps_dummyjson_item():
    src = HttpJsonSource(name="demoapi")
    item = {
        "id": 5,
        "title": "Wireless Mouse",
        "price": 19.99,
        "brand": "Acme",
        "category": "accessories",
        "thumbnail": "http://img/5.jpg",
        "stock": 3,
    }
    offer = src._to_offer(item)
    assert offer is not None
    assert offer.slug == "demoapi-5"
    assert offer.name == "Wireless Mouse"
    assert offer.price == 19.99
    assert offer.in_stock is True


def test_http_source_skips_item_without_price():
    src = HttpJsonSource(name="demoapi")
    assert src._to_offer({"id": 1, "title": "No price"}) is None


# ── F047 rate limiting ──

@pytest.mark.asyncio
async def test_rate_limited_source_enforces_interval():
    spy = _SpySource()
    limited = RateLimitedSource(spy, min_interval_seconds=0.2)

    start = time.monotonic()
    await limited.search("a")
    await limited.search("b")
    elapsed = time.monotonic() - start

    assert spy.calls == 2
    assert elapsed >= 0.2  # second call waited for the interval


# ── F049 health ──

@pytest.mark.asyncio
async def test_health_via_search(product_repo, price_repo):
    health.reset()
    from app.services.search_service import SearchService

    class _BoomSource(PriceSource):
        name = "boom"

        async def search(self, keyword):
            raise RuntimeError("down")

    service = SearchService([_SpySource("ok"), _BoomSource()], product_repo, price_repo)
    await service.search("anything")

    by_name = {h["source"]: h for h in health.snapshot()}
    assert by_name["ok"]["status"] == "ok"
    assert by_name["boom"]["status"] == "error"
    assert by_name["boom"]["last_error_message"] == "down"


# ── F050 custom sources from config ──

def test_custom_sources_parsed_from_config(monkeypatch):
    from app.core.config import get_settings
    from app.sources import get_default_sources

    monkeypatch.setattr(
        get_settings(),
        "custom_sources",
        '[{"name":"myapi","url_template":"https://x/search?q={query}","results_path":"items"}]',
    )
    monkeypatch.setattr(get_settings(), "enabled_sources", "myapi")

    sources = get_default_sources()
    assert [s.name for s in sources] == ["myapi"]
    assert isinstance(sources[0], HttpJsonSource)
