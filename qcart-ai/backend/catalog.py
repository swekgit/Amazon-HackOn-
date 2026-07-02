"""Loads the catalog + the user's history, and exposes lookup helpers.
This is the data layer the rest of the backend builds on."""

import json
import logging
import os
from collections import defaultdict
from pathlib import Path

import boto3
import db

log = logging.getLogger(__name__)

DATA = Path(__file__).parent / "data"

# ─── S3 image base URL ────────────────────────────────────────────────────────
_IMAGE_BASE = "https://qcart-ai-apoorva-images.s3.ap-south-1.amazonaws.com/products/"

# ─── OpenSearch config (optional — falls back to keyword if not set) ──────────
_OS_ENDPOINT = os.getenv("OPENSEARCH_ENDPOINT", "").strip()
_OS_INDEX    = os.getenv("OPENSEARCH_INDEX", "qcart-products")
_OS_REGION   = os.getenv("OPENSEARCH_REGION", "us-east-1")

# ─── Titan Embed Text v2 on Bedrock ──────────────────────────────────────────
_BEDROCK_REGION  = os.getenv("AWS_REGION", "us-east-1")
_EMBED_MODEL_ID  = "amazon.titan-embed-text-v2:0"   # 1024-dim, normalize=true
EMBED_DIM        = 1024

# ─── resolve_ingredient tunable constants ─────────────────────────────────────
# After a clean rebuild with normalize=True + faiss+innerproduct,
# Titan inner-product scores are in [-1, 1] (cosine similarity).
# Typical exact-match scores: 0.85–0.97. Weak/wrong matches: 0.55–0.75.
#
# SIM_FLOOR   — reject if the best individual hit score < this value.
#               Start at 0.75; lower to 0.70 if valid ingredients get dropped.
# RESOLVE_MARGIN — winning group's summed score must beat runner-up by this factor.
#               1.20 = 20% dominance required. Lower if valid matches are dropped.
# RESOLVE_K   — k-NN neighbours fetched. Raise to 60 if rare groups are missed.
RESOLVE_K         = 40     # k-NN neighbours fetched per query
SIM_FLOOR         = 0.75   # minimum best_sim (post normalize=True rebuild)
RESOLVE_MARGIN    = 1.10   # winning group summed score >= runner-up * MARGIN

# ─── kept for back-compat (used by old _opensearch_retrieve path) ─────────────
_COHERE_MODEL_ID = _EMBED_MODEL_ID
_COHERE_BATCH    = 96

# lazy-init: created on first use so import doesn't block if no creds
_bedrock_client = None

# ─── Deprecated local-embed vars kept so _opensearch_retrieve still compiles ──
_EMBED_MODEL  = os.getenv("BEDROCK_EMBED_MODEL", "amazon.titan-embed-text-v2:0")
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

# ─── Cohere Embed Multilingual v3 — shared helpers ───────────────────────────

def _get_bedrock():
    """Lazy-init Bedrock client (created once, thread-safe enough for FastAPI)."""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = boto3.client("bedrock-runtime", region_name=_BEDROCK_REGION)
    return _bedrock_client


def embed(texts: list[str], input_type: str) -> list[list[float]]:
    """Embed a list of texts using Amazon Titan Embed Text v2 (1024-dim, normalized).

    Sends dimensions=1024 and normalize=true. normalize=true is REQUIRED because
    the OpenSearch index uses faiss + innerproduct: inner product equals cosine
    similarity only when vectors are unit-normalized.

    input_type is accepted for API compatibility (Titan ignores it).
    Titan takes ONE text per call — iterates internally.
    """
    client = _get_bedrock()
    results = []
    for text in texts:
        body = json.dumps({
            "inputText":  text,
            "dimensions": EMBED_DIM,
            "normalize":  True,
        })
        resp = client.invoke_model(modelId=_EMBED_MODEL_ID, body=body)
        vec  = json.loads(resp["body"].read())["embedding"]
        results.append(vec)
    return results


def product_embedding_text(p: dict) -> str:
    """Canonical text representation of a product for embedding."""
    return (
        f'{p["name"]}. '
        f'category: {p["category"]}. '
        f'type: {p.get("swap_group") or ""}. '
        f'brand: {p.get("brand") or ""}. '
        f'tags: {", ".join(p.get("tags", []))}'
    )


def _get_os_client():
    """Build and return a cached OpenSearch client (lazy-init)."""
    from opensearchpy import OpenSearch, RequestsHttpConnection
    from requests_aws4auth import AWS4Auth

    session     = boto3.Session()
    credentials = session.get_credentials()
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        _OS_REGION,
        "es",
        session_token=credentials.token,
    )
    return OpenSearch(
        hosts=[{"host": _OS_ENDPOINT, "port": 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=10,
    )


def _knn_search(qvec: list[float], k: int) -> list[dict]:
    """Run a kNN search against the OpenSearch index. Returns scored hit dicts."""
    client = _get_os_client()
    body = {
        "size": k,
        "query": {
            "knn": {
                "embedding": {
                    "vector": qvec,
                    "k":      k,
                }
            }
        },
    }
    res = client.search(index=_OS_INDEX, body=body)
    return [
        {"product": h["_source"], "score": h["_score"]}
        for h in res["hits"]["hits"]
    ]


def resolve_ingredient(ingredient: str, k: int = RESOLVE_K) -> dict | None:
    """Map a free-text ingredient name to ONE real catalog product.

    Algorithm:
    1. Embed the ingredient text with Titan (normalize=True, dims=1024).
    2. k-NN search in OpenSearch (k=RESOLVE_K) → hits with raw similarity scores.
    3. Group hits by swap_group, summing their scores (group voting).
    4. Apply TWO numeric confidence gates — no hardcoded per-ingredient logic:
         (a) best_sim >= SIM_FLOOR  — absolute minimum confidence
         (b) winning_group_sum >= second_best_group_sum * RESOLVE_MARGIN
             — the winner must clearly dominate the runner-up
       If either gate fails → return None (caller puts ingredient in unmatched).
    5. Within the winning group: prefer in_stock, then rank by raw similarity
       with small boosts for prime_eligible and rating.

    Returns:
        {"swap_group": str, "product": dict, "alternatives": list[dict]}
        or None if confidence gates fail or OpenSearch is not configured.
    """
    if not _OS_ENDPOINT:
        return None
    try:
        qvec = embed([ingredient], "search_query")[0]
        hits = _knn_search(qvec, k)
        if not hits:
            return None

        # Group voting
        group_score: dict[str, float]      = defaultdict(float)
        group_hits:  dict[str, list[dict]] = defaultdict(list)

        for h in hits:
            p  = h["product"]
            sg = p.get("swap_group") or f'__solo::{p["id"]}'
            group_score[sg] += h["score"]
            group_hits[sg].append(h)

        # Find best group
        ranked_groups = sorted(group_score.items(), key=lambda kv: -kv[1])
        best_group, best_sum = ranked_groups[0]
        second_sum = ranked_groups[1][1] if len(ranked_groups) > 1 else 0.0

        # Best raw similarity from the winning group
        best_sim = max(h["score"] for h in group_hits[best_group])

        # Gate (a): absolute similarity floor
        if best_sim < SIM_FLOOR:
            log.debug(
                "resolve_ingredient(%r): REJECTED best_sim=%.4f < SIM_FLOOR=%.4f",
                ingredient, best_sim, SIM_FLOOR,
            )
            return None

        # Gate (b): winning group must clearly beat runner-up
        if second_sum > 0 and best_sum < second_sum * RESOLVE_MARGIN:
            log.debug(
                "resolve_ingredient(%r): REJECTED margin fail "
                "best_sum=%.4f second_sum=%.4f MARGIN=%.2f",
                ingredient, best_sum, second_sum, RESOLVE_MARGIN,
            )
            return None

        # Rank within winning group
        members = group_hits[best_group]
        pool    = [m for m in members if m["product"].get("stock_status") == "in_stock"] or members

        ranked = sorted(
            pool,
            key=lambda m: (
                m["score"]
                + (0.03 if m["product"].get("prime_eligible") else 0.0)
                + 0.01 * float(m["product"].get("rating") or 0)
            ),
            reverse=True,
        )

        log.debug(
            "resolve_ingredient(%r) → swap_group=%r best_sim=%.4f group_sum=%.4f",
            ingredient, best_group, best_sim, best_sum,
        )

        return {
            "swap_group":   best_group,
            "product":      ranked[0]["product"],
            "alternatives": [r["product"] for r in ranked[1:4]],
        }

    except Exception as exc:
        log.warning("resolve_ingredient(%r) failed: %s", ingredient, exc)
        return None


def _opensearch_retrieve(intent: str, limit: int) -> list[dict] | None:
    """Vector search via OpenSearch using Cohere embeddings.
    Returns product list or None on failure / not configured.
    """
    if not _OS_ENDPOINT:
        return None
    try:
        qvec = embed([intent], "search_query")[0]
        hits = _knn_search(qvec, limit)
        return [h["product"] for h in hits]
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


# ─── OpenSearch index builder (run once, NOT on import) ───────────────────────

def build_index() -> None:
    """Force-delete + recreate the OpenSearch kNN index, then ingest all products.

    - ALWAYS deletes and recreates (clean rebuild — no mixed Cohere/Titan vectors).
    - Uses Titan Embed Text v2 with dimensions=1024, normalize=True.
    - Retries each embed call on ThrottlingException with exponential backoff.
    - Asserts doc count == product count before returning.

    Run once:
        cd qcart-ai/backend
        python catalog.py
    """
    import time

    if not _OS_ENDPOINT:
        print("ERROR: OPENSEARCH_ENDPOINT not set. Cannot build index.")
        return

    client = _get_os_client()

    INDEX_MAPPING = {
        "settings": {"index.knn": True},
        "mappings": {
            "properties": {
                "id":             {"type": "keyword"},
                "name":           {"type": "text"},
                "category":       {"type": "keyword"},
                "swap_group":     {"type": "keyword"},
                "brand":          {"type": "keyword"},
                "price":          {"type": "float"},
                "rating":         {"type": "float"},
                "prime_eligible": {"type": "boolean"},
                "stock_status":   {"type": "keyword"},
                "tags":           {"type": "keyword"},
                "embedding": {
                    "type":      "knn_vector",
                    "dimension": EMBED_DIM,
                    "method": {
                        "name":       "hnsw",
                        "space_type": "innerproduct",
                        "engine":     "faiss",
                    },
                },
            }
        },
    }

    # Always delete and recreate for a clean build (no mixed vectors)
    if client.indices.exists(index=_OS_INDEX):
        print(f"Deleting existing index '{_OS_INDEX}' for clean rebuild...")
        client.indices.delete(index=_OS_INDEX)

    client.indices.create(index=_OS_INDEX, body=INDEX_MAPPING)
    print(f"Created index '{_OS_INDEX}' (dim={EMBED_DIM}, faiss+innerproduct).")

    # ── Embed + ingest with retry on throttling ───────────────────────────────
    products = get_catalog()
    total    = len(products)
    print(f"Catalog: {total} products to index.")

    def embed_with_retry(text: str, max_tries: int = 5) -> list[float]:
        delay = 0.5
        for attempt in range(max_tries):
            try:
                return embed([text], "search_document")[0]
            except Exception as e:
                if "ThrottlingException" in type(e).__name__ or "throttl" in str(e).lower():
                    if attempt < max_tries - 1:
                        print(f"  Throttled — retrying in {delay:.1f}s ...", flush=True)
                        time.sleep(delay)
                        delay = min(delay * 2, 8.0)
                    else:
                        raise
                else:
                    raise

    indexed = 0
    for p in products:
        text = product_embedding_text(p)
        vec  = embed_with_retry(text)

        doc = {
            "id":             p["id"],
            "name":           p["name"],
            "category":       p["category"],
            "swap_group":     p.get("swap_group"),
            "brand":          p.get("brand", ""),
            "price":          p.get("price", 0),
            "rating":         p.get("rating"),
            "prime_eligible": p.get("prime_eligible", False),
            "stock_status":   p.get("stock_status", "in_stock"),
            "tags":           p.get("tags", []),
            "embedding":      vec,
        }
        client.index(index=_OS_INDEX, id=p["id"], body=doc)
        indexed += 1
        if indexed % 50 == 0 or indexed == total:
            print(f"  indexed {indexed}/{total}", flush=True)

    client.indices.refresh(index=_OS_INDEX)
    count = client.count(index=_OS_INDEX)["count"]
    print(f"\nTOTAL in index: {count}/{total}")
    if count >= total:
        print("ALL DONE ✅ (normalize=True, faiss+innerproduct)")
    else:
        print(f"⚠ Only {count}/{total} docs indexed — re-run to continue.")
        raise RuntimeError(f"Index incomplete: {count}/{total}")


if __name__ == "__main__":
    build_index()
