"""Product detail, comparison, and price-history endpoints."""
import csv
import io

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.api.deps import PriceServiceDep
from app.domain.schemas import (
    OfferOut,
    PriceAnalytics,
    PriceHistoryOut,
    ProductDetail,
)
from app.services.price_service import ProductNotFoundError

router = APIRouter(prefix="/products", tags=["products"])

# Allowed history windows in days (F017). None/0 means "all history".
HistoryDays = Query(
    None, ge=0, le=3650, description="Limit history to the last N days (0/empty = all)"
)


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
async def get_history(
    product_id: int, service: PriceServiceDep, days: int | None = HistoryDays
) -> PriceHistoryOut:
    try:
        return await service.get_price_history(product_id, days=days)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/{product_id}/analytics",
    response_model=PriceAnalytics,
    summary="Price statistics & deal score over the history window",
)
async def get_analytics(
    product_id: int, service: PriceServiceDep, days: int | None = HistoryDays
) -> PriceAnalytics:
    try:
        return await service.get_analytics(product_id, days=days)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/{product_id}/history/export",
    summary="Export the price history as CSV or JSON (F023)",
)
async def export_history(
    product_id: int,
    service: PriceServiceDep,
    days: int | None = HistoryDays,
    format: str = Query("csv", pattern="^(csv|json)$", description="csv or json"),
):
    try:
        history = await service.get_price_history(product_id, days=days)
    except ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    filename = f"price-history-{product_id}.{format}"
    if format == "json":
        return StreamingResponse(
            io.BytesIO(history.model_dump_json().encode()),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["recorded_at", "source", "price", "currency"])
    for p in history.points:
        writer.writerow([p.recorded_at.isoformat(), p.source, p.price, p.currency])
    return StreamingResponse(
        io.BytesIO(buffer.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
