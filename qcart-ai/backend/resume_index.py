"""resume_index.py — index only the products not yet in OpenSearch."""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))
from dotenv import load_dotenv; load_dotenv()
import catalog

client = catalog._get_os_client()
products = catalog.get_catalog()
total    = len(products)

# Find already-indexed IDs
resp = client.search(
    index=catalog._OS_INDEX,
    body={"size": 10000, "_source": ["id"], "query": {"match_all": {}}},
)
indexed_ids = {h["_source"]["id"] for h in resp["hits"]["hits"]}
todo = [p for p in products if p["id"] not in indexed_ids]
print(f"Already indexed: {len(indexed_ids)}/{total}  |  Remaining: {len(todo)}")

def embed_with_retry(text, max_tries=5):
    delay = 0.5
    for attempt in range(max_tries):
        try:
            return catalog.embed([text], "search_document")[0]
        except Exception as e:
            if "ThrottlingException" in type(e).__name__ or "throttl" in str(e).lower():
                if attempt < max_tries - 1:
                    print(f"  Throttled — retrying in {delay:.1f}s ...", flush=True)
                    time.sleep(delay); delay = min(delay * 2, 8.0)
                else:
                    raise
            else:
                raise

ok = 0
for p in todo:
    vec = embed_with_retry(catalog.product_embedding_text(p))
    doc = {
        "id": p["id"], "name": p["name"], "category": p["category"],
        "swap_group": p.get("swap_group"), "brand": p.get("brand", ""),
        "price": p.get("price", 0), "rating": p.get("rating"),
        "prime_eligible": p.get("prime_eligible", False),
        "stock_status": p.get("stock_status", "in_stock"),
        "tags": p.get("tags", []), "embedding": vec,
    }
    client.index(index=catalog._OS_INDEX, id=p["id"], body=doc)
    ok += 1
    if ok % 10 == 0 or ok == len(todo):
        print(f"  indexed {ok}/{len(todo)}", flush=True)

client.indices.refresh(index=catalog._OS_INDEX)
count = client.count(index=catalog._OS_INDEX)["count"]
print(f"\nTOTAL in index: {count}/{total}")
print("ALL DONE ✅" if count >= total else f"⚠ Still missing {total - count} docs — re-run")
