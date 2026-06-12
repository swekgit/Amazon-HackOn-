"""The brain.

One conversational turn: given the current cart and the user's new message,
return an updated cart + a short reply + context/urgency classification.
First turn (empty cart) = build from scratch. Later turns = refine.

Caching: the catalog + the user's history are the same on every request, so we
mark that block with cache_control. Anthropic then caches that prefix and only
re-processes the small dynamic part (cart + message) — cheaper and faster across
a session. (The cached block needs to be reasonably large to take effect; our
catalog clears that comfortably.)
"""

import json
import os

from anthropic import Anthropic

import catalog

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
client = Anthropic()

INSTRUCTIONS = """You are the brain of a MOMENT-AWARE quick-commerce app (10-min delivery).
The user tells you a moment or need in plain language ("movie night for 4",
"I have fever", "party for 6", "this week's groceries") OR asks to change the
current cart ("make it cheaper", "remove dairy", "add something for the kids").

You receive: the current cart, the user's new message, the product CATALOG, and
the user's recent ORDER HISTORY / preferences.

Rules:
- Build or update the cart to fit the message. If the cart is empty, build it fresh.
- ONLY use product ids that exist in the catalog. Never invent ids.
- Use the history to personalise (respect diet, favour items they reorder), but
  only when relevant to the current moment.
- Set realistic quantities from the number of people / context.
- Respect refinements precisely: "cheaper" -> swap to lower-price picks; "premium"
  -> upgrade; "remove X" -> drop it; "more people" -> scale quantities.
- Classify the moment:
    context  = one of: movie_night, party, health, baby, routine, late_night, other
    urgency  = "high" for health/emergency/late-night essentials, else "normal"
- Also suggest 1-2 complementary items NOT already in the cart (the copilot touch).

Respond with ONLY valid JSON, no markdown, exactly this shape:
{
  "reply": "one short friendly sentence about what you did",
  "context": "movie_night",
  "urgency": "normal",
  "cart": [ { "product_id": "p001", "quantity": 2, "reason": "max 6 words" } ],
  "suggestions": [ { "product_id": "p005", "reason": "max 6 words" } ]
}"""


def _context_block() -> str:
    return (
        f"CATALOG (choose product_id only from here):\n{catalog.compact_catalog()}\n\n"
        f"USER HISTORY / PREFERENCES:\n{catalog.history_summary()}"
    )


def think(message: str, cart: list) -> dict:
    """Returns the raw parsed dict from the model (ids not yet validated)."""
    cart_state = [
        {"product_id": i["id"], "name": i["name"], "quantity": i["quantity"]}
        for i in cart
    ]

    resp = client.messages.create(
        model=MODEL,
        max_tokens=1200,
        system=[
            {"type": "text", "text": INSTRUCTIONS},
            # cached prefix: catalog + history (same every call)
            {"type": "text", "text": _context_block(),
             "cache_control": {"type": "ephemeral"}},
        ],
        messages=[{
            "role": "user",
            "content": (
                f"CURRENT CART: {json.dumps(cart_state)}\n"
                f"USER MESSAGE: {message}"
            ),
        }],
    )

    raw = "".join(b.text for b in resp.content if b.type == "text").strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(raw)
