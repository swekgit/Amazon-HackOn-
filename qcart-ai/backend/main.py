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

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import brain
import cache
import catalog
import db
import gap

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
