#!/usr/bin/env python3
"""One-time export of product embedding vectors from OpenSearch to a local .npz file.

Scrolls all documents from the qcart-products index and saves:
  product_ids  — (N,) object array of catalog ids (e.g. p0001)
  embeddings   — (N, 1024) float32 matrix (Titan-normalized, as stored in OpenSearch)

Usage:
    cd qcart-ai/backend
    source venv/bin/activate
    python export_product_embeddings.py

Output:
    data/product_embeddings.npz
"""

from __future__ import annotations

import sys

import numpy as np
from dotenv import load_dotenv

load_dotenv()

import catalog


def main() -> None:
    if not catalog._OS_ENDPOINT:
        print("ERROR: OPENSEARCH_ENDPOINT not set.", file=sys.stderr)
        sys.exit(1)

    client = catalog._get_os_client()
    index = catalog._OS_INDEX
    out_path = catalog.LOCAL_EMBEDDINGS_PATH

    ids: list[str] = []
    vectors: list[list[float]] = []

    resp = client.search(
        index=index,
        scroll="2m",
        size=200,
        body={
            "_source": ["id", "embedding"],
            "query": {"match_all": {}},
        },
    )
    scroll_id = resp["_scroll_id"]
    hits = resp["hits"]["hits"]

    while hits:
        for h in hits:
            src = h.get("_source", {})
            emb = src.get("embedding")
            pid = src.get("id") or h.get("_id")
            if not pid or not emb or len(emb) != catalog.EMBED_DIM:
                print(f"  skip {pid!r}: missing or wrong-dim embedding", file=sys.stderr)
                continue
            ids.append(str(pid))
            vectors.append(emb)

        resp = client.scroll(scroll_id=scroll_id, scroll="2m")
        scroll_id = resp["_scroll_id"]
        hits = resp["hits"]["hits"]

    try:
        client.clear_scroll(scroll_id=scroll_id)
    except Exception:
        pass

    if not ids:
        print("ERROR: no embeddings exported.", file=sys.stderr)
        sys.exit(1)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out_path,
        product_ids=np.asarray(ids, dtype=object),
        embeddings=np.asarray(vectors, dtype=np.float32),
    )

    print(f"Wrote {len(ids)} vectors (dim={catalog.EMBED_DIM}) to {out_path}")
    print(f"  file size: {out_path.stat().st_size / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()
