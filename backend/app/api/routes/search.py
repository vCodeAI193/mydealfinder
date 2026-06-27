"""Search endpoint."""
from fastapi import APIRouter, Query

from app.api.deps import SearchServiceDep
from app.domain.schemas import SearchResponse
from app.services.search_service import SORT_OPTIONS, SearchOptions

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResponse, summary="Search products by keyword")
async def search(
    service: SearchServiceDep,
    q: str = Query(..., min_length=1, description="Search keyword, e.g. 'headphones'"),
    category: str | None = Query(None, description="Filter by category (F003)"),
    brand: str | None = Query(None, description="Filter by brand (F003)"),
    min_price: float | None = Query(None, ge=0, description="Minimum best price (F004)"),
    max_price: float | None = Query(None, ge=0, description="Maximum best price (F004)"),
    sort: str = Query("price_asc", description=f"Sort order (F005): one of {', '.join(SORT_OPTIONS)}"),
    in_stock_only: bool = Query(True, description="Exclude out-of-stock offers (F010)"),
    page: int = Query(1, ge=1, description="Page number (F006)"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page (F006)"),
) -> SearchResponse:
    """Aggregate offers from all sources for `q` and return products, filtered,
    sorted, and paginated according to the optional query parameters."""
    options = SearchOptions(
        category=category,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        sort=sort if sort in SORT_OPTIONS else "price_asc",
        in_stock_only=in_stock_only,
        page=page,
        page_size=page_size,
    )
    return await service.search(q, options)
