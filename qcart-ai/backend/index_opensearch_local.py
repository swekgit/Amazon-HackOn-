"""index_opensearch_local.py — build the OpenSearch vector index using LOCAL embeddings
(sentence-transformers). No AWS Bedrock, no throttling, unlimited.

Model : all-MiniLM-L6-v2  → 384-dim vectors.

IMPORTANT: the backend query path MUST use the SAME model (catalog.py _embed()),
otherwise kNN results are garbage.

Run:
    pip install sentence-transformers opensearch-py requests-aws4auth boto3
    python index_opensearch_local.py        # resumable: re-run to continue

Optional (index only first N products for a quick smoke-test):
    $env:INDEX_LIMIT="50"
    python index_opensearch_local.py
"""

import os

import boto3
from dotenv import load_dotenv
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from sentence_transformers import SentenceTransformer

import catalog

load_dotenv()

OS_ENDPOINT = (
    os.getenv(
        "OPENSEARCH_ENDPOINT",
        "search-qcart-search-1-sibhz5mutsifc6hbccuw6has3u.us-east-1.es.amazonaws.com",
    )
    .replace("https://", "")
    .strip("/")
)
OS_INDEX  = os.getenv("OPENSEARCH_INDEX", "qcart-products")
OS_REGION = os.getenv("OPENSEARCH_REGION", "us-east-1")
DIM       = 384  # all-MiniLM-L6-v2

# ── OpenSearch auth (AWS creds for domain auth — NOT used for embeddings) ──────
session = boto3.Session()
creds   = session.get_credentials()
awsauth = AWS4Auth(
    creds.access_key,
    creds.secret_key,
    OS_REGION,
    "es",
    session_token=creds.token,
)

client = OpenSearch(
    hosts=[{"host": OS_ENDPOINT, "port": 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
    timeout=30,
)

print("Loading local embedding model (all-MiniLM-L6-v2)...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("Model loaded.")


def product_text(p: dict) -> str:
    tags = " ".join(p.get("tags", []))
    return f"{p['name']} {p.get('brand', '')} {p['category']} {tags}".strip()


def ensure_index():
    if client.indices.exists(index=OS_INDEX):
        cnt = client.count(index=OS_INDEX)["count"]
        # If existing index has WRONG dimension, we must recreate it
        try:
            mp  = client.indices.get_mapping(index=OS_INDEX)
            dim = mp[OS_INDEX]["mappings"]["properties"]["embedding"]["dimension"]
        except Exception:
            dim = None

        if dim != DIM:
            print(f"Existing index dim={dim} != {DIM}. Deleting and recreating.")
            client.indices.delete(index=OS_INDEX)
        else:
            print(f"Index exists with {cnt} docs (dim {DIM}) — resuming.")
            return

    body = {
        "settings": {"index": {"knn": True}},
        "mappings": {
            "properties": {
                "id":         {"type": "keyword"},
                "name":       {"type": "text"},
                "category":   {"type": "keyword"},
                "swap_group": {"type": "keyword"},
                "brand":      {"type": "keyword"},
                "price":      {"type": "float"},
                "tags":       {"type": "keyword"},
                "embedding":  {"type": "knn_vector", "dimension": DIM},
            }
        },
    }
    client.indices.create(index=OS_INDEX, body=body)
    print(f"Created index '{OS_INDEX}' (knn_vector dim={DIM}).")


def already_indexed() -> set:
    ids = set()
    try:
        resp = client.search(
            index=OS_INDEX,
            body={
                "size": 10000,
                "_source": ["id"],
                "query": {"match_all": {}},
            },
        )
        ids = {h["_source"]["id"] for h in resp["hits"]["hits"]}
    except Exception:
        pass
    return ids


def main():
    products = catalog.get_catalog()

    lim = os.getenv("INDEX_LIMIT", "").strip()
    if lim.isdigit():
        products = products[: int(lim)]

    print(f"Catalog: {len(products)} products")

    ensure_index()

    done = already_indexed()
    todo = [p for p in products if p["id"] not in done]
    print(f"Already indexed: {len(done)} | To do: {len(todo)}")

    # Embed in batches — local model is fast, no throttle
    B  = 64
    ok = 0
    for start in range(0, len(todo), B):
        batch = todo[start : start + B]
        texts = [product_text(p) for p in batch]
        vecs  = model.encode(texts, normalize_embeddings=True).tolist()

        for p, v in zip(batch, vecs):
            client.index(
                index=OS_INDEX,
                id=p["id"],
                body={
                    "id":         p["id"],
                    "name":       p["name"],
                    "category":   p["category"],
                    "swap_group": p.get("swap_group"),
                    "brand":      p.get("brand", ""),
                    "price":      p["price"],
                    "tags":       p.get("tags", []),
                    "embedding":  v,
                },
            )
            ok += 1
            print(f"  indexed {ok}/{len(todo)}", flush=True)

    client.indices.refresh(index=OS_INDEX)
    total = client.count(index=OS_INDEX)["count"]
    print(f"\nTOTAL in index: {total}/{len(catalog.get_catalog())}")
    print("ALL DONE ✅" if total >= len(products) else "⚠ Re-run to continue.")


if __name__ == "__main__":
    main()
