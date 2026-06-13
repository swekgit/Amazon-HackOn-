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
import re

from openai import OpenAI

import catalog

MODEL = os.getenv(
    "MODEL_NAME",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
)

from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY"),
    timeout=45,
)

INSTRUCTIONS = """You are a quick-commerce cart AI. Respond with ONLY valid JSON.

CONTEXT CLASSIFICATION (case-insensitive, first match wins):
"movie night"→movie_night | "party"→party | "fever"/"sick"/"cold"→health
"baby"/"newborn"/"infant"→baby | "groceries"/"restock"→routine
"late night"/"midnight"→late_night | else→other
On refinement commands, keep previous context.

URGENCY: health/baby→"high", all others→"normal". Only these two values.

CART CONSTRUCTION (empty cart or new scenario):
Tag rules: movie_night→"movie"/"snack", party→"party", health→"fever"/"medicine"
baby→"baby"/"newparent", routine→"weekly"/"staple", late_night→"snack"/"instant"
other→sensible mix. Cart size: 3–10 items. Suggest 1–2 extras not in cart.
Quantity: default 1. For N people: ceil(N/2), min 1, max 6.
ONLY use product_id from CATALOG.

REFINEMENTS (modify current cart, preserve context):
"make it cheaper": swap each item to "cheap"-tagged in same category if exists,
  else keep unchanged. Preserve quantities. Total MUST decrease.
  No alternatives found → return unchanged, explain in reply.
"make it premium": swap each item to "premium"-tagged in same category if exists,
  else keep unchanged. Preserve quantities. Total MUST increase.
  Empty cart → reply no cart to upgrade.
"remove dairy": drop all "dairy"-tagged items. Keep rest unchanged.
  No dairy → unchanged, explain. All dairy → empty cart.
"for N people" (N=1–20): keep same items, set qty=ceil(N/2), min 1, max 6.
  Invalid N → unchanged, explain range. Empty cart → explain.

OUTPUT (ONLY this JSON, no markdown, no other text):
{"reply":"<short sentence>","context":"<context>","urgency":"high|normal",
"cart":[{"product_id":"<id>","quantity":<int>,"reason":"<max 6 words>"}],
"suggestions":[{"product_id":"<id>","reason":"<max 6 words>"}]}"""


def _context_block(message: str) -> str:
    return (
        f"CATALOG (choose product_id only from here):\n{catalog.retrieve(message)}\n\n"
        f"USER HISTORY / PREFERENCES:\n{catalog.history_summary()}"
    )


def think(message: str, cart: list) -> dict:
    """Returns the raw parsed dict from the model (ids not yet validated)."""
    cart_state = [
        {"product_id": i["id"], "name": i["name"], "quantity": i["quantity"]}
        for i in cart
    ]

    prompt = f"""
{INSTRUCTIONS}

{_context_block(message)}

CURRENT CART:
{json.dumps(cart_state)}

USER MESSAGE:
{message}

RESPOND WITH ONLY VALID JSON — no markdown, no explanation. Use this exact schema:
{{"reply": "...", "context": "...", "urgency": "...", "cart": [{{"product_id": "...", "quantity": N, "reason": "..."}}], "suggestions": [{{"product_id": "...", "reason": "..."}}]}}
"""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=16384
    )

    content = resp.choices[0].message.content
    if content is None:
        raise ValueError(
            f"Model returned empty content. "
            f"Check your NVIDIA_API_KEY and that model '{MODEL}' is accessible. "
            f"Finish reason: {resp.choices[0].finish_reason}"
        )

    raw = content.strip()
    raw = (
        raw.removeprefix("```json")
           .removeprefix("```")
           .removesuffix("```")
           .strip()
    )

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: extract first JSON object using regex
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise
