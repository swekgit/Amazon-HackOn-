"""Loads the catalog + the user's history, and exposes lookup helpers.
This is the data layer the rest of the backend builds on."""

import json
from pathlib import Path

DATA = Path(__file__).parent / "data"

CATALOG = json.loads((DATA / "products.json").read_text())
HISTORY = json.loads((DATA / "orders.json").read_text())

BY_ID = {p["id"]: p for p in CATALOG}


def get(product_id: str):
    """Return a product dict by id, or None."""
    return BY_ID.get(product_id)


def compact_catalog() -> str:
    """Catalog as a compact JSON string for the prompt (id/name/category/price/tags)."""
    rows = [
        {"id": p["id"], "name": p["name"], "category": p["category"],
         "price": p["price"], "tags": p["tags"]}
        for p in CATALOG
    ]
    return json.dumps(rows, separators=(",", ":"))


def history_summary() -> str:
    """Readable history block so Claude can personalise (Context Engine)."""
    prefs = HISTORY.get("preferences", {})
    freq = [BY_ID[i]["name"] for i in HISTORY.get("frequently_bought", []) if i in BY_ID]
    return json.dumps({"preferences": prefs, "frequently_bought": freq})


def enrich(product_id: str, quantity: int, reason: str = "") -> dict | None:
    """Turn a picked id into a full cart line. Returns None if id is unknown."""
    p = BY_ID.get(product_id)
    if not p:
        return None
    qty = max(1, int(quantity))
    return {
        "id": p["id"],
        "name": p["name"],
        "category": p["category"],
        "price": p["price"],
        "tags": p["tags"],
        "quantity": qty,
        "reason": reason,
        "line_total": p["price"] * qty,
    }
