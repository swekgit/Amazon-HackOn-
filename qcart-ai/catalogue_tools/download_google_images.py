"""
Google Custom Search Image Downloader — PASS 3
================================================
Downloads product images via Google Custom Search JSON API.
Only processes products from logs/missing_products.json.

Prerequisites:
  pip install requests rapidfuzz tqdm python-dotenv
  Set GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID in .env

Usage:
  python download_google_images.py
"""

import json
import time
import logging
import sys
from pathlib import Path
from datetime import datetime

import requests
from tqdm import tqdm

from config import (
    GOOGLE_API_KEY, GOOGLE_SEARCH_ENGINE_ID,
    IMAGE_FOLDER, LOG_FOLDER,
    MAX_GOOGLE_REQUESTS, GOOGLE_RATE_LIMIT,
    MIN_CONFIDENCE, DRY_RUN, TEST_MODE, TEST_PRODUCTS,
)
from image_utils import (
    load_json, save_json, load_missing_products, filter_already_downloaded,
    build_queries, calculate_similarity, download_image, validate_image,
    cache_lookup, cache_save, log_success, log_failure, update_downloaded,
    SESSION,
)

# ─── Paths ────────────────────────────────────────────────
CACHE_FILE = LOG_FOLDER / "google_cache.json"
DOWNLOADED_FILE = LOG_FOLDER / "google_downloaded.json"
FAILED_FILE = LOG_FOLDER / "google_failed.json"
DEBUG_LOG = LOG_FOLDER / "google_debug.log"

IMAGE_FOLDER.mkdir(exist_ok=True)
LOG_FOLDER.mkdir(exist_ok=True)

# ─── Logging ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(DEBUG_LOG, mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger("google_images")

# ─── API ──────────────────────────────────────────────────
GOOGLE_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
api_calls = 0


def search_google(query: str) -> list[dict]:
    """Search Google Custom Search for images. Returns list of items."""
    global api_calls

    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_SEARCH_ENGINE_ID,
        "q": query,
        "searchType": "image",
        "imgSize": "large",
        "num": 10,
    }

    try:
        resp = SESSION.get(GOOGLE_SEARCH_URL, params=params, timeout=20)
        api_calls += 1
        logger.debug(f"    Google API #{api_calls} | HTTP {resp.status_code}")

        if resp.status_code == 200:
            return resp.json().get("items", [])
        elif resp.status_code == 429:
            logger.warning("    Google rate limited (429)")
            return []
        elif resp.status_code == 403:
            logger.error("    Google API quota exceeded or invalid key (403)")
            return []
        else:
            logger.warning(f"    Google HTTP {resp.status_code}")
            return []
    except Exception as e:
        logger.error(f"    Google API error: {type(e).__name__}: {e}")
        return []


def process_product(product: dict, cache: dict) -> dict:
    """Process a single product via Google Custom Search."""
    global api_calls
    pid = product["id"]
    image_path = IMAGE_FOLDER / f"{pid}.jpg"

    if image_path.exists():
        return {"id": pid, "status": "already_exists"}

    # Check cache
    cached = cache_lookup(cache, pid)
    if cached:
        if cached.get("status") == "no_match":
            return {"id": pid, "status": "cached_no_match"}
        url = cached.get("image_url")
        if url and not DRY_RUN:
            if download_image(url, image_path):
                update_downloaded(pid)
                return {"id": pid, "status": "downloaded", "source": "cache"}

    queries = build_queries(product)

    if DRY_RUN:
        logger.info(f"[{pid}] [DRY RUN] {product.get('name', '')}")
        for i, q in enumerate(queries, 1):
            logger.info(f"[{pid}]   Q{i}: '{q}'")
        return {"id": pid, "status": "dry_run"}

    if api_calls >= MAX_GOOGLE_REQUESTS:
        return {"id": pid, "status": "budget_exhausted"}

    logger.info(f"[{pid}] {product.get('name', '')}")
    best_url = None
    best_score = 0.0

    for query in queries:
        if api_calls >= MAX_GOOGLE_REQUESTS:
            break

        results = search_google(query)
        time.sleep(GOOGLE_RATE_LIMIT)

        if not results:
            continue

        for item in results[:10]:
            title = item.get("title", "")
            link = item.get("link", "")
            score = calculate_similarity(product, title)

            if score > best_score and link:
                best_score = score
                best_url = link

        if best_score >= 70:
            break

    if not best_url or best_score < MIN_CONFIDENCE:
        cache_save(cache, pid, {"status": "no_match", "best_score": best_score}, CACHE_FILE)
        log_failure(pid, "Google", f"score {best_score:.0f} < {MIN_CONFIDENCE}")
        return {"id": pid, "status": "no_match", "score": best_score}

    logger.info(f"[{pid}]   Best: score={best_score:.0f} url={best_url[:60]}")
    success = download_image(best_url, image_path)

    if success:
        cache_save(cache, pid, {"image_url": best_url, "score": best_score, "downloaded": True}, CACHE_FILE)
        update_downloaded(pid)
        log_success(pid, "Google", best_url, best_score)
        return {"id": pid, "status": "downloaded", "url": best_url, "score": best_score}
    else:
        cache_save(cache, pid, {"image_url": best_url, "score": best_score, "download_failed": True}, CACHE_FILE)
        log_failure(pid, "Google", "download failed")
        return {"id": pid, "status": "download_failed"}


def main():
    if not DRY_RUN and (not GOOGLE_API_KEY or not GOOGLE_SEARCH_ENGINE_ID):
        logger.error("GOOGLE_API_KEY or GOOGLE_SEARCH_ENGINE_ID not set in .env")
        logger.error("Set DRY_RUN=true to test without API.")
        sys.exit(1)

    products = load_missing_products()
    products = filter_already_downloaded(products)

    if TEST_MODE:
        products = products[:TEST_PRODUCTS]
        logger.info(f"TEST MODE: {TEST_PRODUCTS} products")

    cache = load_json(CACHE_FILE, {})

    logger.info("=" * 60)
    logger.info("QCart AI -- Google Custom Search (Pass 3)")
    logger.info("=" * 60)
    logger.info(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE'} | Budget: {MAX_GOOGLE_REQUESTS}")
    logger.info(f"To process: {len(products)}")
    logger.info("=" * 60)

    if not products:
        logger.info("Nothing to process.")
        return

    downloaded = []
    failed = []

    for product in tqdm(products, desc="Google Pass 3", unit="product"):
        result = process_product(product, cache)
        if result["status"] == "downloaded":
            downloaded.append(result)
        elif result["status"] == "budget_exhausted":
            logger.warning("Budget exhausted. Resume later.")
            break
        elif result["status"] not in ("already_exists", "dry_run", "cached_no_match"):
            failed.append(result)

    if not DRY_RUN:
        save_json(DOWNLOADED_FILE, downloaded)
        save_json(FAILED_FILE, failed)

    logger.info(f"\nGoogle Pass 3: Downloaded={len(downloaded)} Failed={len(failed)} API calls={api_calls}")


if __name__ == "__main__":
    main()
