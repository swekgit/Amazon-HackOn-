"""Demo validation script — verifies all demo scenarios return correct responses.

Usage:
    1. Start the backend: uvicorn main:app --port 8000
    2. Run: python demo_validation.py

Validates HTTP 200, valid JSON structure, field correctness, cart integrity,
and gap engine output for each scenario.
"""

import sys
import time

import httpx

BASE_URL = "http://localhost:8000"
TIMEOUT = 60

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
    "for 6 people",
]

VALID_CONTEXTS = {"movie_night", "party", "health", "baby", "routine", "late_night", "other"}
VALID_URGENCY = {"high", "normal"}


def validate_response(label: str, resp: httpx.Response) -> list:
    """Validate a response and return list of failure reasons (empty = pass)."""
    failures = []

    # HTTP 200
    if resp.status_code != 200:
        failures.append(f"HTTP {resp.status_code} (expected 200): {resp.text[:100]}")
        return failures

    # Valid JSON
    try:
        data = resp.json()
    except Exception:
        failures.append("Response is not valid JSON")
        return failures

    # Context present and valid
    if "context" not in data:
        failures.append("Missing 'context' field")
    elif data["context"] not in VALID_CONTEXTS:
        failures.append(f"Invalid context: '{data['context']}' not in {VALID_CONTEXTS}")

    # Urgency present and valid
    if "urgency" not in data:
        failures.append("Missing 'urgency' field")
    elif data["urgency"] not in VALID_URGENCY:
        failures.append(f"Invalid urgency: '{data['urgency']}' not in {VALID_URGENCY}")

    # Reply present
    if "reply" not in data:
        failures.append("Missing 'reply' field")
    elif not isinstance(data["reply"], str) or len(data["reply"]) == 0:
        failures.append("'reply' is empty or not a string")

    # Cart not empty
    if "cart" not in data:
        failures.append("Missing 'cart' field")
    elif not isinstance(data["cart"], list):
        failures.append(f"'cart' is not a list: {type(data['cart'])}")
    elif len(data["cart"]) == 0:
        failures.append("Cart is empty")
    else:
        # Validate each cart item
        computed_subtotal = 0
        for i, item in enumerate(data["cart"]):
            prefix = f"cart[{i}]"

            if "id" not in item:
                failures.append(f"{prefix}: missing 'id'")
            elif not isinstance(item["id"], str) or len(item["id"]) == 0:
                failures.append(f"{prefix}: 'id' is empty or not a string")

            if "quantity" not in item:
                failures.append(f"{prefix}: missing 'quantity'")
            elif not isinstance(item["quantity"], int) or item["quantity"] <= 0:
                failures.append(f"{prefix}: quantity={item.get('quantity')} (expected int > 0)")

            if "line_total" not in item:
                failures.append(f"{prefix}: missing 'line_total'")
            elif not isinstance(item["line_total"], (int, float)) or item["line_total"] <= 0:
                failures.append(f"{prefix}: line_total={item.get('line_total')} (expected > 0)")
            else:
                computed_subtotal += item["line_total"]

        # Subtotal > 0
        if "subtotal" not in data:
            failures.append("Missing 'subtotal' field")
        elif data["subtotal"] <= 0:
            failures.append(f"subtotal={data['subtotal']} (expected > 0)")
        elif computed_subtotal > 0 and abs(data["subtotal"] - computed_subtotal) > 0.01:
            failures.append(
                f"subtotal mismatch: reported={data['subtotal']}, "
                f"computed sum(line_total)={computed_subtotal}"
            )

    # gap_amount >= 0
    if "gap_amount" not in data:
        failures.append("Missing 'gap_amount' field")
    elif not isinstance(data["gap_amount"], (int, float)) or data["gap_amount"] < 0:
        failures.append(f"gap_amount={data.get('gap_amount')} (expected >= 0)")

    # cached field exists
    if "cached" not in data:
        failures.append("Missing 'cached' field")

    return failures


def call_cart(message: str, cart: list = None) -> httpx.Response | None:
    """POST /api/cart and return the raw response."""
    payload = {"message": message, "cart": cart or []}
    try:
        return httpx.post(
            f"{BASE_URL}/api/cart",
            json=payload,
            timeout=TIMEOUT,
        )
    except httpx.TimeoutException:
        return None
    except httpx.ConnectError:
        return None


def main():
    print("=" * 60)
    print("QCart AI Demo Validation")
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
    results = []
    start = time.time()

    # Phase 1: Validate scenarios
    print("Phase 1: Validating demo scenarios...")
    base_cart = None

    for scenario in SCENARIOS:
        print(f"\n  [{scenario}]")
        resp = call_cart(scenario)
        if resp is None:
            results.append((scenario, ["Connection failed or timeout"]))
            print("    FAIL: Connection failed or timeout")
            continue

        failures = validate_response(scenario, resp)
        results.append((scenario, failures))

        if failures:
            for f in failures:
                print(f"    FAIL: {f}")
        else:
            data = resp.json()
            print(f"    PASS — context={data['context']}, urgency={data['urgency']}, "
                  f"items={len(data['cart'])}, subtotal=₹{data['subtotal']}, "
                  f"gap=₹{data['gap_amount']}, cached={data['cached']}")
            # Save first successful cart for refinements
            if base_cart is None:
                base_cart = data["cart"]

    # Phase 2: Validate refinements
    print("\n\nPhase 2: Validating refinement commands...")

    if base_cart is None:
        print("  SKIP: No base cart available from scenarios")
        for ref in REFINEMENTS:
            results.append((ref, ["Skipped — no base cart"]))
    else:
        current_cart = base_cart
        for refinement in REFINEMENTS:
            print(f"\n  [{refinement}]")
            resp = call_cart(refinement, current_cart)
            if resp is None:
                results.append((refinement, ["Connection failed or timeout"]))
                print("    FAIL: Connection failed or timeout")
                continue

            failures = validate_response(refinement, resp)

            # Special case: "remove dairy" may produce empty cart if all items are dairy
            if refinement == "remove dairy" and resp.status_code == 200:
                data = resp.json()
                if len(data.get("cart", [])) == 0:
                    # Empty cart is valid for remove dairy — clear those failures
                    failures = [f for f in failures
                                if "Cart is empty" not in f
                                and "subtotal" not in f.lower()
                                and "line_total" not in f.lower()]

            results.append((refinement, failures))

            if failures:
                for f in failures:
                    print(f"    FAIL: {f}")
            else:
                data = resp.json()
                print(f"    PASS — context={data['context']}, urgency={data['urgency']}, "
                      f"items={len(data['cart'])}, subtotal=₹{data['subtotal']}, "
                      f"gap=₹{data['gap_amount']}, cached={data['cached']}")
                # Update cart for next refinement
                if data["cart"]:
                    current_cart = data["cart"]

    # Summary
    elapsed = time.time() - start
    passed = sum(1 for _, failures in results if not failures)
    failed = sum(1 for _, failures in results if failures)
    total = len(results)

    print("\n" + "=" * 60)
    print(f"VALIDATION COMPLETE in {elapsed:.1f}s")
    print(f"  Passed: {passed}/{total}")
    print(f"  Failed: {failed}/{total}")
    print("=" * 60)

    if failed > 0:
        print("\nDetailed failures:")
        for label, failures in results:
            if failures:
                print(f"\n  [{label}]")
                for f in failures:
                    print(f"    - {f}")
        sys.exit(1)
    else:
        print("\nAll scenarios validated. Demo is ready!")


if __name__ == "__main__":
    main()
