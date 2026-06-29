"""Database models for all new features."""
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Index, String, Text, UniqueConstraint, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── F002: Search Suggestions ────────────────────────────────────────────────
class SearchSuggestion(Base):
    __tablename__ = "search_suggestions"
    id: Mapped[int] = mapped_column(primary_key=True)
    prefix: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    suggestions: Mapped[str] = mapped_column(Text)  # JSON array stored as text
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ── F007: Saved Searches ───────────────────────────────────────────────────
class SavedSearch(Base):
    __tablename__ = "saved_searches"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    query: Mapped[str] = mapped_column(String(255))
    options_json: Mapped[str] = mapped_column(Text)  # Serialized search options
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ── F066: Shareable Links ──────────────────────────────────────────────────
class ShareLink(Base):
    __tablename__ = "share_links"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    share_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ── F068: Public Wishlists ─────────────────────────────────────────────────
class PublicWishlist(Base):
    __tablename__ = "public_wishlists"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    public_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ── F070-F071: Community Prices & Voting ──────────────────────────────────
class CommunityPriceSubmission(Base):
    __tablename__ = "community_price_submissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_email: Mapped[str] = mapped_column(String(320), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    source: Mapped[str] = mapped_column(String(100))
    price: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    image_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)  # pending/approved/rejected
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CommunityVote(Base):
    __tablename__ = "community_votes"
    __table_args__ = (UniqueConstraint("submission_id", "voter_email", name="uq_vote_voter"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("community_price_submissions.id", ondelete="CASCADE"))
    voter_email: Mapped[str] = mapped_column(String(320), index=True)
    vote_type: Mapped[str] = mapped_column(String(16))  # upvote/flag
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ── F072: API Keys ─────────────────────────────────────────────────────────
class ApiKey(Base):
    __tablename__ = "api_keys"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ── F090: Email Verification ──────────────────────────────────────────────
class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    alert_id: Mapped[int | None] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
