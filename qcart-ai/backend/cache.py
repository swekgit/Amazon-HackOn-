"""Tiny in-memory response cache.

Why: during a demo the same prompts get repeated ("movie night for 4"), and
re-hitting the model adds latency + cost. We key on (message + current cart state)
so an identical turn returns instantly. TTL keeps it from going stale.

For a single-process hackathon server this is plenty. At scale you'd swap the
dict for Redis with the same get/set interface.
"""

import hashlib
import json
import time

_TTL_SECONDS = 600          # 10 minutes
_store: dict[str, tuple[float, dict]] = {}


def _key(message: str, cart: list, signals: dict | None = None) -> str:
    # Cart identity = sorted (id, qty) pairs, so order doesn't change the key.
    signature = sorted((i.get("id"), i.get("quantity", 1)) for i in cart)
    personalization = None
    if signals:
        personalization = {
            "cid": signals.get("customer_id"),
            "seg": signals.get("segment"),
            "tags": sorted(signals.get("tags") or []),
            "city": signals.get("city"),
            "tb": signals.get("time_bucket"),
        }
    raw = json.dumps(
        {"m": message.strip().lower(), "c": signature, "p": personalization},
        sort_keys=True,
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def get(message: str, cart: list, signals: dict | None = None):
    k = _key(message, cart, signals)
    hit = _store.get(k)
    if not hit:
        return None
    ts, value = hit
    if time.time() - ts > _TTL_SECONDS:
        _store.pop(k, None)           # expired
        return None
    return value


def set(message: str, cart: list, value: dict, signals: dict | None = None):
    _store[_key(message, cart, signals)] = (time.time(), value)


def clear():
    _store.clear()
