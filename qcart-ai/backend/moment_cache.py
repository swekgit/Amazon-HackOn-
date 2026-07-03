"""In-memory cache for pre-generated moment carts.

Keyed by (customer_id, city, moment_id, time_bucket) so carts stay
personalized per user and refresh when the time-of-day bucket changes.

Same trade-offs as cache.py: single-process, TTL-based, not shared across
instances. At scale, swap for Redis with the same get/set/prewarm interface.
"""

from __future__ import annotations

import threading
import time

_TTL_SECONDS = 600
_store: dict[str, tuple[float, dict]] = {}
_prewarming: set[str] = set()


def _key(
    customer_id: str | None,
    city: str,
    moment_id: str,
    time_bucket: str,
) -> str:
    return f"{customer_id or 'anon'}:{city}:{moment_id}:{time_bucket}"


def get(
    customer_id: str | None,
    city: str,
    moment_id: str,
    time_bucket: str,
) -> dict | None:
    k = _key(customer_id, city, moment_id, time_bucket)
    hit = _store.get(k)
    if not hit:
        return None
    ts, value = hit
    if time.time() - ts > _TTL_SECONDS:
        _store.pop(k, None)
        return None
    return value


def set(
    customer_id: str | None,
    city: str,
    moment_id: str,
    time_bucket: str,
    value: dict,
) -> None:
    k = _key(customer_id, city, moment_id, time_bucket)
    _store[k] = (time.time(), value)


def prewarm_async(
    customer_id: str | None,
    city: str,
    time_bucket: str,
    moment_ids: list[str],
    generate_fn,
) -> None:
    """Background-pre-generate carts for the listed moments (skip if cached)."""

    def _run() -> None:
        for moment_id in moment_ids:
            warm_key = _key(customer_id, city, moment_id, time_bucket)
            if warm_key in _prewarming or get(customer_id, city, moment_id, time_bucket):
                continue
            _prewarming.add(warm_key)
            try:
                payload = generate_fn(moment_id)
                if payload:
                    set(customer_id, city, moment_id, time_bucket, payload)
            except Exception:
                pass
            finally:
                _prewarming.discard(warm_key)

    threading.Thread(target=_run, daemon=True).start()


def clear() -> None:
    _store.clear()
    _prewarming.clear()
