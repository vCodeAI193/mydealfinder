"""Unit tests for SearchService aggregation logic."""
import pytest

from app.services.search_service import SearchService
from app.sources.base import PriceSource, SourceOffer


class _StubSource(PriceSource):
    """A configurable in-test source returning a fixed offer list."""

    def __init__(self, name: str, offers: list[SourceOffer]):
        self.name = name
        self._offers = offers

    async def search(self, keyword: str) -> list[SourceOffer]:
        return list(self._offers)


class _BoomSource(PriceSource):
    name = "boom"

    async def search(self, keyword: str) -> list[SourceOffer]:
        raise RuntimeError("source is down")


def _offer(slug: str, price: float, name: str = "Widget") -> SourceOffer:
    return SourceOffer(slug=slug, name=name, price=price, currency="USD", url=f"http://x/{slug}")


@pytest.mark.asyncio
async def test_search_aggregates_offers_into_one_product(product_repo, price_repo):
    sources = [
        _StubSource("a", [_offer("widget", 100.0)]),
        _StubSource("b", [_offer("widget", 90.0)]),
        _StubSource("c", [_offer("widget", 95.0)]),
    ]
    service = SearchService(sources, product_repo, price_repo)

    resp = await service.search("widget")

    assert resp.count == 1
    result = resp.results[0]
    assert result.offer_count == 3
    # Best price is the cheapest across sources.
    assert result.best_price == 90.0


@pytest.mark.asyncio
async def test_search_sorts_products_by_best_price(product_repo, price_repo):
    sources = [
        _StubSource("a", [_offer("cheap", 10.0, "Cheap"), _offer("pricey", 500.0, "Pricey")]),
    ]
    service = SearchService(sources, product_repo, price_repo)

    resp = await service.search("anything")

    assert [r.slug for r in resp.results] == ["cheap", "pricey"]


@pytest.mark.asyncio
async def test_search_tolerates_a_failing_source(product_repo, price_repo):
    sources = [
        _StubSource("a", [_offer("widget", 100.0)]),
        _BoomSource(),
    ]
    service = SearchService(sources, product_repo, price_repo)

    resp = await service.search("widget")

    # The healthy source still produces a result despite the broken one.
    assert resp.count == 1
    assert resp.results[0].offer_count == 1


@pytest.mark.asyncio
async def test_search_records_price_history(product_repo, price_repo):
    sources = [_StubSource("a", [_offer("widget", 100.0)])]
    service = SearchService(sources, product_repo, price_repo)

    resp = await service.search("widget")
    product_id = resp.results[0].id

    history = await price_repo.history_for_product(product_id)
    assert len(history) == 1
    assert history[0].price == 100.0


@pytest.mark.asyncio
async def test_repeated_search_updates_offer_not_duplicates(product_repo, price_repo):
    service = SearchService([_StubSource("a", [_offer("widget", 100.0)])], product_repo, price_repo)
    await service.search("widget")

    # Same product, cheaper price on a second search.
    service2 = SearchService([_StubSource("a", [_offer("widget", 80.0)])], product_repo, price_repo)
    resp = await service2.search("widget")

    assert resp.count == 1
    assert resp.results[0].offer_count == 1  # not duplicated
    assert resp.results[0].best_price == 80.0  # updated
