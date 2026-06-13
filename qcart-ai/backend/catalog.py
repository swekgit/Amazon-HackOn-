"""Loads the catalog + the user's history, and exposes lookup helpers.
This is the data layer the rest of the backend builds on."""

import json
from pathlib import Path

DATA = Path(__file__).parent / "data"

CATALOG = json.loads((DATA / "products.json").read_text())
HISTORY = json.loads((DATA / "orders.json").read_text())

BY_ID = {p["id"]: p for p in CATALOG}

# ─── Intent-based retrieval ────────────────────────────────────────────────────

_STOPWORDS = {
    "i", "a", "an", "the", "for", "it", "my", "me", "is", "to", "have",
    "make", "get", "need", "want", "some", "please", "can", "you", "do",
    "of", "and", "or", "in", "on", "up", "so", "we", "us",
}

_INTENT_TAGS = {
    "movie_night": ["movie", "snack", "sweet", "party"],
    "party": ["party", "snack", "drink", "frozen"],
    "health": ["fever", "medicine", "immunity", "cold", "comfort"],
    "baby": ["baby", "newparent"],
    "routine": ["weekly", "staple", "breakfast", "restock"],
    "late_night": ["snack", "instant", "drink"],
    "other": ["snack", "staple"],
}

_CONTEXT_KEYWORDS = {
    "movie night": "movie_night", "movie": "movie_night",
    "party": "party",
    "fever": "health", "sick": "health", "cold": "health",
    "baby": "baby", "newborn": "baby", "infant": "baby",
    "groceries": "routine", "restock": "routine",
    "late night": "late_night", "midnight": "late_night",
}


def _detect_context(intent_lower: str) -> str:
    """Detect context from intent using keyword matching (first match wins)."""
    for keyword, ctx in _CONTEXT_KEYWORDS.items():
        if keyword in intent_lower:
            return ctx
    return "other"


def _extract_keywords(intent: str) -> set:
    """Extract meaningful keywords from intent string."""
    words = intent.lower().split()
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}


def retrieve(intent: str, limit: int = 40) -> str:
    """Return a compact JSON catalog subset relevant to the user intent.

    For refinement commands (premium, cheaper, dairy), ensures swap targets
    are included. Falls back to full catalog if fewer than 10 products match.
    """
    intent_lower = intent.lower().strip()
    keywords = _extract_keywords(intent)

    # Detect refinement commands — need broader product set
    is_premium = "premium" in keywords
    is_cheaper = "cheaper" in keywords or "cheap" in keywords
    is_dairy = "dairy" in keywords

    if is_premium or is_cheaper:
        # Include all products in categories where premium/cheap alternatives exist
        target_tag = "premium" if is_premium else "cheap"
        target_categories = {
            p["category"] for p in CATALOG if target_tag in p["tags"]
        }
        # All products in those categories (so model can see from/to)
        scored = []
        for p in CATALOG:
            if p["category"] in target_categories:
                # Prioritize the target-tagged items
                priority = 2 if target_tag in p["tags"] else 1
                scored.append((priority, p))
            else:
                scored.append((0, p))
        scored.sort(key=lambda x: -x[0])
        results = [p for _, p in scored[:limit]]

    elif is_dairy:
        # Include all dairy-tagged + some context items
        scored = []
        for p in CATALOG:
            score = 2 if "dairy" in p["tags"] else 0
            scored.append((score, p))
        scored.sort(key=lambda x: -x[0])
        results = [p for _, p in scored[:limit]]

    else:
        # Standard context-based retrieval
        context = _detect_context(intent_lower)
        relevant_tags = set(_INTENT_TAGS.get(context, ["snack", "staple"]))

        scored = []
        for p in CATALOG:
            tag_score = len(relevant_tags.intersection(p["tags"]))
            # Keyword match: check if any keyword appears in product tags or name
            name_lower = p["name"].lower()
            kw_score = sum(
                1 for kw in keywords
                if kw in p["tags"] or kw in name_lower
            )
            total = tag_score * 2 + kw_score
            scored.append((total, p))

        scored.sort(key=lambda x: -x[0])
        results = [p for _, p in scored[:limit]]

    # Safety net: if too few results, fall back to full catalog
    if len(results) < 10:
        results = CATALOG[:limit]

    rows = [
        {"id": p["id"], "name": p["name"], "category": p["category"],
         "price": p["price"], "tags": p["tags"]}
        for p in results
    ]
    return json.dumps(rows, separators=(",", ":"))


# ─── Existing public API (unchanged) ──────────────────────────────────────────


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
