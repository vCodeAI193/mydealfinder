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
    # F085/F086: search-result cache time-to-live in seconds (0 disables caching).
    cache_ttl_seconds: int = 60

    # F082: Python logging level (DEBUG/INFO/WARNING/ERROR).
    log_level: str = "INFO"
    # F083: expose a Prometheus /metrics endpoint.
    enable_metrics: bool = True

    # F084/F046: in-process background scheduler. Disabled by default so tests
    # and one-off runs do not spawn loops; intervals of 0 disable a given job.
    scheduler_enabled: bool = False
    refresh_interval_seconds: int = 0  # F046: re-query sources for known products
    alert_check_interval_seconds: int = 0  # F084: evaluate alerts on a cadence

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
    # F036: allow using the app without an account.
    allow_guest: bool = True
    # F042: allow users to export all their data.
    enable_data_export: bool = True
    # F043: allow users to delete their own account.
    enable_account_deletion: bool = True

    # F028: SMTP email delivery. When smtp_host is unset, alerts are logged.
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "alerts@mydealfinder.local"
    smtp_use_tls: bool = True

    @property
    def email_enabled(self) -> bool:
        return bool(self.smtp_host)

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
            "allow_guest": self.allow_guest,
            "enable_data_export": self.enable_data_export,
            "enable_account_deletion": self.enable_account_deletion,
        }


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
