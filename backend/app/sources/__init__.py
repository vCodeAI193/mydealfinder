"""Pluggable price sources.

`get_default_sources()` returns the source instances the application queries.
Swap a mock for a real scraper here without touching the service layer.
"""
from app.sources.base import PriceSource, SourceOffer
from app.sources.mock_sources import (
    MockAmazonSource,
    MockEbaySource,
    MockWalmartSource,
)


def get_default_sources() -> list[PriceSource]:
    """Return the list of sources used by the application."""
    return [MockAmazonSource(), MockEbaySource(), MockWalmartSource()]


__all__ = [
    "PriceSource",
    "SourceOffer",
    "MockAmazonSource",
    "MockEbaySource",
    "MockWalmartSource",
    "get_default_sources",
]
