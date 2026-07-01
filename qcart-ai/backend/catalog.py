"""Loads the catalog + the user's history, and exposes lookup helpers.
This is the data layer the rest of the backend builds on."""

import json
import logging
import os
from pathlib import Path

import db

log = logging.getLogger(__name__)

DATA = Path(__file__).parent / "data"

# ─── S3 image base URL ────────────────────────────────────────────────────────
_IMAGE_BASE = "https://qcart-ai-apoorva-images.s3.ap-south-1.amazonaws.com/products/"

# ─── OpenSearch config (optional — falls back to keyword if not set) ──────────
_OS_ENDPOINT = os.getenv("OPENSEARCH_ENDPOINT", "").strip()
_OS_INDEX    = os.getenv("OPENSEARCH_INDEX", "qcart-products")
_EMBED_MODEL = os.getenv(
    "BEDROCK_EMBED_MODEL",
    "amazon.titan-embed-text-v2:0",
)
_EMBED_REGION = os.getenv("BEDROCK_EMBED_REGION", "us-east-1")


def get_catalog() -> list[dict]:
    """Load product catalog from MongoDB if available, else fall back to JSON file.

    Returns a list of product dicts. Never raises — gracefully degrades.
    """
    # Try MongoDB first
    if db.products is not None:
        try:
            if db.is_connected():
                docs = list(db.products.find({}, {"_id": 0}))
                if docs:
                    return docs
        except Exception:
            pass

    # Fallback: load from local JSON file
    products_data = json.loads((DATA / "products.json").read_text())
    # products.json may be a plain list or {"products": [...]}
    if isinstance(products_data, list):
        return products_data
    return products_data.get("products", [])


CATALOG = get_catalog()

HISTORY = json.loads((DATA / "orders.json").read_text())

BY_ID = {p["id"]: p for p in CATALOG}

# ─── Intent-based retrieval ────────────────────────────────────────────────────

_STOPWORDS = {
    "i", "a", "an", "the", "for", "it", "my", "me", "is", "to", "have",
    "make", "get", "need", "want", "some", "please", "can", "you", "do",
    "of", "and", "or", "in", "on", "up", "so", "we", "us",
}

_INTENT_TAGS = {
    "movie_night": ["movie", "snack", "sweet", "party"],
    "party": ["party", "snack", "drink", "frozen"],
    "health": ["fever", "medicine", "immunity", "cold", "comfort"],
    "baby": ["baby", "newparent"],
    "routine": ["weekly", "staple", "breakfast", "restock"],
    "late_night": ["snack", "instant", "drink"],
    "other": ["snack", "staple"],
}

_CONTEXT_KEYWORDS = {
    "movie night": "movie_night", "movie": "movie_night",
    "party": "party",
    "fever": "health", "sick": "health", "cold": "health",
    "baby": "baby", "newborn": "baby", "infant": "baby",
    "groceries": "routine", "restock": "routine",
    "late night": "late_night", "midnight": "late_night",
}


def _detect_context(intent_lower: str) -> str:
    """Detect context from intent using keyword matching (first match wins)."""
    for keyword, ctx in _CONTEXT_KEYWORDS.items():
        if keyword in intent_lower:
            return ctx
    return "other"


def _extract_keywords(intent: str) -> set:
    """Extract meaningful keywords from intent string."""
    words = intent.lower().split()
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}


def _row(p: dict) -> dict:
    """Compact product row returned to the LLM — includes all required fields."""
    return {
        "id":         p["id"],
        "name":       p["name"],
        "category":   p["category"],
        "swap_group": p.get("swap_group"),
        "brand":      p.get("brand", ""),
        "price":      p["price"],
        "tags":       p["tags"],
    }


# ─── OpenSearch vector retrieval (primary) ────────────────────────────────────

def _embed(text: str) -> list[float] | None:
    """Generate a Bedrock embedding for text. Returns None on any failure."""
    try:
        import boto3
        client = boto3.client("bedrock-runtime", region_name=_EMBED_REGION)
        body = json.dumps({"inputText": text})
        response = client.invoke_model(
            modelId=_EMBED_MODEL,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response["body"].read())
        return result.get("embedding")
    except Exception as exc:
        log.warning("Bedrock embed failed: %s", exc)
        return None


def _opensearch_retrieve(intent: str, limit: int) -> list[dict] | None:
    """Vector search via OpenSearch. Returns product list or None on failure."""
    if not _OS_ENDPOINT:
        return None
    try:
        from opensearchpy import OpenSearch, RequestsHttpConnection
        from requests_aws4auth import AWS4Auth
        import boto3

        session = boto3.Session()
        credentials = session.get_credentials()
        region = os.getenv("OPENSEARCH_REGION", _EMBED_REGION)
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            "es",
            session_token=credentials.token,
        )
        client = OpenSearch(
            hosts=[{"host": _OS_ENDPOINT, "port": 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=5,
        )

        vector = _embed(intent)
        if vector is None:
            return None

        query = {
            "size": limit,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": vector,
                        "k": limit,
                    }
                }
            },
            "_source": ["id", "name", "category", "swap_group", "brand", "price", "tags"],
        }
        response = client.search(index=_OS_INDEX, body=query)
        hits = response.get("hits", {}).get("hits", [])
        return [h["_source"] for h in hits]
    except Exception as exc:
        log.warning("OpenSearch retrieval failed: %s", exc)
        return None


# ─── Keyword retrieval (fallback) ─────────────────────────────────────────────

def _keyword_retrieve(intent: str, limit: int) -> list[dict]:
    """Keyword-based retrieval searching name, category, tags, brand."""
    intent_lower = intent.lower().strip()
    keywords = _extract_keywords(intent)

    is_premium = "premium" in keywords
    is_cheaper = "cheaper" in keywords or "cheap" in keywords
    is_dairy   = "dairy" in keywords

    if is_premium or is_cheaper:
        target_tag = "premium" if is_premium else "cheap"
        target_categories = {p["category"] for p in CATALOG if target_tag in p["tags"]}
        scored = []
        for p in CATALOG:
            if p["category"] in target_categories:
                priority = 2 if target_tag in p["tags"] else 1
                scored.append((priority, p))
            else:
                scored.append((0, p))
        scored.sort(key=lambda x: -x[0])
        results = [p for _, p in scored[:limit]]

    elif is_dairy:
        scored = [(2 if "dairy" in p["tags"] else 0, p) for p in CATALOG]
        scored.sort(key=lambda x: -x[0])
        results = [p for _, p in scored[:limit]]

    else:
        context = _detect_context(intent_lower)
        relevant_tags = set(_INTENT_TAGS.get(context, ["snack", "staple"]))

        scored = []
        for p in CATALOG:
            tag_score  = len(relevant_tags.intersection(p["tags"]))
            name_lower = p["name"].lower()
            brand_lower = p.get("brand", "").lower()
            cat_lower  = p["category"].lower()
            kw_score = sum(
                1 for kw in keywords
                if kw in p["tags"]
                or kw in name_lower
                or kw in cat_lower
                or kw in brand_lower
            )
            total = tag_score * 2 + kw_score
            scored.append((total, p))

        scored.sort(key=lambda x: -x[0])
        results = [p for _, p in scored[:limit]]

    if len(results) < 10:
        results = CATALOG[:limit]

    return results


def retrieve(intent: str, limit: int = 40) -> str:
    """Return a compact JSON catalog subset relevant to the user intent.

    PRIMARY:  OpenSearch vector retrieval (if OPENSEARCH_ENDPOINT is set).
    FALLBACK: Keyword retrieval (always works, never throws).

    Logs which retriever was used.
    Rows returned include: id, name, category, swap_group, brand, price, tags.
    """
    products = _opensearch_retrieve(intent, limit)

    if products is not None:
        log.info("Retriever used = OpenSearch")
    else:
        log.info("Retriever used = KeywordFallback")
        raw = _keyword_retrieve(intent, limit)
        products = [_row(p) for p in raw]

    # Ensure every row has the required fields (OpenSearch docs may vary)
    rows = []
    for p in products:
        rows.append({
            "id":         p.get("id", ""),
            "name":       p.get("name", ""),
            "category":   p.get("category", ""),
            "swap_group": p.get("swap_group"),
            "brand":      p.get("brand", ""),
            "price":      p.get("price", 0),
            "tags":       p.get("tags", []),
        })

    return json.dumps(rows, separators=(",", ":"))


# ─── Existing public API (unchanged) ──────────────────────────────────────────


def get(product_id: str):
    """Return a product dict by id, or None."""
    return BY_ID.get(product_id)


def compact_catalog() -> str:
    """Catalog as a compact JSON string for the prompt (id/name/category/swap_group/brand/price/tags)."""
    rows = [_row(p) for p in CATALOG]
    return json.dumps(rows, separators=(",", ":"))


def history_summary() -> str:
    """Readable history block so Claude can personalise (Context Engine)."""
    prefs = HISTORY.get("preferences", {})
    freq = [BY_ID[i]["name"] for i in HISTORY.get("frequently_bought", []) if i in BY_ID]
    return json.dumps({"preferences": prefs, "frequently_bought": freq})


def enrich(product_id: str, quantity: int, reason: str = "") -> dict | None:
    """Turn a picked id into a full cart line. Returns None if id is unknown.

    Adds brand and image fields (Task 3).
    brand: from catalog, empty string if not present.
    image: S3 URL constructed from product id.
    """
    p = BY_ID.get(product_id)
    if not p:
        return None
    qty = max(1, int(quantity))
    return {
        "id":         p["id"],
        "name":       p["name"],
        "category":   p["category"],
        "price":      p["price"],
        "tags":       p["tags"],
        "quantity":   qty,
        "reason":     reason,
        "line_total": p["price"] * qty,
        "brand":      p.get("brand", ""),
        "image":      f"{_IMAGE_BASE}{p['id']}.jpg",
    }

def find_alternatives(product_id: str, cart_ids: set[str]) -> dict:

    current = BY_ID.get(product_id)

    if not current:
        return {
            "cheaper": None,
            "premium": None,
            "alternatives": [],
        }

    swap_group = current.get("swap_group")

    if not swap_group:
        return {
            "cheaper": None,
            "premium": None,
            "alternatives": [],
        }

    current_price = current["price"]

    candidates = [
        p
        for p in CATALOG
        if p.get("swap_group") == swap_group
        and p["id"] != product_id
        and p["id"] not in cart_ids
    ]

    cheaper_candidates = [
        p for p in candidates
        if p["price"] < current_price
    ]

    premium_candidates = [
        p for p in candidates
        if p["price"] > current_price
    ]

    cheaper = None
    premium = None

    if cheaper_candidates:
        best = max(
            cheaper_candidates,
            key=lambda p: p["price"]
        )
        cheaper = {
            "id": best["id"],
            "name": best["name"],
            "price": best["price"],
        }

    if premium_candidates:
        best = min(
            premium_candidates,
            key=lambda p: p["price"]
        )
        premium = {
            "id": best["id"],
            "name": best["name"],
            "price": best["price"],
        }

    # New: structured alternatives list (max 3)
    # Priority: 1) cheaper, 2) prime eligible, 3) highest rating
    scored_alts = []
    for p in candidates:
        reason = ""
        priority = 0

        if p["price"] < current_price:
            reason = "cheaper"
            priority = 3
        elif p.get("prime_eligible"):
            reason = "faster"
            priority = 2
        else:
            # Skip items that are neither cheaper nor prime_eligible
            continue

        scored_alts.append((priority, p.get("rating", 0), p, reason))

    # Sort by priority desc, then rating desc
    scored_alts.sort(key=lambda x: (-x[0], -x[1]))

    alternatives = []
    for _, _, p, reason in scored_alts[:3]:
        alternatives.append({
            "id": p["id"],
            "name": p["name"],
            "brand": p.get("brand", ""),
            "price": p["price"],
            "reason": reason,
        })

    return {
        "cheaper": cheaper,
        "premium": premium,
        "alternatives": alternatives,
    }