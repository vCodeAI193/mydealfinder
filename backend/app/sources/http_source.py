"""A real, network-backed price source (F044) and a rate-limit wrapper (F047)."""
import asyncio
import json
import time
import urllib.parse
import urllib.request

from app.core.logging import get_logger
from app.sources.base import PriceSource, SourceOffer

logger = get_logger("http_source")


def _dig(data: dict | list, path: str | None):
    """Follow a dotted path (e.g. "products") into a nested structure."""
    if not path:
        return data
    cur = data
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


class HttpJsonSource(PriceSource):
    """Fetch offers from any HTTP endpoint that returns JSON.

    Configured entirely by data (URL template + field mapping), so new real
    sources can be added without code changes (F050). The default mapping
    targets the public dummyjson.com products API as a concrete example.
    """

    DEFAULT_MAPPING = {
        "id": "id",
        "name": "title",
        "price": "price",
        "brand": "brand",
        "category": "category",
        "image": "thumbnail",
        "stock": "stock",
    }

    def __init__(
        self,
        name: str,
        url_template: str = "https://dummyjson.com/products/search?q={query}&limit=10",
        *,
        results_path: str | None = "products",
        mapping: dict | None = None,
        timeout: float = 8.0,
    ) -> None:
        self.name = name
        self._url_template = url_template
        self._results_path = results_path
        self._mapping = {**self.DEFAULT_MAPPING, **(mapping or {})}
        self._timeout = timeout

    def _fetch_sync(self, url: str) -> dict | list:
        req = urllib.request.Request(url, headers={"User-Agent": "MyDealFinder/0.1"})
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            return json.loads(resp.read().decode())

    def _to_offer(self, item: dict) -> SourceOffer | None:
        m = self._mapping
        try:
            price = float(item[m["price"]])
        except (KeyError, TypeError, ValueError):
            return None
        raw_id = str(item.get(m["id"], "")) or item.get(m["name"], "")
        slug = f"{self.name}-{raw_id}".lower().replace(" ", "-")
        stock = item.get(m["stock"], 1)
        return SourceOffer(
            slug=slug,
            name=str(item.get(m["name"], "Unknown")),
            price=round(price, 2),
            currency="USD",
            url=self._url_template.split("?")[0] + f"/{raw_id}",
            in_stock=bool(stock),
            brand=item.get(m["brand"]),
            category=item.get(m["category"]),
            description=item.get("description"),
            image_url=item.get(m["image"]),
        )

    async def search(self, keyword: str) -> list[SourceOffer]:
        url = self._url_template.format(query=urllib.parse.quote(keyword))
        data = await asyncio.get_event_loop().run_in_executor(None, self._fetch_sync, url)
        items = _dig(data, self._results_path) or []
        offers = [self._to_offer(i) for i in items if isinstance(i, dict)]
        return [o for o in offers if o is not None]


class RateLimitedSource(PriceSource):
    """Wrap a source to enforce a minimum interval between calls (F047)."""

    def __init__(self, inner: PriceSource, min_interval_seconds: float) -> None:
        self._inner = inner
        self.name = inner.name
        self._min_interval = min_interval_seconds
        self._lock = asyncio.Lock()
        self._last_call = 0.0

    async def search(self, keyword: str) -> list[SourceOffer]:
        async with self._lock:
            elapsed = time.monotonic() - self._last_call
            wait = self._min_interval - elapsed
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call = time.monotonic()
        return await self._inner.search(keyword)
