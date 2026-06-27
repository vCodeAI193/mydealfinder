"""Watchlist business logic (F037)."""
from app.domain.schemas import WatchlistItemOut
from app.repositories.product_repository import ProductRepository
from app.repositories.watchlist_repository import WatchlistRepository
from app.services import currency as fx
from app.services.price_service import ProductNotFoundError


class WatchlistService:
    def __init__(self, watchlist_repo: WatchlistRepository, product_repo: ProductRepository) -> None:
        self._watchlist = watchlist_repo
        self._products = product_repo

    async def list_items(self, user_id: int, currency: str | None = None) -> list[WatchlistItemOut]:
        items = await self._watchlist.list_for_user(user_id)
        target = (currency or "USD").upper()
        out: list[WatchlistItemOut] = []
        for item in items:
            best = await self._products.best_offer(item.product_id)
            out.append(
                WatchlistItemOut(
                    product_id=item.product_id,
                    slug=item.product.slug,
                    name=item.product.name,
                    image_url=item.product.image_url,
                    best_price=fx.convert(best.price, best.currency, target) if best else None,
                    currency=target if best else None,
                    added_at=item.created_at,
                )
            )
        return out

    async def add(self, user_id: int, product_id: int) -> None:
        if await self._products.get_with_offers(product_id) is None:
            raise ProductNotFoundError(f"Product {product_id} not found")
        await self._watchlist.add(user_id, product_id)

    async def remove(self, user_id: int, product_id: int) -> bool:
        return await self._watchlist.remove(user_id, product_id)
