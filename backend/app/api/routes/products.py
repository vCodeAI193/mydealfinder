"""Product detail, comparison, and price-history endpoints."""
from fastapi import APIRouter, HTTPException

from app.api.deps import PriceServiceDep
from app.domain.schemas import OfferOut, PriceHistoryOut, ProductDetail
from app.services.price_service import ProductNotFoundError

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/{product_id}", response_model=ProductDetail, summary="Get a product with all offers")
async def get_product(product_id: int, service: PriceServiceDep) -> ProductDetail:
    try:
        return await service.get_product_detail(product_id)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/{product_id}/offers",
    response_model=list[OfferOut],
    summary="Compare prices across sources (cheapest first)",
)
async def get_offers(product_id: int, service: PriceServiceDep) -> list[OfferOut]:
    try:
        detail = await service.get_product_detail(product_id)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return detail.offers


@router.get(
    "/{product_id}/history",
    response_model=PriceHistoryOut,
    summary="Get the price history of a product",
)
async def get_history(product_id: int, service: PriceServiceDep) -> PriceHistoryOut:
    try:
        return await service.get_price_history(product_id)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
