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

  
  GOAL ESSENTIALS CHECKLIST (READINESS):
For goal-oriented contexts (party, movie_night, health, baby, routine, late_night):
Return the COMPLETE checklist of essentials required for the goal.

Return:
"readiness": {
  "label":"<short label>",
  "essentials":[
    {
      "product_id":"<catalog id>",
      "reason":"<max 8 words>"
    }
  ]
}

Rules:
- essentials = the FULL checklist for the goal (items in cart + commonly forgotten items)
- Include BOTH items already present in the cart AND important items not yet in cart
- All product_ids MUST exist in catalog
- Return 4–7 essentials, no duplicates
- For vague/generic requests: essentials []
- Examples:
  movie_night: popcorn, chips, soft drinks, chocolates, tissues
  party: drinks, snacks, cups, napkins, ice
  health: medicine, thermometer, ORS, sanitizer, tissues


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
    "essentials":[
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
    "essentials":[
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


_RECIPE_DETECT_PROMPT = """You are a recipe-intent classifier for a grocery cart AI.

Given a user message, decide if it is a RECIPE REQUEST (the user wants to cook a dish and needs ingredients).

Rules:
- A recipe request names a dish and optionally servings or "already have" items.
- Users often write in Hinglish. Recognise these "already have" patterns:
    "<item> already hai", "<item> hai", "<item> ghar pe hai",
    "<item> aur <item> ghar pe hai", "I have <item>", "I already have <item>"
- Extract every already-have item as a simple English grocery word (e.g. "ghee", "rice", "sugar").
- Examples:
    "gajar ka halwa for 4, ghee already hai"
        → dish: "gajar ka halwa", servings: 4, already_have: ["ghee"]
    "biryani for 6, rice aur ghee ghar pe hai"
        → dish: "biryani", servings: 6, already_have: ["rice", "ghee"]
    "kheer for 4, rice aur milk ghar pe hai"
        → dish: "kheer", servings: 4, already_have: ["rice", "milk"]
    "aloo paratha for 4, atta hai"
        → dish: "aloo paratha", servings: 4, already_have: ["atta"]
    "sooji halwa for 2, ghee ghar pe"
        → dish: "sooji halwa", servings: 2, already_have: ["ghee"]
- Non-recipe messages: "add milk", "party snacks", "make it cheaper"

Respond with ONLY valid JSON, no markdown:
{
  "is_recipe": true | false,
  "dish": "<dish name or null>",
  "servings": <integer or null>,
  "already_have": ["<ingredient>", ...]
}
"""


def detect_recipe(message: str) -> dict:
    """Classify whether the message is a recipe request and extract metadata.

    Returns dict with keys: is_recipe, dish, servings, already_have.
    Never raises — returns is_recipe=false on any failure.
    """
    prompt = f"{_RECIPE_DETECT_PROMPT}\n\nUser message: {message}"
    messages = [{"role": "user", "content": [{"text": prompt}]}]
    try:
        result = invoke_json(Task.INTENT_CLASSIFICATION, messages, temperature=0.1, max_tokens=300)
        parsed = result["parsed"]
        return {
            "is_recipe":    bool(parsed.get("is_recipe", False)),
            "dish":         parsed.get("dish"),
            "servings":     parsed.get("servings"),
            "already_have": parsed.get("already_have") or [],
        }
    except Exception:
        return {"is_recipe": False, "dish": None, "servings": None, "already_have": []}


_RECIPE_INGREDIENTS_PROMPT = """You are a recipe ingredient extractor for a grocery cart AI.

Given a dish name and number of servings, return the SCALED ingredient list.

Rules:
- Scale quantities proportionally to the given servings (base recipe = 2 servings).
- Return ONLY ingredient names the user would buy at a grocery store
  (e.g. "carrots", "milk", "sugar", "ghee", "cashews", "almonds").
- Do NOT include cooking equipment or water.
- Keep names simple and generic (no brand names).
- For nuts and dry fruits, name the SPECIFIC item — never use the generic term
  "dry fruits". Use "cashews", "almonds", "raisins", "pistachios", etc.

Respond with ONLY valid JSON, no markdown:
{
  "ingredients": ["<ingredient>", "<ingredient>", ...]
}
"""


def extract_recipe_ingredients(dish: str, servings: int) -> list[str]:
    """Ask the LLM for the grocery ingredients for a dish scaled to servings.

    Returns list of ingredient name strings. Never raises.
    """
    prompt = (
        f"{_RECIPE_INGREDIENTS_PROMPT}\n\n"
        f"Dish: {dish}\nServings: {servings}"
    )
    messages = [{"role": "user", "content": [{"text": prompt}]}]
    try:
        result = invoke_json(Task.INTENT_CLASSIFICATION, messages, temperature=0.1, max_tokens=400)
        return result["parsed"].get("ingredients") or []
    except Exception:
        return []


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
