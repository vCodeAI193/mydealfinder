"""Product detail, comparison, and price-history business logic."""
from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.domain.models import Offer, PricePoint
from app.domain.schemas import (
    AlertSuggestion,
    OfferOut,
    PriceAnalytics,
    PriceHistoryOut,
    PricePointOut,
    ProductDetail,
)
from app.repositories.price_repository import PriceRepository
from app.repositories.product_repository import ProductRepository
from app.services import currency as fx
from app.sources.metadata import rating_for


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

    async def get_product_detail(
        self,
        product_id: int,
        currency: str | None = None,
        pinned: list[str] | None = None,
    ) -> ProductDetail:
        """Return a product with every current offer.

        Offers are ordered with pinned sources first (F013), then by the
        ranking price — the shipping-inclusive total when the `true_price` flag
        is on (F011), otherwise the sticker price. Prices are converted to
        `currency` for display (F012), and ratings/coupons are attached when
        their flags are enabled (F014/F015)."""
        product = await self._products.get_with_offers(product_id)
        if product is None:
            raise ProductNotFoundError(f"Product {product_id} not found")

        settings = get_settings()
        pinned_set = {s.lower() for s in (pinned or [])}
        target_ccy = (currency or "USD").upper()

        out_offers = [
            self._build_offer(o, target_ccy, pinned_set, settings)
            for o in product.offers
        ]
        rank = (lambda o: o.total_price) if settings.true_price else (lambda o: o.price)
        # Pinned first (F013), then cheapest by the active ranking price.
        out_offers.sort(key=lambda o: (not o.pinned, rank(o)))

        # Best price is the cheapest by ranking, ignoring pinning.
        best = min(out_offers, key=rank) if out_offers else None
        return ProductDetail(
            id=product.id,
            slug=product.slug,
            name=product.name,
            brand=product.brand,
            category=product.category,
            image_url=product.image_url,
            description=product.description,
            best_price=rank(best) if best else None,
            currency=target_ccy if best else None,
            offer_count=len(out_offers),
            offers=out_offers,
        )

    @staticmethod
    def _build_offer(offer: Offer, target_ccy: str, pinned: set[str], settings) -> OfferOut:
        """Map an ORM offer to an OfferOut, applying conversion & display flags."""
        def conv(amount: float) -> float:
            return fx.convert(amount, offer.currency, target_ccy)

        return OfferOut(
            source=offer.source,
            url=offer.url,
            price=conv(offer.price),
            shipping_cost=conv(offer.shipping_cost or 0.0),
            total_price=conv(offer.total_price),
            currency=target_ccy,
            in_stock=offer.in_stock,
            source_rating=rating_for(offer.source) if settings.show_source_ratings else None,
            coupon_code=offer.coupon_code if settings.show_coupons else None,
            coupon_savings=conv(offer.coupon_savings or 0.0) if settings.show_coupons else 0.0,
            pinned=offer.source.lower() in pinned,
            updated_at=offer.updated_at,
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

    async def suggest_threshold(self, product_id: int, days: int | None = 30) -> AlertSuggestion:
        """Suggest a sensible alert threshold from recent prices (F034).

        Heuristic: aim a few percent below the lower of the current price and
        the window average — a realistic "good deal" target the price has a
        decent chance of hitting."""
        analytics = await self.get_analytics(product_id, days=days)
        candidates = [p for p in (analytics.current_price, analytics.avg_price) if p is not None]
        suggested = round(min(candidates) * 0.97, 2) if candidates else None
        return AlertSuggestion(
            product_id=product_id,
            current_price=analytics.current_price,
            avg_price=analytics.avg_price,
            suggested_threshold=suggested,
            window_days=days,
        )

    async def _load_history(self, product_id: int, days: int | None) -> list[PricePoint]:
        """Validate the product exists and return its (optionally windowed) history."""
        product = await self._products.get_with_offers(product_id)
        if product is None:
            raise ProductNotFoundError(f"Product {product_id} not found")
        return await self._prices.history_for_product(product_id, since=_window_start(days))
