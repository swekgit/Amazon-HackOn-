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

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import brain
import cache
import catalog
import gap

load_dotenv()

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


@app.get("/api/health")
def health():
    return {"ok": True, "catalog_size": len(catalog.CATALOG), "model": brain.MODEL}


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

    # 3) validate + enrich cart
    cart_lines = []
    for picked in result.get("cart", []):
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
    for s in result.get("suggestions", []):
        p = catalog.get(s.get("product_id"))
        if p and p["id"] not in in_cart:
            suggestions.append({"id": p["id"], "name": p["name"],
                                "price": p["price"], "reason": s.get("reason", "")})

    context = result.get("context", "routine")
    subtotal = sum(l["line_total"] for l in cart_lines)

    # 5) gap engine
    gap_info = gap.compute(cart_lines, context)

    payload = {
        "reply": result.get("reply", "Here's your cart."),
        "context": context,
        "urgency": result.get("urgency", "normal"),
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
