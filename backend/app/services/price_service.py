"""Product detail, comparison, and price-history business logic."""
from datetime import datetime, timedelta, timezone

from app.domain.models import PricePoint
from app.domain.schemas import (
    OfferOut,
    PriceAnalytics,
    PriceHistoryOut,
    PricePointOut,
    ProductDetail,
)
from app.repositories.price_repository import PriceRepository
from app.repositories.product_repository import ProductRepository


class ProductNotFoundError(Exception):
    """Raised when a requested product does not exist."""


def _window_start(days: int | None) -> datetime | None:
    """Translate a "last N days" window into an absolute cutoff."""
    if not days or days <= 0:
        return None
    return datetime.now(timezone.utc) - timedelta(days=days)


class PriceService:
    def __init__(self, product_repo: ProductRepository, price_repo: PriceRepository) -> None:
        self._products = product_repo
        self._prices = price_repo

    async def get_product_detail(self, product_id: int) -> ProductDetail:
        """Return a product with every current offer, cheapest first."""
        product = await self._products.get_with_offers(product_id)
        if product is None:
            raise ProductNotFoundError(f"Product {product_id} not found")

        offers = sorted(product.offers, key=lambda o: o.price)
        best = offers[0] if offers else None
        return ProductDetail(
            id=product.id,
            slug=product.slug,
            name=product.name,
            brand=product.brand,
            category=product.category,
            image_url=product.image_url,
            description=product.description,
            best_price=best.price if best else None,
            currency=best.currency if best else None,
            offer_count=len(offers),
            offers=[OfferOut.model_validate(o) for o in offers],
        )

    async def get_price_history(
        self, product_id: int, days: int | None = None
    ) -> PriceHistoryOut:
        """Return the price-history time series, optionally limited to the last
        `days` days (F017)."""
        points = await self._load_history(product_id, days)
        return PriceHistoryOut(
            product_id=product_id,
            window_days=days,
            points=[PricePointOut.model_validate(p) for p in points],
        )

    async def get_analytics(self, product_id: int, days: int | None = None) -> PriceAnalytics:
        """Compute summary statistics and a deal score over the price history.

        Uses the best (minimum) price observed per day so multi-source noise
        does not skew the stats. The deal score is 100 when the current best
        price sits at the window's historical low and 0 at its high (F020),
        and `pct_vs_avg` is the current price relative to the window average
        (F021)."""
        points = await self._load_history(product_id, days)
        currency = points[-1].currency if points else None

        # Best price per day → the comparison series.
        daily_best: dict[str, float] = {}
        for p in points:
            day = p.recorded_at.date().isoformat()
            daily_best[day] = min(p.price, daily_best.get(day, p.price))
        prices = list(daily_best.values())

        # Current best price comes from the live offers, not just history.
        best_offer = await self._products.best_offer(product_id)
        current = best_offer.price if best_offer else (prices[-1] if prices else None)
        if best_offer is not None:
            currency = best_offer.currency

        if not prices:
            return PriceAnalytics(
                product_id=product_id, window_days=days, sample_size=0, currency=currency,
                current_price=current,
            )

        low, high = min(prices), max(prices)
        avg = sum(prices) / len(prices)
        ref = current if current is not None else prices[-1]

        pct_vs_avg = round((ref - avg) / avg * 100, 1) if avg else 0.0
        if high == low:
            deal_score = 100 if ref <= low else 50
        else:
            # Clamp to [0, 100] since the current price can dip below the
            # historical low captured in the window.
            raw = (high - ref) / (high - low) * 100
            deal_score = int(round(max(0.0, min(100.0, raw))))

        return PriceAnalytics(
            product_id=product_id,
            window_days=days,
            sample_size=len(prices),
            currency=currency,
            current_price=round(ref, 2),
            min_price=round(low, 2),
            max_price=round(high, 2),
            avg_price=round(avg, 2),
            pct_vs_avg=pct_vs_avg,
            deal_score=deal_score,
        )

    async def _load_history(self, product_id: int, days: int | None) -> list[PricePoint]:
        """Validate the product exists and return its (optionally windowed) history."""
        product = await self._products.get_with_offers(product_id)
        if product is None:
            raise ProductNotFoundError(f"Product {product_id} not found")
        return await self._prices.history_for_product(product_id, since=_window_start(days))
