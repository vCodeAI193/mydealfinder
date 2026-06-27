"""The contract every price source must implement."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SourceOffer:
    """A normalized offer returned by a source for a single product.

    Sources speak this neutral shape so the service layer never needs to know
    whether the data came from a mock, an API, or an HTML scraper.
    """

    slug: str  # stable product identity key shared across sources
    name: str
    price: float
    currency: str
    url: str
    in_stock: bool = True
    shipping_cost: float = 0.0  # F011
    coupon_code: str | None = None  # F015
    coupon_savings: float = 0.0  # F015
    brand: str | None = None
    category: str | None = None
    description: str | None = None
    image_url: str | None = None


class PriceSource(ABC):
    """A source of product offers (a shop, marketplace, or scraper)."""

    #: Human-readable, stable identifier for the source (e.g. "amazon").
    name: str = "base"

    @abstractmethod
    async def search(self, keyword: str) -> list[SourceOffer]:
        """Return offers matching `keyword`. Implementations must not raise on
        an empty match — they return an empty list instead."""
        raise NotImplementedError
