"""Pydantic schemas — the API contract (request/response models)."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


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
    window_days: int | None = None  # None means "all history"
    points: list[PricePointOut]


class PriceAnalytics(BaseModel):
    """Derived statistics over a product's price history (F019–F021)."""

    product_id: int
    window_days: int | None = None
    sample_size: int
    currency: str | None = None
    current_price: float | None = None
    min_price: float | None = None
    max_price: float | None = None
    avg_price: float | None = None
    # Current price vs the window average, in percent (negative = below avg).
    pct_vs_avg: float | None = None  # F021
    # 0–100: 100 when the current price is at the historical low (F020).
    deal_score: int | None = None


class SearchResponse(BaseModel):
    query: str
    count: int  # total products matching the query (before pagination)
    page: int = 1
    page_size: int = 20
    results: list[ProductSummary]  # the current page of results


class AlertCreate(BaseModel):
    """Request body to register a price alert.

    Use `alert_type="absolute"` with `threshold_price`, or
    `alert_type="percentage"` with `threshold_pct` (the % drop from the price at
    creation time) — F026. Set `recurring=true` to re-fire on future drops (F033).
    """

    product_id: int
    email: EmailStr
    alert_type: Literal["absolute", "percentage"] = "absolute"
    threshold_price: float | None = Field(
        default=None, gt=0, description="Absolute target price (absolute alerts)."
    )
    threshold_pct: float | None = Field(
        default=None, gt=0, le=100, description="Percent drop from current price (percentage alerts)."
    )
    recurring: bool = False
    currency: str = Field(default="USD", min_length=3, max_length=3)

    @model_validator(mode="after")
    def _check_threshold(self) -> "AlertCreate":
        if self.alert_type == "absolute" and self.threshold_price is None:
            raise ValueError("threshold_price is required for absolute alerts")
        if self.alert_type == "percentage" and self.threshold_pct is None:
            raise ValueError("threshold_pct is required for percentage alerts")
        return self


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    email: EmailStr
    alert_type: str
    threshold_price: float | None = None
    threshold_pct: float | None = None
    reference_price: float | None = None
    effective_threshold: float | None = None
    currency: str
    recurring: bool
    status: str
    active: bool
    armed: bool
    created_at: datetime
    triggered_at: datetime | None = None
    triggered_price: float | None = None


class AlertSuggestion(BaseModel):
    """A suggested alert threshold derived from price history (F034)."""

    product_id: int
    current_price: float | None = None
    avg_price: float | None = None
    suggested_threshold: float | None = None
    window_days: int | None = None


class AlertCheckResult(BaseModel):
    """Outcome of evaluating outstanding alerts."""

    checked: int
    triggered: list[AlertOut]
