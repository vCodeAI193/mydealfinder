"""A tiny, dependency-free in-process metrics registry (F083).

Renders the Prometheus text exposition format. Good enough to scrape counters
for an MVP without pulling in prometheus_client.
"""
import threading

_lock = threading.Lock()
_counters: dict[str, float] = {}
_gauges: dict[str, float] = {}

# Registered metric help text (name -> description).
_HELP: dict[str, str] = {
    "mydealfinder_searches_total": "Total product searches served.",
    "mydealfinder_alert_checks_total": "Total alert-evaluation passes.",
    "mydealfinder_alerts_triggered_total": "Total alerts triggered.",
    "mydealfinder_price_refreshes_total": "Total scheduled price refreshes.",
    "mydealfinder_scheduler_runs_total": "Total background scheduler job runs.",
    "mydealfinder_cache_hits_total": "Total search cache hits.",
    "mydealfinder_cache_misses_total": "Total search cache misses.",
}


def inc(name: str, amount: float = 1.0) -> None:
    with _lock:
        _counters[name] = _counters.get(name, 0.0) + amount


def set_gauge(name: str, value: float) -> None:
    with _lock:
        _gauges[name] = value


def reset() -> None:
    """Clear all metrics (used in tests)."""
    with _lock:
        _counters.clear()
        _gauges.clear()


def render() -> str:
    """Return the registry as Prometheus text exposition format."""
    lines: list[str] = []
    with _lock:
        for name, value in sorted(_counters.items()):
            if name in _HELP:
                lines.append(f"# HELP {name} {_HELP[name]}")
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")
        for name, value in sorted(_gauges.items()):
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
    return "\n".join(lines) + "\n"
