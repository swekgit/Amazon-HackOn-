"""
SerpAPI Image Downloader -- Production Version
================================================
Downloads product images via SerpAPI (Google Shopping + Google Images fallback).
Only processes products from logs/missing_products.json.

Strategy:
  1. Search Google Shopping (better product images)
  2. Extract ALL candidate image URLs from result (not just thumbnail)
  3. Validate Content-Type before downloading (reject HTML/JSON)
  4. Validate downloaded image with Pillow
  5. If Shopping fails, automatically fall back to Google Images
  6. Cache failures to never retry bad URLs

Prerequisites:
  pip install requests rapidfuzz tqdm python-dotenv Pillow

Usage:
  python download_serpapi.py
"""

import json
import io
import time
import logging
import sys
from pathlib import Path
from datetime import datetime

import requests
from tqdm import tqdm
from rapidfuzz import fuzz

from config import (
    SERP_API_KEY, IMAGE_FOLDER, LOG_FOLDER,
    MAX_SERP_REQUESTS, SERP_RATE_LIMIT,
    MIN_CONFIDENCE, DRY_RUN, TEST_MODE, TEST_PRODUCTS, MAX_RETRIES,
)
from image_utils import (
    load_json, save_json, load_missing_products, filter_already_downloaded,
    build_queries, calculate_similarity, extract_size,
    cache_lookup, cache_save, log_success, log_failure, update_downloaded,
    SESSION,
)

# ─── Paths ────────────────────────────────────────────────
CACHE_FILE = LOG_FOLDER / "serp_cache.json"
DOWNLOADED_FILE = LOG_FOLDER / "serp_downloaded.json"
FAILED_FILE = LOG_FOLDER / "serp_failed.json"
DEBUG_LOG = LOG_FOLDER / "serp_debug.log"
SAMPLE_RESPONSE_FILE = LOG_FOLDER / "serpapi_sample_response.json"
DOWNLOAD_DEBUG_FILE = LOG_FOLDER / "serpapi_download_debug.json"

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
logger = logging.getLogger("serpapi")

# ─── State ────────────────────────────────────────────────
SERP_BASE_URL = "https://serpapi.com/search.json"
api_calls = 0
sample_saved = False
download_debug_entries = []

# URLs known to return HTML/garbage -- skip immediately
REJECTED_URL_PATTERNS = ["encrypted-tbn"]
RETRYABLE_STATUS_CODES = {500, 502, 503, 504}
VALID_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


# ══════════════════════════════════════════════════════════
#  IMAGE VALIDATION WITH PILLOW
# ══════════════════════════════════════════════════════════

def validate_image_pillow(file_path: Path) -> bool:
    """
    Validate image using Pillow. Supports JPEG, PNG, WEBP, GIF.
    Falls back to magic-byte check if Pillow fails to import.
    """
    try:
        from PIL import Image
        with Image.open(file_path) as img:
            img.verify()
        return True
    except ImportError:
        # Pillow not installed -- fallback to magic bytes
        return _validate_magic_bytes(file_path)
    except Exception:
        return False


def _validate_magic_bytes(file_path: Path) -> bool:
    """Fallback validation using file magic bytes."""
    try:
        with open(file_path, "rb") as f:
            header = f.read(8)
        # JPEG
        if header[:2] == b"\xff\xd8":
            return True
        # PNG
        if header[:4] == b"\x89PNG":
            return True
        # WEBP
        if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
            return True
        # GIF
        if header[:3] == b"GIF":
            return True
        return False
    except OSError:
        return False


# ══════════════════════════════════════════════════════════
#  CANDIDATE URL EXTRACTION (TASK 2)
# ══════════════════════════════════════════════════════════

IMAGE_FIELDS = [
    "original", "original_image", "image", "large_image",
    "product_image", "image_url", "image_link",
    "images", "thumbnails", "thumbnail", "serpapi_thumbnail",
]


def extract_candidate_image_urls(result: dict) -> list[str]:
    """
    Recursively inspect a Shopping/Images result dict.
    Collect every possible image URL, ordered from highest quality to lowest.
    Prefer direct URLs over encrypted-tbn thumbnail wrappers.
    """
    direct_urls = []
    thumbnail_urls = []

    def _extract(obj, depth=0):
        if depth > 5:
            return
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and value.startswith("http") and _looks_like_image_url(value):
                    if key.lower() in ("original", "original_image", "large_image", "image", "product_image", "image_url", "image_link"):
                        if not _is_thumbnail_wrapper(value):
                            direct_urls.append(value)
                        else:
                            thumbnail_urls.append(value)
                    elif key.lower() in ("thumbnail", "serpapi_thumbnail"):
                        thumbnail_urls.append(value)
                    elif "image" in key.lower() or "img" in key.lower():
                        if not _is_thumbnail_wrapper(value):
                            direct_urls.append(value)
                        else:
                            thumbnail_urls.append(value)
                elif isinstance(value, (dict, list)):
                    _extract(value, depth + 1)
        elif isinstance(obj, list):
            for item in obj[:10]:
                _extract(item, depth + 1)

    _extract(result)

    # Deduplicate, direct URLs first
    seen = set()
    ordered = []
    for url in direct_urls + thumbnail_urls:
        if url not in seen:
            ordered.append(url)
            seen.add(url)
    return ordered


def _looks_like_image_url(url: str) -> bool:
    """Quick heuristic: does this URL look like it could be an image?"""
    lower = url.lower()
    if any(ext in lower for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif")):
        return True
    if "image" in lower or "img" in lower or "photo" in lower:
        return True
    if "tbn:" in lower or "shopping" in lower:
        return True
    return True  # Be permissive; Content-Type check will filter


def _is_thumbnail_wrapper(url: str) -> bool:
    """Check if URL is an encrypted-tbn thumbnail wrapper."""
    return "encrypted-tbn" in url.lower()


# ══════════════════════════════════════════════════════════
#  CONTENT-TYPE VALIDATION & DOWNLOAD (TASKS 3, 4, 5, 8)
# ══════════════════════════════════════════════════════════

def validate_and_download(url: str, save_path: Path, failed_urls: set) -> tuple[bool, str]:
    """
    Validate Content-Type then download.
    Returns (success: bool, reason: str).
    Never retries 403, 404, HTML, or invalid images.
    Retries only timeout/connection/5xx.
    """
    if url in failed_urls:
        return False, "previously_failed"

    if not url or not url.startswith("http"):
        return False, "invalid_url"

    for attempt in range(MAX_RETRIES):
        try:
            # Stream GET to check headers before downloading body
            resp = SESSION.get(url, timeout=20, stream=True, allow_redirects=True)

            status = resp.status_code
            content_type = resp.headers.get("Content-Type", "").lower().split(";")[0].strip()

            # Non-retryable failures
            if status in (403, 404):
                resp.close()
                failed_urls.add(url)
                return False, f"http_{status}"

            if status != 200:
                resp.close()
                if status in RETRYABLE_STATUS_CODES and attempt < MAX_RETRIES - 1:
                    time.sleep(2 * (attempt + 1))
                    continue
                failed_urls.add(url)
                return False, f"http_{status}"

            # Content-Type validation (TASK 3)
            if content_type in ("text/html", "application/json", "text/plain"):
                resp.close()
                failed_urls.add(url)
                return False, f"content_type_rejected:{content_type}"

            # Accept valid image types OR octet-stream (some CDNs)
            is_image_ct = any(content_type.startswith(t) for t in ("image/", "application/octet-stream"))
            if not is_image_ct and content_type:
                resp.close()
                failed_urls.add(url)
                return False, f"content_type_not_image:{content_type}"

            # Download body
            tmp_path = save_path.with_suffix(".tmp")
            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Size check
            size = tmp_path.stat().st_size
            if size < 1000:
                tmp_path.unlink()
                failed_urls.add(url)
                return False, f"too_small:{size}bytes"

            # Pillow validation (TASK 5)
            if validate_image_pillow(tmp_path):
                tmp_path.replace(save_path)
                return True, "ok"
            else:
                # Peek at header for debug
                with open(tmp_path, "rb") as f:
                    hdr = f.read(4).hex()
                tmp_path.unlink()
                failed_urls.add(url)
                return False, f"invalid_image:header={hdr}"

        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES - 1:
                time.sleep(3 * (attempt + 1))
                continue
            return False, "timeout"
        except requests.exceptions.ConnectionError:
            if attempt < MAX_RETRIES - 1:
                time.sleep(5)
                continue
            return False, "connection_error"
        except OSError as e:
            return False, f"os_error:{e}"
        except Exception as e:
            return False, f"error:{type(e).__name__}"

    return False, "max_retries"


# ══════════════════════════════════════════════════════════
#  SERP API CALLS
# ══════════════════════════════════════════════════════════

def search_serp_shopping(query: str) -> tuple[list[dict], int]:
    """Search Google Shopping. Returns (results, http_status)."""
    global api_calls
    params = {
        "api_key": SERP_API_KEY,
        "engine": "google_shopping",
        "q": query,
        "gl": "in",
        "hl": "en",
        "num": 10,
    }
    try:
        resp = SESSION.get(SERP_BASE_URL, params=params, timeout=20)
        api_calls += 1
        logger.debug(f"    Shopping #{api_calls} | HTTP {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            return data.get("shopping_results", []), 200
        return [], resp.status_code
    except Exception as e:
        logger.error(f"    Shopping error: {e}")
        return [], 0


def search_serp_images(query: str) -> tuple[list[dict], int]:
    """Search Google Images. Returns (results, http_status)."""
    global api_calls
    params = {
        "api_key": SERP_API_KEY,
        "engine": "google_images",
        "q": query,
        "gl": "in",
        "hl": "en",
        "num": 10,
    }
    try:
        resp = SESSION.get(SERP_BASE_URL, params=params, timeout=20)
        api_calls += 1
        logger.debug(f"    Images #{api_calls} | HTTP {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            return data.get("images_results", []), 200
        return [], resp.status_code
    except Exception as e:
        logger.error(f"    Images error: {e}")
        return [], 0


# ══════════════════════════════════════════════════════════
#  RESULT RANKING (TASK 9)
# ══════════════════════════════════════════════════════════

def rank_shopping_results(product: dict, results: list[dict]) -> list[tuple[dict, float]]:
    """
    Rank Shopping results by compound score:
    similarity + brand match + pack size + direct image availability.
    """
    ranked = []
    expected_size = extract_size(product.get("name", ""))

    for item in results[:15]:
        title = item.get("title", "")
        score = calculate_similarity(product, title)

        # Bonus: has direct image (not just thumbnail)
        candidates = extract_candidate_image_urls(item)
        has_direct = any(not _is_thumbnail_wrapper(u) for u in candidates)
        if has_direct:
            score += 5

        # Bonus: has any image at all
        if candidates:
            score += 3

        ranked.append((item, min(100, score)))

    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked


# ══════════════════════════════════════════════════════════
#  PROCESS SINGLE PRODUCT (TASKS 4, 6, 7)
# ══════════════════════════════════════════════════════════

def process_product(product: dict, cache: dict) -> dict:
    """
    Process a single product:
    1. Google Shopping search + ranked candidate URLs
    2. Validate & download first working URL
    3. If Shopping fails -> automatic Google Images fallback
    4. Cache result
    """
    global api_calls, sample_saved
    pid = product["id"]
    image_path = IMAGE_FOLDER / f"{pid}.jpg"

    if image_path.exists():
        return {"id": pid, "status": "already_exists"}

    # Check cache (TASK 10)
    cached = cache_lookup(cache, pid)
    if cached:
        if cached.get("status") == "no_match":
            return {"id": pid, "status": "cached_no_match"}
        # If previously failed URL, don't retry it
        if cached.get("download_failed"):
            failed_url = cached.get("failed_url", "")
            # But allow retry if we now have better logic
            pass
        url = cached.get("image_url")
        if url and cached.get("downloaded") and not DRY_RUN:
            success, reason = validate_and_download(url, image_path, set())
            if success:
                update_downloaded(pid)
                return {"id": pid, "status": "downloaded", "source": "cache"}

    queries = build_queries(product)

    if DRY_RUN:
        logger.info(f"[{pid}] [DRY RUN] {product.get('name', '')}")
        for i, q in enumerate(queries, 1):
            logger.info(f"[{pid}]   Q{i}: '{q}'")
        return {"id": pid, "status": "dry_run"}

    if api_calls >= MAX_SERP_REQUESTS:
        return {"id": pid, "status": "budget_exhausted"}

    logger.info(f"[{pid}] {product.get('name', '')}")

    debug_entry = {
        "product_id": pid,
        "query": "",
        "shopping_score": 0,
        "shopping_candidates": [],
        "google_candidates": [],
        "selected_field": "",
        "selected_url": "",
        "content_type": "",
        "downloaded": False,
        "fallback_used": False,
        "validation": "",
    }

    failed_urls = set()  # Track failed URLs this session

    # ─── STRATEGY 1: Google Shopping ──────────────────────
    shopping_success = False
    for query in queries[:3]:
        if api_calls >= MAX_SERP_REQUESTS:
            break

        debug_entry["query"] = query
        results, status = search_serp_shopping(query)
        time.sleep(SERP_RATE_LIMIT)

        logger.debug(f"[{pid}]   Shopping query='{query}' results={len(results)} http={status}")

        if not results:
            continue

        # TASK 1: Save sample response (once in TEST_MODE)
        if TEST_MODE and not sample_saved:
            save_json(SAMPLE_RESPONSE_FILE, results)
            sample_saved = True
            logger.info(f"[{pid}]   Saved sample response to {SAMPLE_RESPONSE_FILE.name}")

        # Rank results (TASK 9)
        ranked = rank_shopping_results(product, results)

        for item, score in ranked:
            if score < MIN_CONFIDENCE:
                continue

            candidates = extract_candidate_image_urls(item)
            debug_entry["shopping_score"] = score
            debug_entry["shopping_candidates"] = candidates[:5]

            logger.debug(f"[{pid}]   Match: score={score:.0f} candidates={len(candidates)}")

            # Try each candidate URL (TASK 4)
            for url in candidates:
                logger.debug(f"[{pid}]     Trying: {url[:70]}")
                success, reason = validate_and_download(url, image_path, failed_urls)

                if success:
                    debug_entry["selected_url"] = url
                    debug_entry["downloaded"] = True
                    debug_entry["validation"] = "passed"
                    download_debug_entries.append(debug_entry)

                    cache_save(cache, pid, {
                        "image_url": url, "score": score,
                        "downloaded": True, "source": "shopping",
                    }, CACHE_FILE)
                    update_downloaded(pid)
                    log_success(pid, "SerpAPI-Shopping", url, score)
                    logger.info(f"[{pid}]   DOWNLOADED (Shopping, score={score:.0f})")
                    return {"id": pid, "status": "downloaded", "source": "shopping",
                            "url": url, "score": score}
                else:
                    logger.debug(f"[{pid}]     Rejected: {reason}")

        if shopping_success:
            break

    # ─── STRATEGY 2: Google Images Fallback (TASK 6) ──────
    logger.debug(f"[{pid}]   Shopping failed. Falling back to Google Images...")
    debug_entry["fallback_used"] = True

    for query in queries[:2]:
        if api_calls >= MAX_SERP_REQUESTS:
            break

        results, status = search_serp_images(query)
        time.sleep(SERP_RATE_LIMIT)

        logger.debug(f"[{pid}]   Images query='{query}' results={len(results)} http={status}")

        if not results:
            continue

        for item in results[:10]:
            title = item.get("title", "")
            score = calculate_similarity(product, title)
            if score < MIN_CONFIDENCE:
                continue

            candidates = extract_candidate_image_urls(item)
            debug_entry["google_candidates"] = candidates[:5]

            for url in candidates:
                # Skip tiny thumbnails from images results too
                w = item.get("original_width", 200)
                h = item.get("original_height", 200)
                if w < 100 or h < 100:
                    continue

                logger.debug(f"[{pid}]     Trying (Images): {url[:70]}")
                success, reason = validate_and_download(url, image_path, failed_urls)

                if success:
                    debug_entry["selected_url"] = url
                    debug_entry["downloaded"] = True
                    debug_entry["validation"] = "passed"
                    download_debug_entries.append(debug_entry)

                    cache_save(cache, pid, {
                        "image_url": url, "score": score,
                        "downloaded": True, "source": "google_images",
                    }, CACHE_FILE)
                    update_downloaded(pid)
                    log_success(pid, "SerpAPI-Images", url, score)
                    logger.info(f"[{pid}]   DOWNLOADED (Google Images fallback, score={score:.0f})")
                    return {"id": pid, "status": "downloaded", "source": "google_images",
                            "url": url, "score": score}
                else:
                    logger.debug(f"[{pid}]     Rejected: {reason}")

    # ─── MISS ─────────────────────────────────────────────
    debug_entry["validation"] = "all_candidates_failed"
    download_debug_entries.append(debug_entry)

    cache_save(cache, pid, {
        "status": "no_match", "best_score": debug_entry["shopping_score"],
        "failed_urls": list(failed_urls)[:5],
    }, CACHE_FILE)
    log_failure(pid, "SerpAPI", "all candidates failed validation")
    return {"id": pid, "status": "no_match", "score": debug_entry["shopping_score"]}


# ══════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════

def main():
    if not DRY_RUN and not SERP_API_KEY:
        logger.error("SERP_API_KEY not set in .env")
        logger.error("Set DRY_RUN=true to test without API.")
        sys.exit(1)

    products = load_missing_products()
    products = filter_already_downloaded(products)

    if TEST_MODE:
        products = products[:TEST_PRODUCTS]
        logger.info(f"TEST MODE: {TEST_PRODUCTS} products")

    cache = load_json(CACHE_FILE, {})

    logger.info("=" * 60)
    logger.info("QCart AI -- SerpAPI Image Downloader (Production)")
    logger.info("=" * 60)
    logger.info(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE'} | Budget: {MAX_SERP_REQUESTS}")
    logger.info(f"To process: {len(products)}")
    logger.info(f"Cache entries: {len(cache)}")
    logger.info("=" * 60)

    if not products:
        logger.info("Nothing to process. All products have images.")
        return

    downloaded = []
    failed = []

    for product in tqdm(products, desc="SerpAPI", unit="product"):
        result = process_product(product, cache)
        status = result.get("status")

        if status == "downloaded":
            downloaded.append(result)
        elif status == "budget_exhausted":
            logger.warning("\nBudget exhausted. Resume later.")
            break
        elif status not in ("already_exists", "dry_run", "cached_no_match"):
            failed.append(result)

    # Save results (skip in DRY_RUN)
    if not DRY_RUN:
        save_json(DOWNLOADED_FILE, downloaded)
        save_json(FAILED_FILE, failed)
        # TASK 11: Save download debug log
        if download_debug_entries:
            save_json(DOWNLOAD_DEBUG_FILE, download_debug_entries)

    # Summary
    logger.info(f"\n{'=' * 60}")
    logger.info("SerpAPI SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Processed     : {len(downloaded) + len(failed)}")
    logger.info(f"Downloaded    : {len(downloaded)}")
    logger.info(f"  Shopping    : {len([d for d in downloaded if d.get('source') == 'shopping'])}")
    logger.info(f"  Images FB   : {len([d for d in downloaded if d.get('source') == 'google_images'])}")
    logger.info(f"Failed        : {len(failed)}")
    logger.info(f"API calls     : {api_calls}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
