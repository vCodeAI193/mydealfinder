"""Scheduled price refresh (F046).

Re-queries the configured sources for every known product so offers stay current
and the price history keeps growing. Reuses the SearchService persistence
pipeline rather than duplicating it.
"""
from app.core import metrics
from app.repositories.price_repository import PriceRepository
from app.repositories.product_repository import ProductRepository
from app.services.search_service import SearchService
from app.sources.base import PriceSource


class RefreshService:
    def __init__(
        self,
        sources: list[PriceSource],
        product_repo: ProductRepository,
        price_repo: PriceRepository,
    ) -> None:
        self._products = product_repo
        self._search = SearchService(sources, product_repo, price_repo)

    async def refresh_all(self) -> int:
        """Refresh offers/history for all known products. Returns the count."""
        products = await self._products.list_all()
        names = sorted({p.name for p in products})
        for name in names:
            await self._search.search(name)
        metrics.inc("mydealfinder_price_refreshes_total", len(names))
        return len(names)
