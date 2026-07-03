"""QCart AI backend — single conversational endpoint.

Flow per turn:
  client -> POST /api/cart { message, cart }
  -> response cache check (instant on repeats)
  -> brain.think()            (Claude: build/refine + classify)
  -> validate ids, enrich     (drop anything hallucinated)
  -> gap.compute()            (free-delivery nudge)
  -> assemble contract, cache, return
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import brain
import cache
import catalog
import db
import gap
import db
import rule_engine
import persona
import recommendation_engine
import cart_why
import moments
import moment_cache

load_dotenv()

log = logging.getLogger(__name__)

DEFAULT_CITY = "Bangalore"

# City aliases for normalization (common alternate names)
CITY_ALIASES = {
    "bengaluru": "Bangalore",
    "bombay": "Mumbai",
    "madras": "Chennai",
    "calcutta": "Kolkata",
    "new delhi": "Delhi",
}


def _normalize_city(city: str) -> str:
    """Normalize city name: trim, title-case, resolve aliases."""
    city = city.strip()
    city_lower = city.lower()
    # Check aliases first
    if city_lower in CITY_ALIASES:
        return CITY_ALIASES[city_lower]
    # Return title-cased version
    return city.title()

app = FastAPI(title="QCart AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten before any real launch
    allow_methods=["*"],
    allow_headers=["*"],
)


class CartTurn(BaseModel):
    message: str
    cart: list = []               # current cart lines (empty on first turn)
    customer_id: str | None = None
    city: str = DEFAULT_CITY


def _load_cart_signals(customer_id: str | None, city: str) -> dict:
    """Load personalization signals for cart generation (reuses foryou sources)."""
    normalized_city = _normalize_city(city)
    segment = "working"
    tags: list[str] = []

    if customer_id:
        demo_persona = persona.get_demo_persona(customer_id)
        if demo_persona:
            segment = demo_persona["segment"]
        elif db.customers is not None:
            customer_doc = db.customers.find_one({"customer_id": customer_id})
            if customer_doc:
                segment = persona.infer_segment(customer_doc)

        if db.customer_tags is not None:
            tag_doc = db.customer_tags.find_one({"customer_id": customer_id})
            tags = (tag_doc or {}).get("tags", [])

    return {
        "customer_id": customer_id,
        "segment": segment,
        "tags": tags,
        "city": normalized_city,
        "time_bucket": recommendation_engine.get_time_bucket(),
    }


# ── Lightweight reads ──────────────────────────────────────────────────────────


@app.get("/api/health")
def health():
    return {"ok": True, "catalog_size": len(catalog.CATALOG), "model": brain.MODEL}


@app.get("/api/cities")
def list_cities():
    """Return all cities that have trending data in MongoDB."""
    try:
        cities = db.trending.distinct("city")
        cities.sort()
        log.info("Loaded %d cities from db.trending", len(cities))
        return {"cities": cities}
    except Exception as exc:
        log.error("Failed to fetch cities: %s", exc)
        raise HTTPException(502, "Could not load city list.") from exc


@app.get("/api/trending")
def trending_products(city: str = DEFAULT_CITY):
    """Return trending products for a city, resolved via catalog."""
    normalized = _normalize_city(city)
    log.info("Trending request for city=%s (normalized=%s)", city, normalized)

    try:
        doc = db.trending.find_one({"city": {"$regex": f"^{normalized}$", "$options": "i"}})
    except Exception as exc:
        log.error("MongoDB query failed: %s", exc)
        raise HTTPException(502, "Database error.") from exc

    if not doc:
        log.warning("No trending data for city '%s'", normalized)
        return {"city": normalized, "products": []}

    products = []
    for pid in doc.get("product_ids", []):
        p = catalog.get(pid)
        if p:
            products.append({
                "id": p["id"],
                "name": p["name"],
                "price": p["price"],
                "tags": p["tags"],
                "image": f"{IMAGE_BASE_URL}/{p['id']}.jpg",
            })

    resolved_city = doc.get("city", normalized)
    log.info("Returning %d trending products for %s", len(products), resolved_city)
    return {"city": resolved_city, "products": products}




import re

IMAGE_BASE_URL = "https://qcart-ai-apoorva-images.s3.ap-south-1.amazonaws.com/products"
_VALID_PRODUCT_ID = re.compile(r"^p\d{4}$")


@app.get("/api/buyagain")
def buy_again(customer_id: str):
    """Return frequently purchased products for a customer, data-driven from order history.

    Sources: MongoDB customer_cycles or orders collection.
    Falls back to empty list if no history exists.
    """
    # Try to get purchase history from customer cycles (predicted reorders)
    products_freq = {}

    if db.customer_cycles is not None:
        try:
            cycles = list(db.customer_cycles.find(
                {"customer_id": customer_id}, {"_id": 0}
            ))
            for cycle in cycles:
                for pid in cycle.get("item_ids", []):
                    products_freq[pid] = products_freq.get(pid, 0) + cycle.get("frequency", 1)
        except Exception as exc:
            log.warning("buy_again cycles query failed: %s", exc)

    # Also check customer document for order history
    if db.customers is not None and not products_freq:
        try:
            customer = db.customers.find_one({"customer_id": customer_id})
            if customer:
                for order in customer.get("orders", []):
                    for item in order.get("items", []):
                        pid = item if isinstance(item, str) else item.get("product_id", "")
                        if pid:
                            products_freq[pid] = products_freq.get(pid, 0) + 1
        except Exception as exc:
            log.warning("buy_again orders query failed: %s", exc)

    if not products_freq:
        return {"customer_id": customer_id, "products": []}

    # Sort by frequency (desc), then validate against catalog
    sorted_pids = sorted(products_freq.keys(), key=lambda p: -products_freq[p])

    results = []
    for pid in sorted_pids:
        if not _VALID_PRODUCT_ID.match(pid):
            log.warning("buy_again: skipping legacy/invalid product id %r", pid)
            continue
        p = catalog.get(pid)
        if not p:
            continue
        if p.get("stock_status") == "out_of_stock":
            continue
        results.append({
            "id": p["id"],
            "name": p["name"],
            "price": p["price"],
            "brand": p.get("brand", ""),
            "category": p["category"],
            "image": f"{IMAGE_BASE_URL}/{p['id']}.jpg",
            "frequency": products_freq[pid],
        })
        if len(results) >= 10:
            break

    return {"customer_id": customer_id, "products": results}


# ── Conversational cart ────────────────────────────────────────────────────────


def _generate_cart_payload(
    message: str,
    cart: list,
    signals: dict,
    customer_id: str | None,
) -> dict:
    """Build a full /api/cart response (includes WHY on each line)."""
    recipe_meta = brain.detect_recipe(message)
    recipe_result = None
    suggestions: list[dict] = []

    if recipe_meta["is_recipe"]:
        recipe_result, cart_lines, suggestions = _handle_recipe(recipe_meta, cart)
        result = {
            "reply": f"Here's your cart for {recipe_meta['dish']}!",
            "context": "routine",
            "urgency": "normal",
            "cart": [],
            "suggestions": [],
            "readiness": {"label": "", "essentials": []},
        }
    else:
        try:
            result = brain.think(message, cart, signals)
        except json.JSONDecodeError as exc:
            raise HTTPException(502, "Brain returned malformed data, try again.") from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(502, f"Could not reach the brain: {exc}") from exc

        fallback_defaults = {
            "reply": "Here's your cart.",
            "context": "routine",
            "urgency": "normal",
            "cart": [],
            "suggestions": [],
            "readiness": {"label": "", "essentials": []},
        }
        for key, default in fallback_defaults.items():
            if key not in result:
                result[key] = default

        valid_urgency = {"high", "normal"}
        valid_context = {
            "movie_night", "party", "health", "baby", "routine", "late_night", "other",
        }
        if result["urgency"] not in valid_urgency:
            result["urgency"] = "normal"
        if result["context"] not in valid_context:
            result["context"] = "routine"

        cart_lines = []
        cart_product_ids = {
            item.get("product_id")
            for item in result["cart"]
            if item.get("product_id")
        }

        for picked in result["cart"]:
            line = catalog.enrich(
                picked.get("product_id"),
                picked.get("quantity", 1),
                picked.get("reason", ""),
            )
            if not line:
                continue
            alt = catalog.find_alternatives(line["id"], cart_product_ids)
            line["alternatives"] = alt["alternatives"]
            cart_lines.append(line)

        if not cart_lines:
            raise HTTPException(404, "Couldn't match anything. Try rephrasing.")

        suggestions = []
        in_cart = {line["id"] for line in cart_lines}
        for s in result["suggestions"]:
            p = catalog.get(s.get("product_id"))
            if p and p["id"] not in in_cart:
                suggestions.append({
                    "id": p["id"],
                    "name": p["name"],
                    "price": p["price"],
                    "reason": s.get("reason", ""),
                })

    context = result["context"]
    raw_readiness = result.get("readiness", {})
    enriched_essentials = []
    seen_ids: set[str] = set()

    for item in raw_readiness.get("essentials", []):
        product = catalog.get(item.get("product_id"))
        if not product or product["id"] in seen_ids:
            continue
        seen_ids.add(product["id"])
        enriched_essentials.append({
            "id": product["id"],
            "name": product["name"],
            "price": product["price"],
            "reason": item.get("reason", ""),
        })

    enriched_essentials = enriched_essentials[:7]
    label = raw_readiness.get("label", "")
    if not label and enriched_essentials:
        label = f"{context.replace('_', ' ').title()} readiness"

    readiness = {"label": label, "essentials": enriched_essentials}

    trending_ids = cart_why.load_trending_ids(signals["city"])
    past_order_ids = cart_why.load_past_order_ids(customer_id)
    cart_why.attach_cart_why(
        cart_lines,
        signals,
        trending_ids=trending_ids,
        past_order_ids=past_order_ids,
    )

    subtotal = sum(line["line_total"] for line in cart_lines)
    gap_info = gap.compute(cart_lines, context)
    payment_offers = _generate_smart_payment_offers(cart_lines, subtotal, context)

    return {
        "reply": result["reply"],
        "context": context,
        "urgency": result["urgency"],
        "cart": cart_lines,
        "recipe": recipe_result,
        "suggestions": suggestions[:6],
        "readiness": readiness,
        "subtotal": subtotal,
        "free_delivery_threshold": gap.FREE_DELIVERY_THRESHOLD,
        "gap_amount": gap_info["gap_amount"],
        "gap_fillers": gap_info["gap_fillers"],
        "payment_offers": payment_offers,
        "saved_payments": [
            {"label": "ICICI Credit Card", "last4": "4521"},
            {"label": "Amazon Pay UPI", "last4": ""},
            {"label": "HDFC Debit Card", "last4": "8890"},
        ],
        "cached": False,
    }


def _moment_cart_generator(signals: dict, customer_id: str | None):
    def generate(moment_id: str) -> dict | None:
        moment = moments.get_by_id(moment_id)
        if not moment:
            return None
        try:
            return _generate_cart_payload(moment["intent"], [], signals, customer_id)
        except HTTPException:
            return None

    return generate


@app.get("/api/moments")
def list_moments(
    customer_id: str | None = None,
    city: str = DEFAULT_CITY,
    pool: str = "missions",
):
    """Personalized moment suggestions for a customer (tags + segment + city)."""
    if pool not in ("missions", "trending"):
        raise HTTPException(400, "pool must be 'missions' or 'trending'")

    signals = _load_cart_signals(customer_id, city)
    ranked = moments.rank_for_customer(pool, signals)

    result = []
    for moment in ranked:
        cached = moment_cache.get(
            customer_id,
            signals["city"],
            moment["id"],
            signals["time_bucket"],
        ) is not None
        result.append({**moment, "cached": cached})

    moment_cache.prewarm_async(
        customer_id,
        signals["city"],
        signals["time_bucket"],
        [moment["id"] for moment in ranked],
        _moment_cart_generator(signals, customer_id),
    )

    return {
        "customer_id": customer_id,
        "city": signals["city"],
        "segment": signals["segment"],
        "tags": signals["tags"],
        "moments": result,
    }


@app.get("/api/moments/{moment_id}/cart")
def moment_cart(
    moment_id: str,
    customer_id: str | None = None,
    city: str = DEFAULT_CITY,
):
    """Return a pre-generated cart for a moment (instant on cache hit)."""
    moment = moments.get_by_id(moment_id)
    if not moment:
        raise HTTPException(404, f"Unknown moment '{moment_id}'.")

    signals = _load_cart_signals(customer_id, city)
    hit = moment_cache.get(
        customer_id,
        signals["city"],
        moment_id,
        signals["time_bucket"],
    )
    if hit:
        return {**hit, "cached": True, "moment_id": moment_id}

    payload = _generate_cart_payload(moment["intent"], [], signals, customer_id)
    moment_cache.set(
        customer_id,
        signals["city"],
        moment_id,
        signals["time_bucket"],
        payload,
    )
    cache.set(moment["intent"], [], payload, signals)
    return {**payload, "cached": False, "moment_id": moment_id}


@app.post("/api/cart")
def cart_turn(turn: CartTurn):
    message = turn.message.strip()
    if not message:
        raise HTTPException(400, "Tell me what you need.")

    signals = _load_cart_signals(turn.customer_id, turn.city)

    cached = cache.get(message, turn.cart, signals)
    if cached:
        return {**cached, "cached": True}

    payload = _generate_cart_payload(message, turn.cart, signals, turn.customer_id)
    cache.set(message, turn.cart, payload, signals)
    return payload


def _handle_recipe(recipe_meta: dict, current_cart: list) -> tuple[dict, list, list]:
    """Process a recipe request end-to-end via semantic ingredient resolution.

    1. Resolve each already_have item to its swap_group via Titan embeddings.
    2. Extract ingredient list for dish + servings via LLM.
    3. For each ingredient, call catalog.resolve_ingredient() (confidence-gated).
       - If resolve returns None → ingredient goes to unmatched (no wrong product added).
       - If swap_group is in already-have set → skipped.
       - Otherwise → enrich + add to cart.

    Returns (recipe_block, cart_lines, suggestions).
    Never invents product ids.
    """
    dish     = recipe_meta["dish"] or "the dish"
    servings = int(recipe_meta["servings"] or 2)

    # Step 1: resolve already-have items to swap_groups semantically
    have_groups: set[str] = set()
    for item in recipe_meta.get("already_have", []):
        r = catalog.resolve_ingredient(item)
        if r:
            have_groups.add(r["swap_group"])

    # Step 2: get ingredient list from LLM
    ingredients = brain.extract_recipe_ingredients(dish, servings)

    cart_product_ids: set[str] = set()
    cart_lines:       list[dict] = []
    skipped:          list[dict] = []
    unmatched:        list[str]  = []

    for ing in ingredients:
        # Step 3: semantic resolve with confidence gates
        r = catalog.resolve_ingredient(ing)
        if not r:
            # No confident match → omit cleanly; do NOT add a wrong product
            unmatched.append(ing)
            continue

        # Already-have check is swap_group based (semantic, not string matching)
        if r["swap_group"] in have_groups:
            skipped.append({"name": ing, "why": "already have", "swap_group": r["swap_group"]})
            continue

        best = r["product"]
        if best["id"] in cart_product_ids:
            continue

        line = catalog.enrich(best["id"], 1, f"for {dish}")
        if not line:
            unmatched.append(ing)
            continue

        alt = catalog.find_alternatives(best["id"], cart_product_ids)
        line["alternatives"] = alt["alternatives"]
        cart_product_ids.add(best["id"])
        cart_lines.append(line)

    recipe_block = {
        "is_recipe": True,
        "dish":      dish,
        "servings":  servings,
        "skipped":   skipped,
        "unmatched": unmatched,
    }

    return recipe_block, cart_lines, []

@app.get("/api/foryou")
def for_you(customer_id: str, city: str = DEFAULT_CITY):
    """PERSONALIZED For You feed per customer (segment + city + tags).
    
    Each customer sees different recommendations based on:
    - Their segment (student/working/family/senior)
    - Their city (for trending)
    - Their behavioral tags (from rule engine)
    """
    # Get persona/segment
    demo_persona = persona.get_demo_persona(customer_id)
    segment = demo_persona["segment"] if demo_persona else "working"

    customer_info = {
        "id": customer_id,
        "name": demo_persona["name"] if demo_persona else customer_id,
        "segment": segment,
    }

    customer = db.customer_tags.find_one(
        {"customer_id": customer_id}
    )

    tags = (customer or {}).get("tags", [])

    # ALWAYS use personalized recommendation engine (segment + city + tags)
    recommended = recommendation_engine.get_recommendations(tags, segment, city)
    trending = recommendation_engine.get_trending(city)

    # Build retrieval query combining tags + segment
    retrieval_query = " ".join(tags + [segment, city]) if tags else f"{segment} {city}"

    candidate_json = catalog.retrieve(
        retrieval_query,
        limit=40,
    )

    candidates = json.loads(candidate_json)

    if not candidates:
        return {
            "customer": customer_info,
            "tags": tags,
            "recommended": recommended[:8],
            "deals": [],
            "trending": trending[:6],
        }

    candidate_ids = [p["id"] for p in candidates]

    offers_cursor = db.offers.find(
        {
            "product_id": {
                "$in": candidate_ids
            }
        }
    )

    offer_map = {
        o["product_id"]: {
            "discount_pct": o["discount_pct"],
            "offer_label": o.get("offer_label", ""),
        }
        for o in offers_cursor
    }

    # Score products based on tags + segment
    scored = sorted(
        candidates,
        key=lambda p: _score_product(p, tags, segment),
        reverse=True,
    )

    deal_candidates = []

    for p in scored:
        if p["id"] not in offer_map:
            continue

        if _score_product(p, tags, segment) <= 0:
            continue

        deal_candidates.append(p)

    deal_candidates = deal_candidates[:4]

    deals = []

    for p in deal_candidates:
        offer = offer_map[p["id"]]

        deals.append(
            {
                "id": p["id"],
                "name": p["name"],
                "price": p["price"],
                "discount_pct": offer["discount_pct"],
                "offer_label": offer["offer_label"],
                "discounted_price": round(
                    p["price"] * (1 - offer["discount_pct"] / 100)
                ),
                "pitch": pitch_for_product(
                    p,
                    tags,
                    offer["discount_pct"]
                ),
            }
        )

    try:
        copy_result = brain.personalize_copy(
            tags=tags,
            recommended_products=[
                {
                    "id": r["id"],
                    "name": r["name"],
                }
                for r in recommended
            ],
            deal_products=[
                {
                    "id": d["id"],
                    "name": d["name"],
                    "discount_pct": d["discount_pct"],
                }
                for d in deals
            ],
        )

        reasons = copy_result.get("reasons", {})
        pitches = copy_result.get("pitches", {})

        for item in recommended:
            item["reason"] = reasons.get(
                item["id"],
                item["reason"],
            )

        for item in deals:
            item["pitch"] = pitches.get(
                item["id"],
                item["pitch"],
            )

    except Exception:
        pass

    return {
        "customer": customer_info,
        "tags": tags,
        "recommended": recommended[:8],
        "deals": deals,
        "trending": trending[:6],
    }

@app.get("/api/predicted")
def predicted_reorders(customer_id: str):
    """PERSONALIZED predicted reorders per customer.
    
    Returns customer-specific kits from customer_cycles collection.
    Examples:
    - cust_meera → "Period-care kit" (pads, painkiller, chocolate, hot water bag)
    - cust_ravi → "Monthly staples" (milk, atta, rice, oil)
    """
    if db.customer_cycles is None:
        raise HTTPException(503, "MongoDB not configured.")

    cycles = list(
        db.customer_cycles.find(
            {"customer_id": customer_id},
            {"_id": 0}
        )
    )

    if not cycles:
        log.info(f"predicted_reorders: No cycles found for customer_id={customer_id}")
        return {"predictions": []}

    today = datetime.now(timezone.utc).date()

    predictions = []

    for cycle in cycles:
        last_purchase_raw = cycle.get("last_purchase")

        if not last_purchase_raw:
            continue

        try:
            last_purchase = (
                datetime.fromisoformat(
                    last_purchase_raw.replace("Z", "+00:00")
                ).date()
            )
        except Exception:
            continue

        interval_days = int(
            cycle.get("interval_days", 0)
        )

        if interval_days <= 0:
            continue

        next_date = last_purchase + timedelta(
            days=interval_days
        )

        days_until = (
            next_date - today
        ).days

        if days_until > 3:
            continue

        cart = []
        subtotal = 0

        for product_id in cycle.get("item_ids", []):
            product = catalog.get(product_id)

            if not product:
                log.warning(f"predicted_reorders: product {product_id} not found in catalog")
                continue

            cart.append(
                {
                    "id": product["id"],
                    "name": product["name"],
                    "price": product["price"],
                    "quantity": 1,
                }
            )

            subtotal += product["price"]

        if not cart:
            continue

        predictions.append(
            {
                "label": cycle.get("label", ""),
                "private": cycle.get("private", False),
                "due_in_days": days_until,
                "interval_days": interval_days,
                "reason": f"you usually reorder every {interval_days} days",
                "cart": cart,
                "subtotal": subtotal,
            }
        )

    predictions.sort(
        key=lambda p: p["due_in_days"]
    )

    log.info(f"predicted_reorders: Returning {len(predictions)} predictions for {customer_id}")
    return {
        "predictions": predictions
    }

def _score_product(product: dict, tags: list[str], segment: str = "working") -> int:
    """Score product relevance based on tags AND segment."""
    score = 0

    ptags = set(product.get("tags", []))

    # Tag-based scoring
    mapping = {
        "party_host": {"party"},
        "entertainer": {"party", "snack"},
        "premium_buyer": {"premium"},
        "coffee_lover": {"coffee"},
        "snacker": {"snack"},
        "fruit_lover": {"fruit"},
        "health_conscious": {"healthy"},
        "vegetarian": {"vegetarian"},
        "breakfast_routine": {"breakfast"},
        "night_owl": {"instant", "snack"},
        "household_planner": {"household", "cleaning", "staple"},
        "weekly_planner": {"staple", "household"},
        "family_planner": {"family", "bulk"},
        "tea_lover": {"tea"},
        "new_parent": {"baby"},
    }

    for tag in tags:
        score += len(ptags.intersection(mapping.get(tag, set()))) * 3

    # Segment-based scoring boost
    segment_boosts = {
        "student": {"instant", "snack", "cheap"},
        "working": {"coffee", "premium", "ready_to_eat", "protein"},
        "family": {"bulk", "staple", "family", "household"},
        "senior": {"healthy", "organic", "diabetic"},
    }

    if segment in segment_boosts:
        score += len(ptags.intersection(segment_boosts[segment])) * 2

    return score


def _default_foryou(customer_id: str, city: str = DEFAULT_CITY):
    """Default personalized foryou when customer has no tags in DB."""
    demo_persona = persona.get_demo_persona(customer_id)
    segment = demo_persona["segment"] if demo_persona else "working"

    customer_info = {
        "id": customer_id,
        "name": demo_persona["name"] if demo_persona else customer_id,
        "segment": segment,
    }

    # Still use personalized recommendation engine (segment + city)
    recommended = recommendation_engine.get_recommendations([], segment, city)
    trending = recommendation_engine.get_trending(city)

    return {
        "customer": customer_info,
        "tags": [],
        "recommended": recommended[:8],
        "deals": [],
        "trending": trending[:6],
    }


def _suggest_items_for_offer_gap(
    gap_amount: int,
    cart_lines: list[dict],
    context: str,
    limit: int = 2,
) -> list[dict]:
    """Pick 1–2 catalog items that help close an offer threshold gap."""
    if gap_amount <= 0:
        return []

    in_cart = {line["id"] for line in cart_lines}
    relevant = set(gap.CONTEXT_TAGS.get(context, ["snack", "staple"]))

    candidates = []
    for p in catalog.CATALOG:
        if p["id"] in in_cart:
            continue
        tag_score = len(relevant.intersection(p.get("tags", [])))
        candidates.append((tag_score, abs(p["price"] - gap_amount), p))

    covering = [c for c in candidates if c[2]["price"] >= gap_amount]
    if covering:
        covering.sort(key=lambda c: (-c[0], c[2]["price"]))
        pool = covering
    else:
        candidates.sort(key=lambda c: (-c[0], c[1]))
        pool = candidates

    return [
        {"id": p["id"], "name": p["name"], "price": p["price"]}
        for _, _, p in pool[:limit]
    ]


def _generate_smart_payment_offers(cart_lines: list[dict], subtotal: float, context: str) -> list[dict]:
    """Return the best unlocked offer plus the next tier with gap + filler items."""
    cart_categories = {line["category"] for line in cart_lines}
    tiers: list[dict] = [
        {
            "id": "po_icici",
            "title": "ICICI Bank 10% off",
            "min_subtotal": 299,
            "rate": 0.10,
            "max_savings": 75,
        },
        {
            "id": "po_amazonpay",
            "title": "Amazon Pay 5% cashback",
            "min_subtotal": 200,
            "rate": 0.05,
            "max_savings": 50,
        },
    ]

    if context == "health" or "health" in cart_categories:
        if any(
            "medicine" in line.get("tags", []) or "fever" in line.get("tags", [])
            for line in cart_lines
        ):
            tiers.append({
                "id": "po_health",
                "title": "Health Essentials 15% off",
                "min_subtotal": 0,
                "rate": 0.15,
                "max_savings": 9999,
            })
    elif context == "party" or "party" in cart_categories:
        tiers.append({
            "id": "po_party",
            "title": "Party Combo Offer",
            "min_subtotal": 500,
            "flat_savings": 100,
        })

    all_offers: list[dict] = []
    for tier in tiers:
        flat = tier.get("flat_savings")
        min_subtotal = tier["min_subtotal"]
        eligible = subtotal >= min_subtotal

        if flat is not None:
            saved = int(flat) if eligible else 0
        else:
            saved = int(min(subtotal * tier["rate"], tier["max_savings"])) if eligible else 0

        gap_amount = max(0, int(min_subtotal - subtotal)) if not eligible else 0
        max_label = flat if flat is not None else tier.get("max_savings", 0)

        if eligible:
            detail = f"Save up to ₹{saved} • Eligible now ✓"
        else:
            detail = f"Add ₹{gap_amount} more to avail {tier['title']} (save up to ₹{max_label})"

        all_offers.append({
            "id": tier["id"],
            "title": tier["title"],
            "detail": detail,
            "eligible": eligible,
            "saved_amount": saved,
            "savings": saved,
            "gap_amount": gap_amount,
            "min_subtotal": min_subtotal,
        })

    locked = sorted(
        [o for o in all_offers if not o["eligible"]],
        key=lambda o: (o["gap_amount"], o["min_subtotal"]),
    )

    result: list[dict] = []

    for next_offer in locked[:2]:
        offer = dict(next_offer)
        gap = offer["gap_amount"]
        tier_title = offer["title"]
        max_label = next(
            (
                t.get("flat_savings") or t.get("max_savings", 0)
                for t in tiers
                if t["title"] == tier_title
            ),
            0,
        )
        suggested = _suggest_items_for_offer_gap(gap, cart_lines, context, limit=2)
        if suggested:
            names = ", ".join(item["name"] for item in suggested)
            offer["detail"] = (
                f"Add ₹{gap} more to avail {tier_title} (save up to ₹{max_label}) — try {names}"
            )
            offer["suggested_items"] = suggested
        else:
            offer["detail"] = (
                f"Add ₹{gap} more to avail {tier_title} (save up to ₹{max_label})"
            )
        offer["savings"] = 0
        result.append(offer)

    return result


@app.get("/api/all-tags")
def all_tags():
    return list(
        db.customer_tags.find(
            {},
            {"_id": 0}
        )
    )

@app.get("/api/debug-product")
def debug_product():
    return catalog.CATALOG[:3]

def reason_from_tags(tags):

    if "party_host" in tags:
        return "Perfect for your next gathering"

    if "premium_buyer" in tags:
        return "Matches your premium taste"

    if "coffee_lover" in tags:
        return "Great with your coffee routine"

    if "health_conscious" in tags:
        return "Fits your healthy lifestyle"

    return "Picked for your profile"


def pitch_from_tags(tags, discount):

    if "party_host" in tags:
        return f"Party favorite at {discount}% off"

    if "premium_buyer" in tags:
        return f"Premium pick, save {discount}%"

    if "coffee_lover" in tags:
        return f"Coffee companion with {discount}% savings"

    return f"Save {discount}% today"

def reason_for_product(product, tags):

    name = product["name"].lower()
    ptags = set(product.get("tags", []))

    if "coffee_lover" in tags and (
        "coffee" in name or "coffee" in ptags
    ):
        return "Perfect for your coffee routine"

    if "night_owl" in tags and (
        "instant" in ptags or
        "snack" in ptags
    ):
        return "Ideal for late-night cravings"

    if "premium_buyer" in tags and "premium" in ptags:
        return "Matches your premium preferences"

    if "party_host" in tags and "party" in ptags:
        return "Great for hosting guests"

    if "health_conscious" in tags:
        return "Fits your healthy lifestyle"

    return "Picked for your profile"

def pitch_for_product(product, tags, discount):

    name = product["name"].lower()

    if "coffee" in name:
        return f"Coffee essential at {discount}% off"

    if "pizza" in name:
        return f"Party favorite at {discount}% off"

    if "cola" in name:
        return f"Perfect party combo, save {discount}%"

    if "milk" in name:
        return f"Daily essential, save {discount}%"

    if "popcorn" in name:
        return f"Movie-night deal, save {discount}%"

    return f"Save {discount}% today"
# ─── Customer Endpoints ────────────────────────────────────────────────────────


@app.get("/api/customer/{customer_id}")
def get_customer(customer_id: str):
    """Fetch a customer document by ID."""
    if db.customers is None:
        raise HTTPException(503, "MongoDB not configured.")

    doc = db.customers.find_one({"customer_id": customer_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, f"Customer '{customer_id}' not found.")
    return doc


@app.post("/api/customer/{customer_id}/tags")
def generate_customer_tags(customer_id: str):
    """Generate and save behavioral tags for a customer using the rule engine."""
    if db.customers is None or db.customer_tags is None:
        raise HTTPException(503, "MongoDB not configured.")

    # Load customer
    customer = db.customers.find_one({"customer_id": customer_id})
    if not customer:
        raise HTTPException(404, f"Customer '{customer_id}' not found.")

    # Generate tags via rule engine
    tags = rule_engine.generate_tags(customer)

    # Upsert into customer_tags collection
    db.customer_tags.update_one(
        {"customer_id": customer_id},
        {"$set": {
            "customer_id": customer_id,
            "tags": tags,
            "updated_at": datetime.now(timezone.utc),
        }},
        upsert=True,
    )

    return {"customer_id": customer_id, "tags": tags}
