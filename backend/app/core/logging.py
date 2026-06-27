"""Application logging configuration (F082)."""
import logging

from app.core.config import get_settings

_CONFIGURED = False


def setup_logging() -> None:
    """Configure the root logger from the LOG_LEVEL setting (idempotent)."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    level = getattr(logging, get_settings().log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
