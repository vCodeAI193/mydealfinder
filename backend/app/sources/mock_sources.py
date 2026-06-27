"""Three mock sources that return offers from the shared demo catalog.

Each source applies a deterministic price multiplier so the same product has a
different (but stable) price per source — exactly what price comparison needs.
A tiny per-source/per-product jitter keeps the numbers realistic without being
random (so tests stay deterministic).
"""
from app.sources.base import PriceSource, SourceOffer
from app.sources.catalog import CatalogItem, find_items


def _stable_jitter(slug: str, source: str) -> float:
    """A deterministic pseudo-offset in the range [-0.04, +0.04] derived from
    the product+source so prices look organic but never change between runs."""
    h = abs(hash(f"{slug}:{source}")) % 81  # 0..80
    return (h - 40) / 1000.0  # -0.040 .. +0.040


class _CatalogSource(PriceSource):
    """Base for mock sources; subclasses set a name, multiplier, and URL host."""

    multiplier: float = 1.0
    host: str = "example.com"

    def _to_offer(self, item: CatalogItem) -> SourceOffer:
        factor = self.multiplier + _stable_jitter(item.slug, self.name)
        price = round(item.base_price * factor, 2)
        return SourceOffer(
            slug=item.slug,
            name=item.name,
            price=price,
            currency="USD",
            url=f"https://www.{self.host}/dp/{item.slug}",
            in_stock=True,
            brand=item.brand,
            category=item.category,
            description=item.description,
            image_url=item.image_url,
        )

    async def search(self, keyword: str) -> list[SourceOffer]:
        return [self._to_offer(item) for item in find_items(keyword)]


class MockAmazonSource(_CatalogSource):
    name = "amazon"
    multiplier = 1.00
    host = "amazon-mock.example.com"


class MockEbaySource(_CatalogSource):
    name = "ebay"
    multiplier = 0.94  # marketplace tends to be a bit cheaper
    host = "ebay-mock.example.com"


class MockWalmartSource(_CatalogSource):
    name = "walmart"
    multiplier = 0.98
    host = "walmart-mock.example.com"
