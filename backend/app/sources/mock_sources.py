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
    # Flat shipping fee; waived when the price is at or above this threshold (F011).
    shipping_fee: float = 0.0
    free_shipping_over: float = 0.0

    def _shipping(self, price: float) -> float:
        if self.shipping_fee and price < self.free_shipping_over:
            return self.shipping_fee
        return 0.0

    def _coupon(self, item: CatalogItem) -> tuple[str | None, float]:
        """Deterministically attach a coupon to ~1/3 of this source's offers (F015)."""
        h = abs(hash(f"{self.name}:coupon:{item.slug}"))
        if h % 3 != 0:
            return None, 0.0
        savings = round(5 + (h % 11), 2)  # 5–15
        return f"{self.name.upper()}{savings:.0f}", savings

    def _to_offer(self, item: CatalogItem) -> SourceOffer:
        factor = self.multiplier + _stable_jitter(item.slug, self.name)
        price = round(item.base_price * factor, 2)
        coupon_code, coupon_savings = self._coupon(item)
        return SourceOffer(
            slug=item.slug,
            name=item.name,
            price=price,
            currency="USD",
            url=f"https://www.{self.host}/dp/{item.slug}",
            in_stock=True,
            shipping_cost=self._shipping(price),
            coupon_code=coupon_code,
            coupon_savings=coupon_savings,
            brand=item.brand,
            category=item.category,
            description=item.description,
            image_url=item.image_url,
        )

    async def search(self, keyword: str) -> list[SourceOffer]:
        from app.core.config import get_settings

        fuzzy = get_settings().fuzzy_search
        return [self._to_offer(item) for item in find_items(keyword, fuzzy=fuzzy)]


class MockAmazonSource(_CatalogSource):
    name = "amazon"
    multiplier = 1.00
    host = "amazon-mock.example.com"
    # Free shipping (Prime-like).


class MockEbaySource(_CatalogSource):
    name = "ebay"
    multiplier = 0.94  # marketplace tends to be a bit cheaper
    host = "ebay-mock.example.com"
    shipping_fee = 6.99  # cheaper item price, but charges shipping
    free_shipping_over = 1_000_000  # effectively always charges


class MockWalmartSource(_CatalogSource):
    name = "walmart"
    multiplier = 0.98
    host = "walmart-mock.example.com"
    shipping_fee = 5.99
    free_shipping_over = 35.0  # free shipping over $35
