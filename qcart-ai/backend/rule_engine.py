"""Customer Rule Engine — deterministic tag generation from order history.

Analyzes a customer's order history and profile to produce behavioral tags.
No AI/LLM calls — pure rule-based logic using product metadata from catalog.

Usage:
    from rule_engine import generate_tags
    tags = generate_tags(customer_doc)
"""

from collections import Counter
from typing import Any

import catalog


# ─── Thresholds (easy to tune) ─────────────────────────────────────────────────

COFFEE_THRESHOLD = 3        # coffee tag appearances to qualify
TEA_THRESHOLD = 3           # tea tag appearances to qualify
BABY_THRESHOLD = 3          # baby category or tag count
HEALTH_THRESHOLD = 4        # combined health-related tag count
SNACK_DOMINANT_RATIO = 0.4  # snacks must be ≥40% of categories to be "dominant"
PARTY_THRESHOLD = 4         # party-related tag appearances
PLANNER_MIN_ORDERS = 3      # minimum orders to qualify as planner
STAPLE_RECURRENCE = 2       # staple product must appear in ≥2 orders


# ─── Helper: extract stats from order history ──────────────────────────────────

def _build_stats(customer: dict) -> dict:
    """Traverse order history and build frequency counters.

    Returns dict with:
        category_counts: Counter of product categories
        tag_counts: Counter of product tags
        total_products: int
        total_orders: int
        products_per_order: list[set] — product IDs per order (for recurrence)
    """
    category_counts: Counter = Counter()
    tag_counts: Counter = Counter()
    total_products = 0
    total_orders = 0
    products_per_order: list[set] = []

    order_history = customer.get("order_history", [])

    for order in order_history:
        total_orders += 1
        order_product_ids: set = set()

        for product_id in order.get("items", []):
            product = catalog.get(product_id)
            if product is None:
                continue  # safely skip missing products

            total_products += 1
            order_product_ids.add(product_id)

            # Count category
            category_counts[product["category"]] += 1

            # Count each tag
            for tag in product.get("tags", []):
                tag_counts[tag] += 1

        products_per_order.append(order_product_ids)

    return {
        "category_counts": category_counts,
        "tag_counts": tag_counts,
        "total_products": total_products,
        "total_orders": total_orders,
        "products_per_order": products_per_order,
    }


# ─── Individual rule functions ─────────────────────────────────────────────────

def _check_vegetarian(customer: dict, stats: dict) -> bool:
    """Rule: vegetarian if profile.diet == 'vegetarian'."""
    profile = customer.get("profile", {})
    return profile.get("diet") == "vegetarian" or profile.get("veg") is True


def _check_coffee_lover(stats: dict) -> bool:
    """Rule: coffee_lover if coffee tag appears ≥ COFFEE_THRESHOLD times."""
    return stats["tag_counts"].get("coffee", 0) >= COFFEE_THRESHOLD


def _check_tea_lover(stats: dict) -> bool:
    """Rule: tea_lover if tea tag appears ≥ TEA_THRESHOLD times."""
    return stats["tag_counts"].get("tea", 0) >= TEA_THRESHOLD


def _check_new_parent(stats: dict) -> bool:
    """Rule: new_parent if baby category ≥ 3 OR baby tag ≥ 3."""
    baby_category = stats["category_counts"].get("baby", 0)
    baby_tag = stats["tag_counts"].get("baby", 0)
    return baby_category >= BABY_THRESHOLD or baby_tag >= BABY_THRESHOLD


def _check_health_conscious(stats: dict) -> bool:
    """Rule: health_conscious if combined health-related tags are high.

    Counts: fruit, healthy, immunity, fever, medicine, vitamin, protein.
    """
    health_tags = ["fruit", "healthy", "immunity", "fever", "medicine", "protein"]
    combined = sum(stats["tag_counts"].get(t, 0) for t in health_tags)
    return combined >= HEALTH_THRESHOLD


def _check_night_owl(stats: dict) -> bool:
    """Rule: night_owl if snacks category is dominant OR late-night tags frequent.

    Dominant = snacks make up ≥40% of all category hits.
    """
    total_categories = sum(stats["category_counts"].values())
    if total_categories == 0:
        return False

    snack_count = stats["category_counts"].get("snacks", 0)
    snack_ratio = snack_count / total_categories

    instant_count = stats["tag_counts"].get("instant", 0)
    late_night_signals = snack_ratio >= SNACK_DOMINANT_RATIO and instant_count >= 1

    return late_night_signals


def _check_party_host(stats: dict) -> bool:
    """Rule: party_host if party-related tags appear frequently.

    Party tags: party, chips, drink, frozen, birthday.
    """
    party_tags = ["party", "chips", "drink", "frozen", "birthday"]
    combined = sum(stats["tag_counts"].get(t, 0) for t in party_tags)
    return combined >= PARTY_THRESHOLD


def _check_household_planner(stats: dict) -> bool:
    """Rule: household_planner if multiple orders with recurring staple products.

    Requires ≥3 orders AND at least one staple product appearing in ≥2 orders.
    """
    if stats["total_orders"] < PLANNER_MIN_ORDERS:
        return False

    # Count how many orders each product appears in
    product_order_count: Counter = Counter()
    for order_ids in stats["products_per_order"]:
        for pid in order_ids:
            product = catalog.get(pid)
            if product and "staple" in product.get("tags", []):
                product_order_count[pid] += 1

    # Check if any staple product recurs across multiple orders
    return any(count >= STAPLE_RECURRENCE for count in product_order_count.values())


# ─── Main entry point ──────────────────────────────────────────────────────────

def generate_tags(customer: dict) -> list[str]:
    """Generate behavioral tags for a customer based on their profile and order history.

    Args:
        customer: Full customer document from MongoDB (with profile + order_history).

    Returns:
        Sorted, deduplicated list of tag strings.
    """
    stats = _build_stats(customer)
    tags: list[str] = []

    # Profile-based rules
    if _check_vegetarian(customer, stats):
        tags.append("vegetarian")

    # Frequency-based rules
    if _check_coffee_lover(stats):
        tags.append("coffee_lover")

    if _check_tea_lover(stats):
        tags.append("tea_lover")

    if _check_new_parent(stats):
        tags.append("new_parent")

    if _check_health_conscious(stats):
        tags.append("health_conscious")

    if _check_night_owl(stats):
        tags.append("night_owl")

    if _check_party_host(stats):
        tags.append("party_host")

    if _check_household_planner(stats):
        tags.append("household_planner")

    return sorted(set(tags))
