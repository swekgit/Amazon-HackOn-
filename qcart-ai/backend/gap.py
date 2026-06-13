"""Gap Engine.

Given a built cart, figure out how far it is from the free-delivery threshold,
then pick a few relevant, well-priced items that would close that gap. Pure logic,
no AI — fast and predictable. This is what turns a delivery threshold into a
helpful nudge instead of a fee.
"""

import catalog

FREE_DELIVERY_THRESHOLD = 399          # ₹ — tune for your demo

# Which catalog tags are "relevant" for each detected context.
CONTEXT_TAGS = {
    "movie_night": ["movie", "snack", "sweet"],
    "party": ["party", "snack", "drink"],
    "health": ["fever", "immunity", "comfort", "medicine"],
    "baby": ["baby", "newparent"],
    "routine": ["weekly", "staple", "breakfast"],
    "late_night": ["snack", "instant", "drink"],
    "other": ["snack", "staple"],
}


def compute(cart: list, context: str = "routine") -> dict:
    subtotal = sum(i["line_total"] for i in cart)
    gap = max(0, FREE_DELIVERY_THRESHOLD - subtotal)

    if gap == 0:
        return {"gap_amount": 0, "gap_fillers": []}

    in_cart = {i["id"] for i in cart}
    relevant = set(CONTEXT_TAGS.get(context, ["snack", "staple"]))

    candidates = []
    for p in catalog.CATALOG:
        if p["id"] in in_cart:
            continue
        score = len(relevant.intersection(p["tags"]))
        abs_diff = abs(p["price"] - gap)
        candidates.append((score, abs_diff, p))

    # Primary sort: tag-overlap descending; secondary: abs price-gap difference ascending
    candidates.sort(key=lambda c: (-c[0], c[1]))

    # Cumulative overshoot guard: combined filler prices must not exceed gap + 60
    max_total = gap + 60
    fillers = []
    running_total = 0
    for _, _, p in candidates:
        if len(fillers) >= 3:
            break
        if running_total + p["price"] > max_total:
            continue
        running_total += p["price"]
        fillers.append(
            {"id": p["id"], "name": p["name"], "price": p["price"],
             "reason": "rounds you up to free delivery"}
        )

    return {"gap_amount": gap, "gap_fillers": fillers}
