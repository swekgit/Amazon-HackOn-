"""
Persona & Segment Engine
==========================
Demo persona mapping + production segment inference.

Demo personas are FIXED for the 8 demo customers.
Production inference uses ONLY behavioural signals — never demographics.
"""

# ══════════════════════════════════════════════════════════
#  DEMO PERSONAS (Fixed for hackathon demo)
# ══════════════════════════════════════════════════════════

DEMO_CUSTOMERS = {
    "cust_ravi": {"name": "Ravi", "segment": "working"},
    "cust_priya": {"name": "Priya", "segment": "working"},
    "cust_aarav": {"name": "Aarav", "segment": "student"},
    "cust_sneha": {"name": "Sneha", "segment": "family"},
    "cust_karan": {"name": "Karan", "segment": "student"},
    "cust_ananya": {"name": "Ananya", "segment": "working"},
    "cust_rohan": {"name": "Rohan", "segment": "senior"},
    "cust_meera": {"name": "Meera", "segment": "family"},
}

VALID_SEGMENTS = {"student", "working", "senior", "family"}


def get_demo_persona(customer_id: str) -> dict | None:
    """Return demo persona dict if customer is a demo account, else None."""
    persona = DEMO_CUSTOMERS.get(customer_id)
    if persona:
        return {
            "id": customer_id,
            "name": persona["name"],
            "segment": persona["segment"],
        }
    return None


# ══════════════════════════════════════════════════════════
#  PRODUCTION SEGMENT INFERENCE
#  
#  This function demonstrates how segments would be inferred
#  at scale using ONLY behavioural signals from the customer
#  document. It is NOT used for demo customers.
#
#  PRIVACY RULES:
#  - Never use name, gender, age, religion, or demographics.
#  - Only use: delivery addresses, order times, purchase patterns,
#    product categories, and order frequencies.
# ══════════════════════════════════════════════════════════

def infer_segment(customer_document: dict) -> str:
    """
    Infer customer segment from behavioural data ONLY.
    
    Signals used:
    - Delivery address type (office, hostel/PG, university)
    - Frequently purchased product categories
    - Order timing patterns (morning, late-night)
    - Order size patterns (bulk vs single items)
    - Product type patterns (baby, health supplements, instant food)
    
    Returns one of: "student", "working", "senior", "family"
    """
    addresses = customer_document.get("delivery_addresses", [])
    orders = customer_document.get("orders", [])
    frequent_categories = customer_document.get("frequent_categories", [])
    order_times = customer_document.get("order_times", [])

    score = {"student": 0, "working": 0, "senior": 0, "family": 0}

    # Signal: delivery address type
    # Office delivery -> working professional
    # Hostel/PG/University -> student
    for addr in addresses:
        addr_lower = (addr.get("label", "") + " " + addr.get("address", "")).lower()
        if any(kw in addr_lower for kw in ("office", "corporate", "tech park", "business")):
            score["working"] += 3
        if any(kw in addr_lower for kw in ("hostel", "pg", "university", "college", "campus")):
            score["student"] += 3

    # Signal: frequent product categories
    # Baby products -> family
    # Health supplements, BP, diabetes, joint care -> senior
    # Instant food, budget snacks -> student
    # Ready meals, coffee -> working
    cat_lower = [c.lower() for c in frequent_categories]
    if any(kw in cat_lower for kw in ("baby", "diapers", "infant")):
        score["family"] += 4
    if any(kw in cat_lower for kw in ("health", "supplements", "bp", "diabetes", "joint")):
        score["senior"] += 4
    if any(kw in cat_lower for kw in ("instant", "noodles", "chips")):
        score["student"] += 2
    if any(kw in cat_lower for kw in ("coffee", "ready_meals", "protein")):
        score["working"] += 2

    # Signal: order timing
    # Late-night ordering -> student
    # Morning office-hour deliveries -> working
    late_night_count = sum(1 for t in order_times if 22 <= t.get("hour", 12) or t.get("hour", 12) < 5)
    morning_count = sum(1 for t in order_times if 7 <= t.get("hour", 12) <= 10)

    if late_night_count > len(order_times) * 0.3:
        score["student"] += 2
    if morning_count > len(order_times) * 0.4:
        score["working"] += 2

    # Signal: order size patterns
    # Weekly bulk purchases -> family
    # Small single-item orders -> student
    avg_items = 0
    if orders:
        total_items = sum(len(o.get("items", [])) for o in orders)
        avg_items = total_items / len(orders)

    if avg_items > 8:
        score["family"] += 3
    elif avg_items < 3:
        score["student"] += 2

    # Signal: budget patterns
    # Consistently budget items -> student
    avg_order_value = 0
    if orders:
        total_value = sum(o.get("total", 0) for o in orders)
        avg_order_value = total_value / len(orders)

    if avg_order_value < 300:
        score["student"] += 2
    elif avg_order_value > 1500:
        score["family"] += 2

    # Return highest-scoring segment
    best_segment = max(score, key=score.get)
    return best_segment if score[best_segment] > 0 else "working"
