"""Loads the catalog + the user's history, and exposes lookup helpers.
This is the data layer the rest of the backend builds on."""

import json
import logging
import os
from collections import defaultdict
from functools import cmp_to_key
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
_EMBED_MODEL_ID  = os.getenv("BEDROCK_EMBED_MODEL", "amazon.titan-embed-text-v2:0")
EMBED_DIM        = int(os.getenv("BEDROCK_EMBED_DIM", "1024"))

# ─── resolve_ingredient tunable constants (env-backed, calibrated defaults) ───
# SIM_FLOOR      — winning group's max-cosine must be >= this value.
# RESOLVE_MARGIN — winner max-cosine >= margin-runner max-cosine * MARGIN.
# RESOLVE_K      — k-NN neighbours fetched per query.
_GROUP_RANK_EPSILON = float(os.getenv("RESOLVE_GROUP_EPSILON", "0.01"))
RESOLVE_K         = int(os.getenv("RESOLVE_K", "40"))
SIM_FLOOR         = float(os.getenv("SIM_FLOOR", "0.2996"))
RESOLVE_MARGIN    = float(os.getenv("RESOLVE_MARGIN", "1.05"))

# ─── kept for back-compat (used by old _opensearch_retrieve path) ─────────────
_COHERE_MODEL_ID = _EMBED_MODEL_ID
_COHERE_BATCH    = 96

# lazy-init: created on first use so import doesn't block if no creds
_bedrock_client = None

# ─── Deprecated local-embed vars kept so _opensearch_retrieve still compiles ──
_EMBED_MODEL  = _EMBED_MODEL_ID
_EMBED_REGION = os.getenv("BEDROCK_EMBED_REGION", _BEDROCK_REGION)


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
        timeout=60,
        max_retries=3,
        retry_on_timeout=True,
    )


def _knn_search(qvec: list[float], k: int) -> list[dict]:
    """Run a kNN search against the OpenSearch index.

    Returns hit dicts with true cosine similarity in ``score`` (OpenSearch
    innerproduct returns _score = 1 + cosine).
    """
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
        {"product": h["_source"], "score": h["_score"] - 1.0}
        for h in res["hits"]["hits"]
    ]


def _group_hits_by_swap_group(hits: list[dict]) -> tuple[
    dict[str, float], dict[str, float], dict[str, list[dict]]
]:
    """Aggregate kNN hits by swap_group: max-cosine, sum-of-cosine, member hits."""
    group_max: dict[str, float] = {}
    group_sum: dict[str, float] = defaultdict(float)
    group_hits: dict[str, list[dict]] = defaultdict(list)

    for h in hits:
        p  = h["product"]
        sg = p.get("swap_group") or f'__solo::{p["id"]}'
        cos = h["score"]
        group_sum[sg] += cos
        group_max[sg] = max(group_max.get(sg, float("-inf")), cos)
        group_hits[sg].append(h)

    return group_max, group_sum, group_hits


def _rank_swap_groups(
    group_max: dict[str, float],
    group_sum: dict[str, float],
    epsilon: float = _GROUP_RANK_EPSILON,
) -> list[str]:
    """Rank swap_groups by max cosine; sum-of-cosine tiebreak within epsilon."""
    def _compare(a: str, b: str) -> int:
        ma, mb = group_max[a], group_max[b]
        if abs(ma - mb) <= epsilon:
            sa, sb = group_sum[a], group_sum[b]
            if sa != sb:
                return -1 if sa > sb else 1
        if ma != mb:
            return -1 if ma > mb else 1
        return 0

    return sorted(group_max.keys(), key=cmp_to_key(_compare))


def _margin_runner_max(
    best_group: str,
    group_max: dict[str, float],
) -> tuple[float, str | None]:
    """Max-cosine of the margin runner-up group.

    Groups are sorted by max-cosine descending.  The runner is the group
    immediately after the winner in that order — i.e. the next-best group's
    max-cosine, NOT ranked[1] from the tiebreak ranking (which can be a
    spurious singleton whose single hit scored slightly above the winner).
    """
    by_max = sorted(group_max.keys(), key=lambda sg: -group_max[sg])
    try:
        idx = by_max.index(best_group)
    except ValueError:
        return 0.0, None
    if idx + 1 < len(by_max):
        runner = by_max[idx + 1]
        return group_max[runner], runner
    return 0.0, None


def resolve_ingredient(ingredient: str, k: int = RESOLVE_K) -> dict | None:
    """Map a free-text ingredient name to ONE real catalog product.

    Algorithm:
    1. Embed the ingredient text with Titan (normalize=True, dims=1024).
    2. k-NN search in OpenSearch (k=RESOLVE_K) → hits with true cosine scores.
    3. Group hits by swap_group; rank groups by MAX cosine (sum tiebreak within ε).
    4. Apply TWO numeric confidence gates in cosine space:
         (a) winner max-cosine >= SIM_FLOOR
         (b) winner max-cosine >= margin-runner max-cosine * RESOLVE_MARGIN
             (margin-runner = next group below winner in max-cosine order)
       If either gate fails → return None (caller puts ingredient in unmatched).
    5. Within the winning group: in-stock filter, then rank by cosine with small
       prime/rating boosts.

    Returns:
        {"swap_group": str, "product": dict, "alternatives": list[dict]}
        or None if confidence gates fail or OpenSearch is not configured.
    """
    if not _OS_ENDPOINT:
        log.info("resolve_ingredient(%r): UNMATCHED — OPENSEARCH_ENDPOINT not set", ingredient)
        return None
    try:
        vecs = embed([ingredient], "search_query")
        if not vecs or not vecs[0]:
            log.info("resolve_ingredient(%r): UNMATCHED — embed returned empty", ingredient)
            return None
        qvec = vecs[0]
        hits = _knn_search(qvec, k)
        if not hits:
            log.info("resolve_ingredient(%r): UNMATCHED — no kNN hits", ingredient)
            return None

        group_max, group_sum, group_hits = _group_hits_by_swap_group(hits)
        ranked_groups = _rank_swap_groups(group_max, group_sum)
        best_group = ranked_groups[0]
        best_sim   = group_max[best_group]
        runner_max, runner_group = _margin_runner_max(best_group, group_max)

        # Gate (a): absolute cosine floor
        if best_sim < SIM_FLOOR:
            log.info(
                "resolve_ingredient(%r): UNMATCHED — best_sim=%.4f < SIM_FLOOR=%.4f "
                "(would-be group=%r)",
                ingredient, best_sim, SIM_FLOOR, best_group,
            )
            return None

        # Gate (b): winner must clearly beat margin-runner on group max-cosine
        if runner_max > 0 and best_sim < runner_max * RESOLVE_MARGIN:
            log.info(
                "resolve_ingredient(%r): UNMATCHED — margin fail best_sim=%.4f "
                "runner_max=%.4f runner_group=%r MARGIN=%.2f (would-be group=%r)",
                ingredient, best_sim, runner_max, runner_group, RESOLVE_MARGIN, best_group,
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

        log.info(
            "resolve_ingredient(%r): MATCH swap_group=%r best_sim=%.4f product=%r",
            ingredient, best_group, best_sim, ranked[0]["product"].get("id"),
        )

        return {
            "swap_group":   best_group,
            "product":      ranked[0]["product"],
            "alternatives": [r["product"] for r in ranked[1:4]],
        }

    except Exception as exc:
        log.info("resolve_ingredient(%r): UNMATCHED — safe failure: %s", ingredient, exc)
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
    if total < 1000:
        raise RuntimeError(
            f"Refusing to build index: catalog has {total} products (expected >= 1000). "
            "Check MongoDB connection or products.json."
        )

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

    from opensearchpy import helpers

    def _actions():
        built = 0
        for p in products:
            text = product_embedding_text(p)
            vec  = embed_with_retry(text)

            yield {
                "_index": _OS_INDEX,
                "_id":    p["id"],
                "_source": {
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
                },
            }
            built += 1
            if built % 50 == 0 or built == total:
                print(f"  embedded {built}/{total}", flush=True)

    success, errors = helpers.bulk(
        client,
        _actions(),
        chunk_size=100,
        request_timeout=120,
        raise_on_error=True,
    )
    print(f"  bulk indexed {success} docs (errors: {errors})", flush=True)

    client.indices.refresh(index=_OS_INDEX)
    count = client.count(index=_OS_INDEX)["count"]
    print(f"\nTOTAL in index: {count}/{total}")
    if count >= total:
        print("ALL DONE ✅ (normalize=True, faiss+innerproduct)")
    else:
        print(f"⚠ Only {count}/{total} docs indexed — re-run to continue.")
        raise RuntimeError(f"Index incomplete: {count}/{total}")


if __name__ == "__main__":
    import sys
    print("Building OpenSearch index (delete + recreate + bulk ingest)...")
    print(f"  endpoint={_OS_ENDPOINT or '(not set)'}")
    print(f"  index={_OS_INDEX}  model={_EMBED_MODEL_ID}")
    try:
        build_index()
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
