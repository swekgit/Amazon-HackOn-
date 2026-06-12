"""Gap Engine.

Given a built cart, figure out how far it is from the free-delivery threshold,
then pick a few relevant, well-priced items that would close that gap. Pure logic,
no AI — fast and predictable. This is what turns a delivery threshold into a
helpful nudge instead of a fee.
"""

import catalog

FREE_DELIVERY_THRESHOLD = 199          # ₹ — tune for your demo

# Which catalog tags are "relevant" for each detected context.
CONTEXT_TAGS = {
    "movie_night": ["movie", "snack", "sweet"],
    "party": ["party", "snack", "drink"],
    "health": ["fever", "immunity", "comfort"],
    "baby": ["baby", "newparent"],
    "routine": ["weekly", "staple", "breakfast"],
    "late_night": ["snack", "instant", "drink"],
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
        if p["price"] > gap + 60:                 # don't overshoot the gap wildly
            continue
        score = len(relevant.intersection(p["tags"]))
        # closeness to the gap (cheaper-than-gap items preferred), plus relevance
        closeness = -abs(p["price"] - gap)
        candidates.append((score, closeness, p))

    candidates.sort(key=lambda c: (c[0], c[1]), reverse=True)

    fillers = [
        {"id": p["id"], "name": p["name"], "price": p["price"],
         "reason": "rounds you up to free delivery"}
        for _, _, p in candidates[:3]
    ]
    return {"gap_amount": gap, "gap_fillers": fillers}
