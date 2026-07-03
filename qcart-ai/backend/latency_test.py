#!/usr/bin/env python3
"""Measure API endpoint latency against a running QCart AI server.

Usage (server must be up on localhost:8000):
    cd qcart-ai/backend
    python latency_test.py

Does not modify application code — HTTP client only.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "http://localhost:8000"
DEFAULT_CITY = "Bangalore"
DEFAULT_CUSTOMER = "cust_ananya"
FORYOU_CUSTOMERS = ("cust_ananya", "cust_ravi", "cust_meera")
REQUEST_TIMEOUT_S = 180


def _request(method: str, path: str, *, params: dict | None = None, body: dict | None = None) -> tuple[int, float, dict | list | str | None, str | None]:
    """Return (status_code, elapsed_ms, parsed_json_or_none, raw_error)."""
    url = BASE_URL + path
    if params:
        url += "?" + urllib.parse.urlencode(params)

    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_S) as resp:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            raw = resp.read().decode("utf-8")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = raw
            return resp.status, elapsed_ms, payload, None
    except urllib.error.HTTPError as exc:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = raw
        return exc.code, elapsed_ms, payload, None
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - t0) * 1000
        return 0, elapsed_ms, None, str(exc)


def _print_call(label: str, status: int, elapsed_ms: float, detail: str = "") -> None:
    line = f"  {label}: {elapsed_ms:.1f} ms  HTTP {status}"
    if detail:
        line += f"  |  {detail}"
    print(line)


def _cart_detail(payload: dict | None) -> str:
    if not isinstance(payload, dict):
        return "invalid response"
    cart = payload.get("cart") or []
    names = [item.get("name", "?") for item in cart]
    cached = payload.get("cached", False)
    recipe = payload.get("recipe") or {}
    recipe_flag = " recipe" if recipe.get("is_recipe") else ""
    return f"{len(cart)} items [{', '.join(names)}] cached={cached}{recipe_flag}"


def _foryou_detail(payload: dict | None) -> str:
    if not isinstance(payload, dict):
        return "invalid response"
    rec = payload.get("recommended") or []
    deals = payload.get("deals") or []
    tags = payload.get("tags") or []
    reasons = [r.get("reason", "") for r in rec if r.get("reason")]
    pitches = [d.get("pitch", "") for d in deals if d.get("pitch")]
    personalized = bool(reasons or pitches)
    top_rec = rec[0].get("name") if rec else "—"
    return (
        f"tags={len(tags)} rec={len(rec)} deals={len(deals)} "
        f"personalized_reasons={personalized} top_rec={top_rec!r}"
    )


def _moments_detail(payload: dict | None) -> str:
    if not isinstance(payload, dict):
        return "invalid response"
    moments = payload.get("moments") or []
    labels = [m.get("label", "?") for m in moments[:3]]
    cached_count = sum(1 for m in moments if m.get("cached"))
    return f"{len(moments)} moments (cached={cached_count}) first=[{', '.join(labels)}]"


def _verdict(endpoint_key: str, cold_ms: float | None, warm_ms: float | None, status: int) -> str:
    if status and status >= 400:
        return "ERROR"
    ms = warm_ms if warm_ms is not None else cold_ms
    if ms is None:
        return "—"
    if endpoint_key in ("cities", "trending", "predicted", "moments"):
        return "SLOW" if ms > 300 else "OK"
    if endpoint_key.startswith("foryou"):
        check = warm_ms if warm_ms is not None else cold_ms
        return "SLOW" if check and check > 2000 else "OK"
    if endpoint_key.startswith("cart"):
        check = warm_ms if warm_ms is not None else cold_ms
        return "SLOW" if check and check > 4000 else "OK"
    return "OK"


def _run_pair(
    summary: list[dict],
    endpoint_key: str,
    label: str,
    method: str,
    path: str,
    *,
    params: dict | None = None,
    body: dict | None = None,
    detail_fn=None,
) -> None:
    print(f"\n{label}")
    status_c, ms_c, payload_c, err_c = _request(method, path, params=params, body=body)
    if err_c:
        _print_call("cold", status_c, ms_c, err_c)
        summary.append({
            "endpoint": label,
            "cold_ms": ms_c,
            "warm_ms": None,
            "status": status_c,
            "verdict": "ERROR",
        })
        return

    detail_c = detail_fn(payload_c) if detail_fn else ""
    _print_call("cold", status_c, ms_c, detail_c)

    status_w, ms_w, payload_w, err_w = _request(method, path, params=params, body=body)
    if err_w:
        _print_call("warm", status_w, ms_w, err_w)
        summary.append({
            "endpoint": label,
            "cold_ms": ms_c,
            "warm_ms": None,
            "status": status_w or status_c,
            "verdict": "ERROR",
        })
        return

    detail_w = detail_fn(payload_w) if detail_fn else ""
    _print_call("warm", status_w, ms_w, detail_w)

    summary.append({
        "endpoint": label,
        "cold_ms": ms_c,
        "warm_ms": ms_w,
        "status": status_w,
        "verdict": _verdict(endpoint_key, ms_c, ms_w, status_w),
    })


def _run_single(
    summary: list[dict],
    endpoint_key: str,
    label: str,
    method: str,
    path: str,
    *,
    params: dict | None = None,
    body: dict | None = None,
    detail_fn=None,
) -> None:
    print(f"\n{label}")
    status, ms, payload, err = _request(method, path, params=params, body=body)
    detail = err or (detail_fn(payload) if detail_fn else "")
    _print_call("call", status, ms, detail)
    summary.append({
        "endpoint": label,
        "cold_ms": ms,
        "warm_ms": None,
        "status": status,
        "verdict": _verdict(endpoint_key, ms, None, status),
    })


def main() -> int:
    print(f"QCart AI latency test → {BASE_URL}")
    print("=" * 72)

    # Health check
    status, ms, payload, err = _request("GET", "/api/health")
    if err or status != 200:
        print(f"ERROR: server not reachable ({err or status})")
        return 1
    print(f"Health OK ({ms:.0f} ms) catalog_size={payload.get('catalog_size') if isinstance(payload, dict) else '?'}")

    summary: list[dict] = []

    _run_single(
        summary, "cities", "GET /api/cities",
        "GET", "/api/cities",
        detail_fn=lambda p: f"{len(p.get('cities', []))} cities" if isinstance(p, dict) else "",
    )

    _run_single(
        summary, "trending", "GET /api/trending?city=Bangalore",
        "GET", "/api/trending",
        params={"city": DEFAULT_CITY},
        detail_fn=lambda p: f"{len(p.get('products', []))} products" if isinstance(p, dict) else "",
    )

    _run_single(
        summary, "predicted", f"GET /api/predicted?customer_id={DEFAULT_CUSTOMER}",
        "GET", "/api/predicted",
        params={"customer_id": DEFAULT_CUSTOMER},
        detail_fn=lambda p: f"{len(p.get('predictions', []))} predictions" if isinstance(p, dict) else "",
    )

    for customer_id in FORYOU_CUSTOMERS:
        _run_pair(
            summary,
            f"foryou_{customer_id}",
            f"GET /api/foryou?customer_id={customer_id}&city={DEFAULT_CITY}",
            "GET",
            "/api/foryou",
            params={"customer_id": customer_id, "city": DEFAULT_CITY},
            detail_fn=_foryou_detail,
        )

    _run_pair(
        summary,
        "moments",
        f"GET /api/moments?pool=missions&customer_id={DEFAULT_CUSTOMER}&city={DEFAULT_CITY}",
        "GET",
        "/api/moments",
        params={"pool": "missions", "customer_id": DEFAULT_CUSTOMER, "city": DEFAULT_CITY},
        detail_fn=_moments_detail,
    )

    cart_cases = [
        ("cart_chips", "chips"),
        ("cart_movie_night", "movie night"),
        ("cart_recipe", "gajar ka halwa"),
    ]
    for key, message in cart_cases:
        body = {
            "message": message,
            "cart": [],
            "customer_id": DEFAULT_CUSTOMER,
            "city": DEFAULT_CITY,
        }
        _run_pair(
            summary,
            key,
            f'POST /api/cart message="{message}"',
            "POST",
            "/api/cart",
            body=body,
            detail_fn=_cart_detail,
        )

    print("\n" + "=" * 72)
    print("SUMMARY")
    print(f"{'endpoint':<58} {'cold ms':>8} {'warm ms':>8} {'st':>4} {'verdict':>8}")
    print("-" * 92)
    for row in summary:
        cold = f"{row['cold_ms']:.0f}" if row["cold_ms"] is not None else "—"
        warm = f"{row['warm_ms']:.0f}" if row["warm_ms"] is not None else "—"
        print(
            f"{row['endpoint']:<58} {cold:>8} {warm:>8} "
            f"{row['status']:>4} {row['verdict']:>8}"
        )

    slow = [r for r in summary if r["verdict"] == "SLOW"]
    if slow:
        print(f"\n{len(slow)} endpoint(s) exceeded threshold.")
    else:
        print("\nAll endpoints within thresholds.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
