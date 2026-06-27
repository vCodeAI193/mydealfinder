"""Optional Redis-backed cache for search results (F085/F086).

Degrades gracefully to a no-op when Redis is not configured, the client library
is missing, or the server is unreachable — so the app never hard-depends on it.
"""
import hashlib
import json

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("cache")


def make_key(prefix: str, payload: dict) -> str:
    """Build a stable cache key from a JSON-serializable payload."""
    blob = json.dumps(payload, sort_keys=True, default=str)
    digest = hashlib.sha256(blob.encode()).hexdigest()[:24]
    return f"{prefix}:{digest}"


class Cache:
    """Thin async wrapper over redis. All methods are safe no-ops on failure."""

    def __init__(self, redis_url: str | None = None, ttl_seconds: int | None = None) -> None:
        settings = get_settings()
        self._url = redis_url if redis_url is not None else settings.redis_url
        self._ttl = ttl_seconds if ttl_seconds is not None else settings.cache_ttl_seconds
        self._client = None
        self._init_client()

    @property
    def enabled(self) -> bool:
        return self._client is not None and self._ttl > 0

    def _init_client(self) -> None:
        if not self._url:
            return
        try:
            import redis.asyncio as redis  # imported lazily so it's an optional dep

            self._client = redis.from_url(self._url, decode_responses=True)
        except Exception as exc:  # missing lib or bad URL
            logger.warning("Redis cache disabled: %s", exc)
            self._client = None

    async def get(self, key: str) -> str | None:
        if not self.enabled:
            return None
        try:
            return await self._client.get(key)
        except Exception as exc:
            logger.warning("Cache get failed: %s", exc)
            return None

    async def set(self, key: str, value: str) -> None:
        if not self.enabled:
            return
        try:
            await self._client.set(key, value, ex=self._ttl)
        except Exception as exc:
            logger.warning("Cache set failed: %s", exc)
