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
    """Return the sources used by the application, honoring the `enabled_sources`
    feature flag (F045). An empty/unknown configuration falls back to all."""
    from app.core.config import get_settings

    all_sources: list[PriceSource] = [
        MockAmazonSource(),
        MockEbaySource(),
        MockWalmartSource(),
    ]
    enabled = get_settings().enabled_source_list
    if not enabled:
        return all_sources
    filtered = [s for s in all_sources if s.name in enabled]
    return filtered or all_sources


__all__ = [
    "PriceSource",
    "SourceOffer",
    "MockAmazonSource",
    "MockEbaySource",
    "MockWalmartSource",
    "get_default_sources",
]
