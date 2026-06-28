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


def _custom_http_sources() -> list[PriceSource]:
    """Build HTTP sources declared in config (F050)."""
    import json

    from app.core.config import get_settings
    from app.core.logging import get_logger
    from app.sources.http_source import HttpJsonSource

    raw = get_settings().custom_sources.strip()
    if not raw:
        return []
    try:
        specs = json.loads(raw)
    except json.JSONDecodeError as exc:
        get_logger("sources").warning("Ignoring invalid CUSTOM_SOURCES: %s", exc)
        return []
    sources: list[PriceSource] = []
    for spec in specs:
        try:
            sources.append(
                HttpJsonSource(
                    name=spec["name"],
                    url_template=spec.get("url_template", HttpJsonSource.__init__.__defaults__[0]),
                    results_path=spec.get("results_path", "products"),
                    mapping=spec.get("mapping"),
                )
            )
        except (KeyError, TypeError) as exc:
            get_logger("sources").warning("Skipping malformed custom source %s: %s", spec, exc)
    return sources


def get_default_sources() -> list[PriceSource]:
    """Return the sources used by the application.

    Honors the `enabled_sources` flag (F045), adds a built-in real HTTP source
    plus any custom HTTP sources from config (F044/F050), and wraps each source
    in a rate limiter when configured (F047).
    """
    from app.core.config import get_settings
    from app.sources.http_source import HttpJsonSource, RateLimitedSource

    settings = get_settings()
    all_sources: list[PriceSource] = [
        MockAmazonSource(),
        MockEbaySource(),
        MockWalmartSource(),
        # A real network-backed source (F044); off unless added to ENABLED_SOURCES.
        HttpJsonSource(name="demoapi"),
        *_custom_http_sources(),
    ]

    enabled = settings.enabled_source_list
    selected = all_sources if not enabled else [s for s in all_sources if s.name in enabled]
    selected = selected or all_sources

    limit = settings.source_rate_limit_per_minute
    if limit > 0:
        interval = 60.0 / limit
        selected = [RateLimitedSource(s, interval) for s in selected]
    return selected


__all__ = [
    "PriceSource",
    "SourceOffer",
    "MockAmazonSource",
    "MockEbaySource",
    "MockWalmartSource",
    "get_default_sources",
]
