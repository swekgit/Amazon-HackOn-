"""The brain.

One conversational turn: given the current cart and the user's new message,
return an updated cart + a short reply + context/urgency classification.
First turn (empty cart) = build from scratch. Later turns = refine.

Now powered by AWS Bedrock via model_router with multi-model fallback:
  - Nova Lite: intent classification, scoring, lightweight tasks
  - Llama 70B / Nova Pro: cart generation, structured JSON
"""

import json
import os
import re

from dotenv import load_dotenv

load_dotenv()

import catalog
from model_router import invoke_json, invoke, Task, get_model_info

# Expose model info for health endpoint
MODEL = get_model_info(Task.CART_GENERATION)["model_id"]

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

  
  OUTCOME ASSURANCE (READINESS):
For goal-oriented contexts (party, movie_night, health, baby, routine, late_night):
Assess whether the cart is complete enough.

Return:
"readiness": {
  "label":"<short label>",
  "score":<0-100>,
  "missing":[
    {
      "product_id":"<catalog id>",
      "reason":"<max 8 words>"
    }
  ]
}

Rules:
- missing products MUST exist in catalog
- never include products already in cart
- max 3 missing products
- genuinely relevant only
- complete cart => score 100
- refinement-only requests => score 100, missing []


OUTPUT (ONLY this JSON, no markdown, no other text):
{
  "reply":"<short sentence>",
  "context":"<context>",
  "urgency":"high|normal",
  "cart":[
    {
      "product_id":"<id>",
      "quantity":1,
      "reason":"..."
    }
  ],
  "suggestions":[
    {
      "product_id":"<id>",
      "reason":"..."
    }
  ],
  "readiness":{
    "label":"...",
    "score":100,
    "missing":[
      {
        "product_id":"...",
        "reason":"..."
      }
    ]
  }
}"""


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

RESPOND WITH ONLY VALID JSON — no markdown, no explanation.

{{
  "reply":"...",
  "context":"...",
  "urgency":"...",
  "cart":[
    {{
      "product_id":"...",
      "quantity":1,
      "reason":"..."
    }}
  ],
  "suggestions":[
    {{
      "product_id":"...",
      "reason":"..."
    }}
  ],
  "readiness":{{
    "label":"...",
    "score":100,
    "missing":[
      {{
        "product_id":"...",
        "reason":"..."
      }}
    ]
  }}
}}
"""

    # Route to Bedrock: cart generation uses Llama/Nova Pro, with fallback
    messages = [
        {"role": "user", "content": [{"text": prompt}]}
    ]

    result = invoke_json(Task.CART_GENERATION, messages, temperature=0.2)
    return result["parsed"]


def recommend_for_you(tags, candidate_products):

    recommended = []

    for p in candidate_products[:5]:
        recommended.append({
            "product_id": p["id"],
            "reason": "Based on your interests"
        })

    deals = []

    for p in candidate_products:
        if "offer" in p:
            deals.append(
                {
                    "product_id": p["id"],
                    "pitch": pitch_for_product(
                        p,
                        tags,
                        p["offer"]["discount_pct"]
                    ),
                }
            )

    return {
        "recommended": recommended[:5],
        "deals": deals[:3]
    }


def personalize_copy(
    tags: list[str],
    recommended_products: list[dict],
    deal_products: list[dict],
) -> dict:

    payload = {
        "customer_tags": tags,
        "recommended": recommended_products,
        "deals": deal_products,
    }

    prompt = f"""
Return ONLY valid JSON.

Customer:
{json.dumps(payload)}

Rules:
- reasons <= 8 words
- pitches <= 10 words
- Use only supplied ids
- Mention only supplied discounts
- No markdown

Output:

{{
  "reasons": {{
    "product_id": "reason"
  }},
  "pitches": {{
    "product_id": "pitch"
  }}
}}
"""

    try:
        messages = [
            {"role": "user", "content": [{"text": prompt}]}
        ]
        result = invoke_json(Task.INTENT_CLASSIFICATION, messages, temperature=0.2, max_tokens=600)
        return result["parsed"]
    except Exception:
        return {
            "reasons": {},
            "pitches": {},
        }
