"""Product detail, comparison, and price-history business logic."""
from app.domain.schemas import (
    OfferOut,
    PriceHistoryOut,
    PricePointOut,
    ProductDetail,
)
from app.repositories.price_repository import PriceRepository
from app.repositories.product_repository import ProductRepository


class ProductNotFoundError(Exception):
    """Raised when a requested product does not exist."""


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

    async def get_price_history(self, product_id: int) -> PriceHistoryOut:
        """Return the full price-history time series for a product."""
        product = await self._products.get_with_offers(product_id)
        if product is None:
            raise ProductNotFoundError(f"Product {product_id} not found")

        points = await self._prices.history_for_product(product_id)
        return PriceHistoryOut(
            product_id=product_id,
            points=[PricePointOut.model_validate(p) for p in points],
        )
