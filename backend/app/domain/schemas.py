"""Pydantic schemas — the API contract (request/response models)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OfferOut(BaseModel):
    """A single source's current price for a product."""

    model_config = ConfigDict(from_attributes=True)

    source: str
    url: str
    price: float
    currency: str
    in_stock: bool
    updated_at: datetime


class ProductSummary(BaseModel):
    """Compact product representation used in search results."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    brand: str | None = None
    category: str | None = None
    image_url: str | None = None
    best_price: float | None = None
    currency: str | None = None
    offer_count: int = 0


class ProductDetail(ProductSummary):
    """Full product detail including every current offer, cheapest first."""

    description: str | None = None
    offers: list[OfferOut] = Field(default_factory=list)


class PricePointOut(BaseModel):
    """One point on a product's price-history time series."""

    model_config = ConfigDict(from_attributes=True)

    source: str
    price: float
    currency: str
    recorded_at: datetime


class PriceHistoryOut(BaseModel):
    product_id: int
    points: list[PricePointOut]


class SearchResponse(BaseModel):
    query: str
    count: int  # total products matching the query (before pagination)
    page: int = 1
    page_size: int = 20
    results: list[ProductSummary]  # the current page of results


class AlertCreate(BaseModel):
    """Request body to register a price alert."""

    product_id: int
    email: EmailStr
    threshold_price: float = Field(gt=0, description="Notify when best price drops below this value.")
    currency: str = Field(default="USD", min_length=3, max_length=3)


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    email: EmailStr
    threshold_price: float
    currency: str
    active: bool
    created_at: datetime
    triggered_at: datetime | None = None
    triggered_price: float | None = None


class AlertCheckResult(BaseModel):
    """Outcome of evaluating outstanding alerts."""

    checked: int
    triggered: list[AlertOut]
