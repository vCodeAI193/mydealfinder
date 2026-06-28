"""In-process per-source health tracking (F049).

Records the last success/error and counts for each source so an operator can see
which data sources are healthy. In-memory and per-process — good enough for the
MVP; a multi-worker deployment would back this with Redis.
"""
import threading
from datetime import datetime, timezone

_lock = threading.Lock()
_health: dict[str, dict] = {}


def _entry(name: str) -> dict:
    return _health.setdefault(
        name,
        {
            "source": name,
            "ok_count": 0,
            "error_count": 0,
            "last_ok": None,
            "last_error": None,
            "last_error_message": None,
            "status": "unknown",
        },
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_ok(name: str, result_count: int) -> None:
    with _lock:
        e = _entry(name)
        e["ok_count"] += 1
        e["last_ok"] = _now()
        e["last_result_count"] = result_count
        e["status"] = "ok"


def record_error(name: str, message: str) -> None:
    with _lock:
        e = _entry(name)
        e["error_count"] += 1
        e["last_error"] = _now()
        e["last_error_message"] = message
        e["status"] = "error"


def snapshot() -> list[dict]:
    with _lock:
        return [dict(v) for v in _health.values()]


def reset() -> None:
    with _lock:
        _health.clear()
