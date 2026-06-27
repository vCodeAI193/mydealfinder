"""Search business logic: query sources, aggregate, persist, record history."""
import asyncio

from app.domain.models import Product
from app.domain.schemas import ProductSummary, SearchResponse
from app.repositories.price_repository import PriceRepository
from app.repositories.product_repository import ProductRepository
from app.sources.base import PriceSource, SourceOffer


class SearchService:
    """Aggregates offers from all configured sources into comparable products.

    Knows nothing about HTTP or SQL details — it orchestrates sources and
    repositories to fulfil a keyword search.
    """

    def __init__(
        self,
        sources: list[PriceSource],
        product_repo: ProductRepository,
        price_repo: PriceRepository,
    ) -> None:
        self._sources = sources
        self._products = product_repo
        self._prices = price_repo

    async def search(self, keyword: str) -> SearchResponse:
        offers_by_source = await self._gather_offers(keyword)

        # Group all source offers by the product slug so we can build one
        # product with many offers.
        grouped: dict[str, list[tuple[str, SourceOffer]]] = {}
        for source_name, offers in offers_by_source.items():
            for offer in offers:
                grouped.setdefault(offer.slug, []).append((source_name, offer))

        summaries: list[ProductSummary] = []
        for slug, source_offers in grouped.items():
            product = await self._persist_product_and_offers(slug, source_offers)
            summaries.append(await self._summarize(product))

        # Cheapest products first; products with no price sink to the bottom.
        summaries.sort(key=lambda s: (s.best_price is None, s.best_price or 0.0))

        return SearchResponse(query=keyword, count=len(summaries), results=summaries)

    async def _gather_offers(self, keyword: str) -> dict[str, list[SourceOffer]]:
        """Query every source concurrently; a failing source yields no offers."""
        results = await asyncio.gather(
            *(source.search(keyword) for source in self._sources),
            return_exceptions=True,
        )
        out: dict[str, list[SourceOffer]] = {}
        for source, result in zip(self._sources, results):
            out[source.name] = [] if isinstance(result, BaseException) else result
        return out

    async def _persist_product_and_offers(
        self, slug: str, source_offers: list[tuple[str, SourceOffer]]
    ) -> Product:
        first = source_offers[0][1]
        product = await self._products.upsert_product(
            slug=slug,
            name=first.name,
            brand=first.brand,
            category=first.category,
            description=first.description,
            image_url=first.image_url,
        )
        for source_name, offer in source_offers:
            await self._products.upsert_offer(
                product_id=product.id,
                source=source_name,
                url=offer.url,
                price=offer.price,
                currency=offer.currency,
                in_stock=offer.in_stock,
            )
            # Every observation is recorded so the history grows over time.
            await self._prices.add_point(
                product_id=product.id,
                source=source_name,
                price=offer.price,
                currency=offer.currency,
            )
        return product

    async def _summarize(self, product: Product) -> ProductSummary:
        best = await self._products.best_offer(product.id)
        count = await self._products.offer_count(product.id)
        return ProductSummary(
            id=product.id,
            slug=product.slug,
            name=product.name,
            brand=product.brand,
            category=product.category,
            image_url=product.image_url,
            best_price=best.price if best else None,
            currency=best.currency if best else None,
            offer_count=count,
        )
