"""Search business logic: query sources, aggregate, persist, record history."""
import asyncio
from dataclasses import dataclass

from app.core import metrics
from app.core.config import get_settings
from app.domain.models import Product
from app.domain.schemas import ProductSummary, SearchResponse
from app.repositories.price_repository import PriceRepository
from app.repositories.product_repository import ProductRepository
from app.services import currency as fx
from app.services.cache import Cache, make_key
from app.sources.base import PriceSource, SourceOffer

# Supported result orderings (F005).
SORT_OPTIONS = ("price_asc", "price_desc", "name")


@dataclass
class SearchOptions:
    """User-configurable search refinements (F003–F006, F010).

    All fields are optional; the defaults reproduce the original behaviour
    (cheapest first, in-stock only, first page of 20).
    """

    category: str | None = None  # F003
    brand: str | None = None  # F003
    min_price: float | None = None  # F004
    max_price: float | None = None  # F004
    sort: str = "price_asc"  # F005
    in_stock_only: bool = True  # F010
    currency: str | None = None  # F012
    page: int = 1  # F006
    page_size: int = 20  # F006


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
        cache: Cache | None = None,
    ) -> None:
        self._sources = sources
        self._products = product_repo
        self._prices = price_repo
        self._cache = cache

    async def search(
        self, keyword: str, options: SearchOptions | None = None
    ) -> SearchResponse:
        options = options or SearchOptions()
        metrics.inc("mydealfinder_searches_total")

        cache_key = self._cache_key(keyword, options)
        if self._cache is not None:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                metrics.inc("mydealfinder_cache_hits_total")
                return SearchResponse.model_validate_json(cached)
            metrics.inc("mydealfinder_cache_misses_total")

        response = await self._run_search(keyword, options)

        if self._cache is not None:
            await self._cache.set(cache_key, response.model_dump_json())
        return response

    @staticmethod
    def _cache_key(keyword: str, options: SearchOptions) -> str:
        # Include the flags that change the output so the key stays correct.
        settings = get_settings()
        return make_key(
            "search",
            {
                "q": keyword.strip().lower(),
                "options": vars(options),
                "true_price": settings.true_price,
                "sources": settings.enabled_source_list,
            },
        )

    async def _run_search(self, keyword: str, options: SearchOptions) -> SearchResponse:
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
            summaries.append(
                await self._summarize(product, options.in_stock_only, options.currency)
            )

        filtered = self._apply_filters(summaries, options)
        self._sort(filtered, options.sort)

        total = len(filtered)
        page = self._paginate(filtered, options)

        return SearchResponse(
            query=keyword,
            count=total,
            page=options.page,
            page_size=options.page_size,
            results=page,
        )

    @staticmethod
    def _apply_filters(
        summaries: list[ProductSummary], options: SearchOptions
    ) -> list[ProductSummary]:
        """Filter aggregated products by category, brand, and price range."""
        def keep(s: ProductSummary) -> bool:
            if options.category and (s.category or "").lower() != options.category.lower():
                return False
            if options.brand and (s.brand or "").lower() != options.brand.lower():
                return False
            if options.min_price is not None and (s.best_price is None or s.best_price < options.min_price):
                return False
            if options.max_price is not None and (s.best_price is None or s.best_price > options.max_price):
                return False
            return True

        return [s for s in summaries if keep(s)]

    @staticmethod
    def _sort(summaries: list[ProductSummary], sort: str) -> None:
        """Order results in place (F005). Products without a price sink last."""
        if sort == "name":
            summaries.sort(key=lambda s: s.name.lower())
        elif sort == "price_desc":
            summaries.sort(key=lambda s: (s.best_price is None, -(s.best_price or 0.0)))
        else:  # price_asc (default)
            summaries.sort(key=lambda s: (s.best_price is None, s.best_price or 0.0))

    @staticmethod
    def _paginate(summaries: list[ProductSummary], options: SearchOptions) -> list[ProductSummary]:
        start = max(options.page - 1, 0) * options.page_size
        return summaries[start : start + options.page_size]

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
                shipping_cost=offer.shipping_cost,
                coupon_code=offer.coupon_code,
                coupon_savings=offer.coupon_savings,
            )
            # Every observation is recorded so the history grows over time.
            await self._prices.add_point(
                product_id=product.id,
                source=source_name,
                price=offer.price,
                currency=offer.currency,
            )
        return product

    async def _summarize(
        self, product: Product, in_stock_only: bool = True, currency: str | None = None
    ) -> ProductSummary:
        settings = get_settings()
        best = await self._products.best_offer(
            product.id, in_stock_only=in_stock_only, by_total=settings.true_price
        )
        count = await self._products.offer_count(product.id)

        best_price = None
        target_ccy = (currency or "USD").upper()
        if best is not None:
            raw = best.total_price if settings.true_price else best.price
            best_price = fx.convert(raw, best.currency, target_ccy)
        return ProductSummary(
            id=product.id,
            slug=product.slug,
            name=product.name,
            brand=product.brand,
            category=product.category,
            image_url=product.image_url,
            best_price=best_price,
            currency=target_ccy if best else None,
            offer_count=count,
        )
