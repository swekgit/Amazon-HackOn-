"""Shared fixtures for QCart AI backend tests.

Provides:
- sys.path setup for importing backend modules
- Catalog access (loads products.json)
- Sample cart generators
- Mock brain response factories
"""

import json
import random
import sys
from pathlib import Path

import pytest

# Ensure the backend directory is importable
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import catalog  # noqa: E402


# ─── Catalog Access ────────────────────────────────────────────────────────────

@pytest.fixture
def products():
    """Full list of products loaded from products.json."""
    return catalog.CATALOG


@pytest.fixture
def products_by_id():
    """Products indexed by ID for quick lookup."""
    return catalog.BY_ID


@pytest.fixture
def valid_product_ids():
    """Set of all valid product IDs in the catalog."""
    return set(catalog.BY_ID.keys())


# ─── Sample Carts ─────────────────────────────────────────────────────────────

@pytest.fixture
def sample_cart(products):
    """A small random cart with 2-5 items from the catalog, quantities 1-10."""
    items = random.sample(products, k=min(random.randint(2, 5), len(products)))
    return [
        {
            "id": p["id"],
            "name": p["name"],
            "category": p["category"],
            "price": p["price"],
            "tags": p["tags"],
            "quantity": random.randint(1, 10),
            "reason": "test item",
            "line_total": p["price"] * random.randint(1, 3),
        }
        for p in items
    ]


@pytest.fixture
def empty_cart():
    """An empty cart."""
    return []


@pytest.fixture
def cart_below_threshold(products):
    """A cart whose subtotal is guaranteed to be below FREE_DELIVERY_THRESHOLD."""
    from gap import FREE_DELIVERY_THRESHOLD

    # Pick cheap items until just under the threshold
    cheap_items = sorted(products, key=lambda p: p["price"])
    cart = []
    subtotal = 0
    for p in cheap_items[:3]:
        qty = 1
        if subtotal + p["price"] >= FREE_DELIVERY_THRESHOLD:
            break
        cart.append({
            "id": p["id"],
            "name": p["name"],
            "category": p["category"],
            "price": p["price"],
            "tags": p["tags"],
            "quantity": qty,
            "reason": "cheap pick",
            "line_total": p["price"] * qty,
        })
        subtotal += p["price"] * qty
    return cart


@pytest.fixture
def cart_above_threshold(products):
    """A cart whose subtotal exceeds FREE_DELIVERY_THRESHOLD."""
    from gap import FREE_DELIVERY_THRESHOLD

    expensive_items = sorted(products, key=lambda p: p["price"], reverse=True)
    cart = []
    subtotal = 0
    for p in expensive_items[:3]:
        qty = 2
        cart.append({
            "id": p["id"],
            "name": p["name"],
            "category": p["category"],
            "price": p["price"],
            "tags": p["tags"],
            "quantity": qty,
            "reason": "expensive pick",
            "line_total": p["price"] * qty,
        })
        subtotal += p["price"] * qty
        if subtotal > FREE_DELIVERY_THRESHOLD:
            break
    return cart


# ─── Mock Brain Responses ──────────────────────────────────────────────────────

@pytest.fixture
def valid_brain_response(valid_product_ids):
    """A well-formed brain response with valid product IDs."""
    ids = list(valid_product_ids)
    cart_ids = random.sample(ids, k=min(3, len(ids)))
    suggestion_ids = random.sample(
        [i for i in ids if i not in cart_ids], k=min(2, len(ids) - 3)
    )
    return {
        "reply": "Here's your cart!",
        "context": "movie_night",
        "urgency": "normal",
        "cart": [
            {"product_id": pid, "quantity": random.randint(1, 5), "reason": "good pick"}
            for pid in cart_ids
        ],
        "suggestions": [
            {"product_id": pid, "reason": "you might like this"}
            for pid in suggestion_ids
        ],
    }


@pytest.fixture
def brain_response_missing_keys():
    """A brain response with several required keys missing."""
    return {
        "reply": "Done!",
        # missing: context, urgency, cart, suggestions
    }


@pytest.fixture
def brain_response_all_keys_missing():
    """A brain response with ALL required keys missing (empty dict)."""
    return {}


@pytest.fixture
def brain_response_invalid_ids(valid_product_ids):
    """A brain response containing a mix of valid and invalid product IDs."""
    valid_ids = list(valid_product_ids)
    valid_picks = random.sample(valid_ids, k=min(2, len(valid_ids)))
    invalid_ids = ["invalid_001", "fake_xyz", "nonexistent_99"]
    mixed_cart = [
        {"product_id": pid, "quantity": 1, "reason": "valid item"}
        for pid in valid_picks
    ] + [
        {"product_id": pid, "quantity": 1, "reason": "invalid item"}
        for pid in invalid_ids
    ]
    random.shuffle(mixed_cart)
    return {
        "reply": "Here you go",
        "context": "routine",
        "urgency": "normal",
        "cart": mixed_cart,
        "suggestions": [
            {"product_id": "ghost_id", "reason": "not real"},
        ],
    }


@pytest.fixture
def brain_response_all_invalid_ids():
    """A brain response where ALL product IDs are invalid."""
    return {
        "reply": "Built your cart",
        "context": "party",
        "urgency": "normal",
        "cart": [
            {"product_id": "bad_001", "quantity": 2, "reason": "fake"},
            {"product_id": "bad_002", "quantity": 1, "reason": "also fake"},
        ],
        "suggestions": [],
    }


# ─── Context Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def valid_contexts():
    """All valid context strings recognized by the gap engine."""
    return ["movie_night", "party", "health", "baby", "routine", "late_night"]


@pytest.fixture
def invalid_contexts():
    """Context strings that should trigger the fallback tag set."""
    return ["unknown", "random_string", "xyz123", "", "not_a_context"]
