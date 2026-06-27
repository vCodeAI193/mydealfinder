"""Search endpoint."""
from fastapi import APIRouter, Query

from app.api.deps import SearchServiceDep
from app.domain.schemas import SearchResponse

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResponse, summary="Search products by keyword")
async def search(
    service: SearchServiceDep,
    q: str = Query(..., min_length=1, description="Search keyword, e.g. 'headphones'"),
) -> SearchResponse:
    """Aggregate offers from all sources for `q` and return products sorted by best price."""
    return await service.search(q)
