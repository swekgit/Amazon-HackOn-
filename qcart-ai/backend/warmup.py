"""Demo warmup script — pre-fills response cache before presentation.

Usage:
    1. Start the backend: uvicorn main:app --port 8000
    2. Run: python warmup.py

This calls POST /api/cart for each demo scenario, then uses the returned
cart to warm refinement commands. Results are cached so the live demo
responds instantly.
"""

import sys
import time

import httpx

BASE_URL = "http://localhost:8000"
TIMEOUT = 60  # seconds per request (reasoning model can be slow)

SCENARIOS = [
    "movie night for 4",
    "party for 6",
    "weekly groceries",
    "baby care essentials",
    "I have fever",
    "late night snacks",
]

REFINEMENTS = [
    "make it premium",
    "make it cheaper",
    "remove dairy",
]


def call_cart(message: str, cart: list = None) -> dict | None:
    """POST /api/cart and return the response payload, or None on failure."""
    payload = {"message": message, "cart": cart or []}
    try:
        resp = httpx.post(
            f"{BASE_URL}/api/cart",
            json=payload,
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            print(f"  HTTP {resp.status_code}: {resp.text[:100]}")
            return None
    except httpx.TimeoutException:
        print(f"  TIMEOUT after {TIMEOUT}s")
        return None
    except httpx.ConnectError:
        print(f"  CONNECTION REFUSED — is the server running on {BASE_URL}?")
        return None


def main():
    print("=" * 60)
    print("QCart AI Demo Warmup")
    print("=" * 60)

    # Check server health
    try:
        health = httpx.get(f"{BASE_URL}/api/health", timeout=5)
        if health.status_code != 200:
            print(f"Server unhealthy: {health.status_code}")
            sys.exit(1)
        info = health.json()
        print(f"Server OK — catalog: {info['catalog_size']} products, model: {info['model']}")
    except (httpx.ConnectError, httpx.TimeoutException):
        print(f"Cannot reach server at {BASE_URL}. Start it first:")
        print(f"  cd backend && uvicorn main:app --port 8000")
        sys.exit(1)

    print()
    passed = 0
    failed = 0
    start = time.time()

    # Phase 1: Warm scenarios
    print("Phase 1: Warming demo scenarios...")
    scenario_carts = {}

    for scenario in SCENARIOS:
        print(f"\n  [{scenario}] ", end="", flush=True)
        result = call_cart(scenario)
        if result:
            cart_items = result.get("cart", [])
            scenario_carts[scenario] = cart_items
            subtotal = result.get("subtotal", 0)
            print(f"OK — {len(cart_items)} items, subtotal=₹{subtotal}, context={result.get('context')}")
            passed += 1
        else:
            failed += 1
            print("FAILED")

    # Phase 2: Warm refinements using first scenario's cart
    print("\n\nPhase 2: Warming refinement commands...")

    # Use movie night cart for refinements (most visible demo)
    base_cart = scenario_carts.get("movie night for 4", [])
    if not base_cart:
        # Fallback: use any available cart
        for cart in scenario_carts.values():
            if cart:
                base_cart = cart
                break

    if not base_cart:
        print("  No base cart available — skipping refinements")
    else:
        for refinement in REFINEMENTS:
            print(f"\n  [{refinement}] ", end="", flush=True)
            result = call_cart(refinement, base_cart)
            if result:
                cart_items = result.get("cart", [])
                subtotal = result.get("subtotal", 0)
                print(f"OK — {len(cart_items)} items, subtotal=₹{subtotal}")
                passed += 1
            else:
                failed += 1
                print("FAILED")

    # Summary
    elapsed = time.time() - start
    print("\n" + "=" * 60)
    print(f"WARMUP COMPLETE in {elapsed:.1f}s")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print("=" * 60)

    if failed > 0:
        print("\nSome scenarios failed. Demo may be slow for those cases.")
        sys.exit(1)
    else:
        print("\nAll scenarios cached. Demo will be instant!")


if __name__ == "__main__":
    main()
