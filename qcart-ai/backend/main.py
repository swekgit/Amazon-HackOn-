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
from datetime import datetime, timezone

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

load_dotenv()

log = logging.getLogger(__name__)

DEFAULT_CITY = "Bangalore"

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
    log.info("Trending request for city=%s", city)

    try:
        doc = db.trending.find_one({"city": {"$regex": f"^{city}$", "$options": "i"}})
    except Exception as exc:
        log.error("MongoDB query failed: %s", exc)
        raise HTTPException(502, "Database error.") from exc

    # Fallback to default city if requested city not found
    if not doc and city.lower() != DEFAULT_CITY.lower():
        log.warning("City '%s' not found, falling back to %s", city, DEFAULT_CITY)
        doc = db.trending.find_one({"city": {"$regex": f"^{DEFAULT_CITY}$", "$options": "i"}})

    if not doc:
        raise HTTPException(404, f"No trending products found for city: {city}")

    products = []
    for pid in doc.get("product_ids", []):
        p = catalog.get(pid)
        if p:
            products.append({
                "id": p["id"],
                "name": p["name"],
                "price": p["price"],
                "tags": p["tags"],
            })

    resolved_city = doc.get("city", city)
    log.info("Returning %d trending products for %s", len(products), resolved_city)
    return {"city": resolved_city, "products": products}


# ── Conversational cart ────────────────────────────────────────────────────────


@app.post("/api/cart")
def cart_turn(turn: CartTurn):
    message = turn.message.strip()
    if not message:
        raise HTTPException(400, "Tell me what you need.")

    # 1) cache
    cached = cache.get(message, turn.cart)
    if cached:
        return {**cached, "cached": True}

    # 2) brain
    try:
        result = brain.think(message, turn.cart)
    except json.JSONDecodeError:
        raise HTTPException(502, "Brain returned malformed data, try again.")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Could not reach the brain: {exc}")

    # 2b) Apply fallback defaults for any missing keys
    FALLBACK_DEFAULTS = {
        "reply": "Here's your cart.",
        "context": "routine",
        "urgency": "normal",
        "cart": [],
        "suggestions": [],
    }
    for key, default in FALLBACK_DEFAULTS.items():
        if key not in result:
            result[key] = default

    # 2c) Validate urgency and context values
    VALID_URGENCY = {"high", "normal"}
    VALID_CONTEXT = {"movie_night", "party", "health", "baby", "routine", "late_night", "other"}

    if result["urgency"] not in VALID_URGENCY:
        result["urgency"] = "normal"
    if result["context"] not in VALID_CONTEXT:
        result["context"] = "routine"

    # 3) validate + enrich cart
    cart_lines = []
    for picked in result["cart"]:
        line = catalog.enrich(
            picked.get("product_id"),
            picked.get("quantity", 1),
            picked.get("reason", ""),
        )
        if line:
            cart_lines.append(line)

    if not cart_lines:
        raise HTTPException(404, "Couldn't match anything. Try rephrasing.")

    # 4) suggestions (validate ids)
    suggestions = []
    in_cart = {l["id"] for l in cart_lines}
    for s in result["suggestions"]:
        p = catalog.get(s.get("product_id"))
        if p and p["id"] not in in_cart:
            suggestions.append({"id": p["id"], "name": p["name"],
                                "price": p["price"], "reason": s.get("reason", "")})

    context = result["context"]
    subtotal = sum(l["line_total"] for l in cart_lines)

    # 5) gap engine
    gap_info = gap.compute(cart_lines, context)

    payload = {
        "reply": result["reply"],
        "context": context,
        "urgency": result["urgency"],
        "cart": cart_lines,
        "suggestions": suggestions[:2],
        "subtotal": subtotal,
        "free_delivery_threshold": gap.FREE_DELIVERY_THRESHOLD,
        "gap_amount": gap_info["gap_amount"],
        "gap_fillers": gap_info["gap_fillers"],
        "cached": False,
    }

    cache.set(message, turn.cart, payload)
    return payload

@app.get("/api/foryou")
def for_you(customer_id: str):

    customer = db.customer_tags.find_one(
        {"customer_id": customer_id}
    )

    tags = (customer or {}).get("tags", [])

    if not tags:
        return _default_foryou(customer_id)

    retrieval_query = " ".join(tags)

    candidate_json = catalog.retrieve(
        retrieval_query,
        limit=40,
    )

    candidates = json.loads(candidate_json)

    if not candidates:
        return _default_foryou(customer_id)

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

    scored = sorted(
        candidates,
        key=lambda p: _score_product(p, tags),
        reverse=True,
    )

    recommended_candidates = scored[:8]

    deal_candidates = []

    for p in scored:

        if p["id"] not in offer_map:
            continue

        if _score_product(p, tags) <= 0:
            continue

        deal_candidates.append(p)

    deal_candidates = deal_candidates[:4]

    recommended = []

    for p in recommended_candidates:
        recommended.append(
            {
                "id": p["id"],
                "name": p["name"],
                "price": p["price"],
                "reason": reason_for_product(p,tags)
            }
        )

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

        print(
    p["name"],
    pitch_for_product(
        p,
        tags,
        offer["discount_pct"]
    )
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
        "customer_id": customer_id,
        "tags": tags,
        "recommended": recommended,
        "deals": deals,
    }


def _score_product(product: dict, tags: list[str]) -> int:
    score = 0

    ptags = set(product.get("tags", []))

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
    }

    for tag in tags:
        score += len(ptags.intersection(mapping.get(tag, set())))

    return score


def _default_foryou(customer_id: str):
    popular = catalog.CATALOG[:5]

    return {
        "customer_id": customer_id,
        "tags": [],
        "recommended": [
            {
                "id": p["id"],
                "name": p["name"],
                "price": p["price"],
                "reason": "Popular choice",
            }
            for p in popular
        ],
        "deals": [],
    }


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
