"""Runtime feature-flag overrides (F080).

Toggling a flag here mutates the cached Settings singleton so the change takes
effect immediately for every reader (settings.<flag>), without a restart. The
override is process-local and reverts to the env value when the process
restarts — appropriate for an MVP admin toggle.
"""
from app.core.config import get_settings

# Boolean flags an admin may toggle at runtime.
TOGGLEABLE: tuple[str, ...] = (
    "fuzzy_search",
    "true_price",
    "show_source_ratings",
    "show_coupons",
    "allow_guest",
    "enable_data_export",
    "enable_account_deletion",
    "enable_metrics",
)


def current() -> dict[str, bool]:
    settings = get_settings()
    return {name: bool(getattr(settings, name)) for name in TOGGLEABLE}


def set_flag(name: str, value: bool) -> None:
    if name not in TOGGLEABLE:
        raise KeyError(name)
    setattr(get_settings(), name, value)
