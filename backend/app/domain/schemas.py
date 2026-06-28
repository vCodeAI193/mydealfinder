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
    shipping_cost: float = 0.0  # F011
    total_price: float  # price + shipping (F011)
    currency: str
    in_stock: bool
    source_rating: float | None = None  # F014
    coupon_code: str | None = None  # F015
    coupon_savings: float = 0.0  # F015
    pinned: bool = False  # F013
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
    alert_type: Literal["absolute", "percentage", "restock"] = "absolute"
    threshold_price: float | None = Field(
        default=None, gt=0, description="Absolute target price (absolute alerts)."
    )
    threshold_pct: float | None = Field(
        default=None, gt=0, le=100, description="Percent drop from current price (percentage alerts)."
    )
    recurring: bool = False
    currency: str = Field(default="USD", min_length=3, max_length=3)
    # Delivery options.
    channel: Literal["email", "webhook"] = "email"  # F030
    webhook_url: str | None = None  # F030
    frequency: Literal["instant", "daily", "weekly"] = "instant"  # F031

    @model_validator(mode="after")
    def _check_threshold(self) -> "AlertCreate":
        if self.alert_type == "absolute" and self.threshold_price is None:
            raise ValueError("threshold_price is required for absolute alerts")
        if self.alert_type == "percentage" and self.threshold_pct is None:
            raise ValueError("threshold_pct is required for percentage alerts")
        if self.channel == "webhook" and not self.webhook_url:
            raise ValueError("webhook_url is required for the webhook channel")
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
    channel: str
    webhook_url: str | None = None
    frequency: str
    created_at: datetime
    triggered_at: datetime | None = None
    triggered_price: float | None = None
    notified_at: datetime | None = None


class AlertSuggestion(BaseModel):
    """A suggested alert threshold derived from price history (F034)."""

    product_id: int
    current_price: float | None = None
    avg_price: float | None = None
    suggested_threshold: float | None = None
    window_days: int | None = None


# ── Accounts (F035–F040) ────────────────────────────────────────────────────


class UserCredentials(BaseModel):
    """Registration / login request body."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserPreferences(BaseModel):
    """A user's configurable defaults (F038–F040)."""

    model_config = ConfigDict(from_attributes=True)

    default_currency: str = Field(default="USD", min_length=3, max_length=3)
    default_sort: str = "price_asc"
    language: str = Field(default="en", min_length=2, max_length=8)


class PreferencesUpdate(BaseModel):
    """Partial preferences update; omitted fields are left unchanged."""

    default_currency: str | None = Field(default=None, min_length=3, max_length=3)
    default_sort: str | None = None
    language: str | None = Field(default=None, min_length=2, max_length=8)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime
    default_currency: str
    default_sort: str
    language: str
    is_admin: bool = False


class AuthResponse(BaseModel):
    """Returned on register/login: the bearer token plus the user."""

    token: str
    user: UserOut


class WatchlistItemOut(BaseModel):
    """A saved product with its current best price (F037)."""

    product_id: int
    slug: str
    name: str
    image_url: str | None = None
    best_price: float | None = None
    currency: str | None = None
    added_at: datetime


class WatchlistAdd(BaseModel):
    product_id: int


# ── Admin (F079–F081) ───────────────────────────────────────────────────────


class AuditEntry(BaseModel):
    id: int
    created_at: datetime
    actor: str
    action: str
    detail: str | None = None


class AdminOverview(BaseModel):
    """Aggregate stats for the admin dashboard (F079)."""

    products: int
    offers: int
    alerts_active: int
    users: int
    sources: list[dict]
    recent_audit: list[AuditEntry]


class FlagUpdate(BaseModel):
    name: str
    value: bool


class AlertCheckResult(BaseModel):
    """Outcome of evaluating outstanding alerts."""

    checked: int
    triggered: list[AlertOut]


class DigestResult(BaseModel):
    """Outcome of sending a batched digest (F031)."""

    frequency: str
    recipients: int
    notifications: int
