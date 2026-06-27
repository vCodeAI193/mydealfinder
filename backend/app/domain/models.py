"""SQLAlchemy ORM models — the persistence representation of the domain."""
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Product(Base):
    """A logical product that may be sold by many sources."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Stable identity key used to de-duplicate the same product across searches/sources.
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    offers: Mapped[list["Offer"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    price_points: Mapped[list["PricePoint"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class Offer(Base):
    """The *current* price of a product at a single source."""

    __tablename__ = "offers"
    __table_args__ = (UniqueConstraint("product_id", "source", name="uq_offer_product_source"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(100), index=True)
    url: Mapped[str] = mapped_column(String(1024))
    price: Mapped[float] = mapped_column(Float)
    shipping_cost: Mapped[float] = mapped_column(Float, default=0.0)  # F011
    coupon_code: Mapped[str | None] = mapped_column(String(40), nullable=True)  # F015
    coupon_savings: Mapped[float] = mapped_column(Float, default=0.0)  # F015
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    product: Mapped[Product] = relationship(back_populates="offers")

    @property
    def total_price(self) -> float:
        """The shipping-inclusive 'true price' used for ranking (F011)."""
        return round(self.price + (self.shipping_cost or 0.0), 2)


class PricePoint(Base):
    """A historical observation of a product's price at a source."""

    __tablename__ = "price_points"
    __table_args__ = (
        Index("ix_pricepoint_product_recorded", "product_id", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(100), index=True)
    price: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    product: Mapped[Product] = relationship(back_populates="price_points")


class Alert(Base):
    """A user's request to be notified when a product price drops.

    Supports absolute thresholds and percentage drops (F026), a snooze/pause
    state (F032), and recurring re-arming (F033). The lifecycle is captured by
    ``status`` (active | paused | triggered) plus ``armed``: a recurring alert
    stays ``active`` but ``armed=False`` after firing until the price rises back
    above its threshold, preventing repeated notifications.
    """

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    email: Mapped[str] = mapped_column(String(320), index=True)

    # "absolute" → threshold_price; "percentage" → drop of threshold_pct from reference_price.
    alert_type: Mapped[str] = mapped_column(String(16), default="absolute")
    threshold_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    threshold_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    reference_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")

    recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(16), default="active", index=True)
    armed: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    triggered_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    product: Mapped[Product] = relationship(back_populates="alerts")

    @property
    def active(self) -> bool:
        """Back-compat convenience: whether the alert is still being evaluated."""
        return self.status == "active"

    @property
    def effective_threshold(self) -> float | None:
        """The absolute price at or below which this alert fires."""
        if self.alert_type == "percentage":
            if self.reference_price is None or self.threshold_pct is None:
                return None
            return round(self.reference_price * (1 - self.threshold_pct / 100), 2)
        return self.threshold_price
