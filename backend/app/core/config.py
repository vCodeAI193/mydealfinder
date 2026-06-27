"""Application configuration loaded from environment variables."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings.

    Values are read from environment variables (or a local .env file).
    Defaults are chosen so the app boots with zero configuration for local dev.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Project metadata
    app_name: str = "MyDealFinder"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database. Defaults to a local SQLite file; override with a Postgres DSN in prod.
    # e.g. postgresql+asyncpg://user:pass@db:5432/mydealfinder
    database_url: str = "sqlite+aiosqlite:///./mydealfinder.db"

    # Redis (optional). When unset, caching is silently disabled.
    redis_url: str | None = None

    # CORS origins allowed to call the API (comma-separated env var).
    cors_origins: str = "http://localhost:3000"

    # Seed the database with demo data on startup.
    seed_on_startup: bool = True

    # ── Feature flags (FF) ──────────────────────────────────────────────────
    # F001: tolerate small typos in search queries.
    fuzzy_search: bool = False
    # F045: which sources to query, comma-separated. Empty means "all".
    enabled_sources: str = "amazon,ebay,walmart"
    # F025: max open alerts per (email, product). 0 means unlimited.
    max_alerts_per_product: int = 0
    # F011: rank/compare offers by shipping-inclusive total price.
    true_price: bool = False
    # F014: surface per-source trust ratings.
    show_source_ratings: bool = False
    # F015: surface coupon/voucher codes on offers.
    show_coupons: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def enabled_source_list(self) -> list[str]:
        return [s.strip().lower() for s in self.enabled_sources.split(",") if s.strip()]

    @property
    def feature_flags(self) -> dict[str, object]:
        """Public feature-flag state, exposed via the /config endpoint."""
        return {
            "fuzzy_search": self.fuzzy_search,
            "enabled_sources": self.enabled_source_list,
            "true_price": self.true_price,
            "show_source_ratings": self.show_source_ratings,
            "show_coupons": self.show_coupons,
        }


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
