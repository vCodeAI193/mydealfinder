"""Unit tests for SearchService aggregation logic."""
import pytest

from app.services.search_service import SearchOptions, SearchService
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


def _rich_offer(slug, price, *, name, brand, category, in_stock=True):
    return SourceOffer(
        slug=slug,
        name=name,
        price=price,
        currency="USD",
        url=f"http://x/{slug}",
        in_stock=in_stock,
        brand=brand,
        category=category,
    )


@pytest.mark.asyncio
async def test_search_filters_by_brand_and_category(product_repo, price_repo):
    sources = [
        _StubSource(
            "a",
            [
                _rich_offer("a1", 10.0, name="Acme Phone", brand="Acme", category="Phones"),
                _rich_offer("b1", 20.0, name="Globex Phone", brand="Globex", category="Phones"),
                _rich_offer("a2", 30.0, name="Acme Laptop", brand="Acme", category="Laptops"),
            ],
        )
    ]
    service = SearchService(sources, product_repo, price_repo)

    resp = await service.search("x", SearchOptions(brand="Acme", category="Phones"))

    assert [r.slug for r in resp.results] == ["a1"]
    assert resp.count == 1


@pytest.mark.asyncio
async def test_search_filters_by_price_range(product_repo, price_repo):
    sources = [
        _StubSource(
            "a",
            [
                _offer("cheap", 10.0),
                _offer("mid", 50.0),
                _offer("pricey", 500.0),
            ],
        )
    ]
    service = SearchService(sources, product_repo, price_repo)

    resp = await service.search("x", SearchOptions(min_price=20, max_price=100))

    assert [r.slug for r in resp.results] == ["mid"]


@pytest.mark.asyncio
async def test_search_sort_desc_and_name(product_repo, price_repo):
    offers = [_offer("a", 30.0, "Zeta"), _offer("b", 10.0, "Alpha"), _offer("c", 20.0, "Mid")]
    service = SearchService([_StubSource("s", offers)], product_repo, price_repo)

    desc = await service.search("x", SearchOptions(sort="price_desc"))
    assert [r.best_price for r in desc.results] == [30.0, 20.0, 10.0]

    by_name = await service.search("x", SearchOptions(sort="name"))
    assert [r.name for r in by_name.results] == ["Alpha", "Mid", "Zeta"]


@pytest.mark.asyncio
async def test_search_pagination(product_repo, price_repo):
    offers = [_offer(f"p{i}", float(i)) for i in range(1, 6)]  # 5 products
    service = SearchService([_StubSource("s", offers)], product_repo, price_repo)

    resp = await service.search("x", SearchOptions(page=2, page_size=2, sort="price_asc"))

    assert resp.count == 5  # total before pagination
    assert resp.page == 2
    assert [r.best_price for r in resp.results] == [3.0, 4.0]


@pytest.mark.asyncio
async def test_in_stock_only_toggle_controls_best_price(product_repo, price_repo):
    offers = [_rich_offer("oos", 42.0, name="OOS", brand="A", category="C", in_stock=False)]
    service = SearchService([_StubSource("s", offers)], product_repo, price_repo)

    # Default excludes out-of-stock offers, so there is no best price.
    default = await service.search("x")
    assert default.results[0].best_price is None

    # With the toggle off, the out-of-stock price is considered.
    including = await service.search("x", SearchOptions(in_stock_only=False))
    assert including.results[0].best_price == 42.0


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
