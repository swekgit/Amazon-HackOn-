"""Build per-cart-line WHY explanations from real personalization signals.

Only cites a reason when the signal genuinely applies to that product.
"""

from __future__ import annotations

import db
import recommendation_engine

# customer behavioral tag → (product tags that must overlap, explanation)
CUSTOMER_TAG_RULES: list[tuple[str, set[str], str]] = [
    ("coffee_lover", {"coffee"}, "Matches your coffee routine"),
    ("night_owl", {"instant", "snack"}, "Fits your late-night snacking"),
    ("premium_buyer", {"premium"}, "Matches your premium preferences"),
    ("party_host", {"party"}, "Great for hosting guests"),
    ("health_conscious", {"healthy", "organic", "low_sugar"}, "Fits your healthy lifestyle"),
    ("vegetarian", {"vegetarian"}, "Matches your vegetarian preference"),
    ("snacker", {"snack"}, "Matches your snacking habit"),
    ("breakfast_routine", {"breakfast"}, "Part of your breakfast routine"),
    ("household_planner", {"household", "staple", "cleaning"}, "Household essential for you"),
    ("weekly_planner", {"staple", "household"}, "Fits your weekly restock"),
    ("family_planner", {"family", "bulk"}, "Family-friendly pick for you"),
    ("tea_lover", {"tea"}, "Matches your tea preference"),
    ("new_parent", {"baby"}, "Useful for your baby-care needs"),
    ("fruit_lover", {"fruit"}, "Matches your fruit preference"),
]

SEGMENT_LABELS = {
    "student": "student shoppers",
    "working": "working professionals",
    "family": "families",
    "senior": "senior shoppers",
}


def load_trending_ids(city: str) -> set[str]:
    if db.trending is None:
        return set()
    try:
        doc = db.trending.find_one({"city": {"$regex": f"^{city}$", "$options": "i"}})
    except Exception:
        return set()
    return set((doc or {}).get("product_ids", []))


def load_past_order_ids(customer_id: str | None) -> set[str]:
    if not customer_id:
        return set()

    ids: set[str] = set()

    if db.customer_cycles is not None:
        try:
            for cycle in db.customer_cycles.find({"customer_id": customer_id}):
                ids.update(cycle.get("item_ids", []))
        except Exception:
            pass

    if db.customers is not None:
        try:
            customer = db.customers.find_one({"customer_id": customer_id})
            if customer:
                for order in customer.get("orders", []):
                    for item in order.get("items", []):
                        pid = item if isinstance(item, str) else item.get("product_id", "")
                        if pid:
                            ids.add(pid)
        except Exception:
            pass

    return ids


def build_item_why(
    product: dict,
    *,
    signals: dict,
    llm_reason: str,
    trending_ids: set[str],
    past_order_ids: set[str],
) -> str:
    """Return a joined WHY string; empty when no signal applies."""
    ptags = set(product.get("tags", []))
    pid = product.get("id", "")
    customer_tags = signals.get("tags") or []
    segment = signals.get("segment", "working")
    city = signals.get("city", "")
    time_bucket = signals.get("time_bucket", "")

    reasons: list[str] = []

    cleaned_reason = (llm_reason or "").strip()
    if cleaned_reason:
        reasons.append(f"Added for your request: {cleaned_reason}")

    for tag, required, message in CUSTOMER_TAG_RULES:
        if tag in customer_tags and ptags.intersection(required):
            reasons.append(message)

    segment_tags = recommendation_engine.SEGMENT_TAGS.get(segment, [])
    if ptags.intersection(segment_tags):
        label = SEGMENT_LABELS.get(segment, segment)
        reasons.append(f"Popular with {label}")

    time_tags = recommendation_engine.TIME_BUCKET_TAGS.get(time_bucket, [])
    if time_bucket and ptags.intersection(time_tags):
        reasons.append(f"Great for {time_bucket} shopping")

    if city and pid in trending_ids:
        reasons.append(f"Trending in {city}")

    if pid in past_order_ids:
        reasons.append("You've ordered this before")

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for r in reasons:
        if r not in seen:
            seen.add(r)
            unique.append(r)

    return " · ".join(unique)


def attach_cart_why(
    cart_lines: list[dict],
    signals: dict,
    *,
    trending_ids: set[str],
    past_order_ids: set[str],
) -> None:
    """Add `why` to each cart line in place. Keeps existing `reason` unchanged."""
    for line in cart_lines:
        line["why"] = build_item_why(
            line,
            signals=signals,
            llm_reason=line.get("reason", ""),
            trending_ids=trending_ids,
            past_order_ids=past_order_ids,
        )
