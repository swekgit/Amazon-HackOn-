"""
Rainforest API Image Downloader — PASS 2
==========================================
Downloads product images from Amazon India via Rainforest API.

RESILIENT DESIGN:
  - If missing_products.json doesn't exist → uses full catalog
  - Auto-creates all required log/cache files
  - DRY_RUN mode for debugging without API calls
  - TEST_MODE to limit products processed
  - Immediate progress saves after each product
  - Full cache to prevent duplicate API calls
  - Graceful budget exhaustion handling

Dependencies:
  pip install requests rapidfuzz tqdm python-dotenv
"""

import json
import re
import time
import logging
import sys
from pathlib import Path
from datetime import datetime

import requests
from rapidfuzz import fuzz
from tqdm import tqdm

# Import centralized config
from config import (
    RAINFOREST_API_KEY,
    AMAZON_DOMAIN,
    IMAGE_FOLDER,
    LOG_FOLDER,
    PRODUCT_FILE,
    MAX_REQUESTS_PER_RUN,
    RATE_LIMIT_SECONDS,
    MAX_RETRIES,
    MIN_CONFIDENCE,
    DRY_RUN,
    TEST_MODE,
    TEST_PRODUCTS,
    validate_rainforest_key,
)

# ─── File Paths ───────────────────────────────────────────
MISSING_FILE = LOG_FOLDER / "missing_products.json"
DOWNLOADED_FILE = LOG_FOLDER / "downloaded_products.json"
CACHE_FILE = LOG_FOLDER / "rainforest_cache.json"
PROGRESS_FILE = LOG_FOLDER / "rainforest_progress.json"
RF_DOWNLOADED_FILE = LOG_FOLDER / "rainforest_downloaded.json"
RF_MISSING_FILE = LOG_FOLDER / "rainforest_missing.json"
FAILED_FILE = LOG_FOLDER / "rainforest_failed.json"
DEBUG_LOG = LOG_FOLDER / "rainforest_debug.log"

# ─── Rainforest API ──────────────────────────────────────
RAINFOREST_SEARCH_URL = "https://api.rainforestapi.com/request"

# ─── HTTP Session ─────────────────────────────────────────
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "QCartAI/1.0 (rainforest-image-pipeline)"
})

# ─── Ensure directories exist ─────────────────────────────
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
logger = logging.getLogger("rainforest")

# ─── Counters ─────────────────────────────────────────────
api_calls_this_run = 0


# ══════════════════════════════════════════════════════════
#  CACHE & PROGRESS MANAGEMENT
# ══════════════════════════════════════════════════════════

def load_json(path: Path, default=None):
    """Load a JSON file safely. Creates file with default if missing."""
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load {path}: {e}")
    # Auto-create if missing
    if default is not None:
        save_json(path, default)
    return default if default is not None else {}


def save_json(path: Path, data):
    """Save data as JSON atomically."""
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def load_cache() -> dict:
    """Load Rainforest response cache."""
    return load_json(CACHE_FILE, {})


def save_cache(cache: dict):
    save_json(CACHE_FILE, cache)


def load_progress() -> dict:
    """Load progress state for resumability."""
    return load_json(PROGRESS_FILE, {
        "processed_ids": [],
        "last_run": None,
        "total_api_calls": 0,
    })


def save_progress(progress: dict):
    progress["last_run"] = datetime.now().isoformat()
    save_json(PROGRESS_FILE, progress)


def load_downloaded_ids() -> list:
    """Load the global downloaded products list."""
    return load_json(DOWNLOADED_FILE, [])


def save_downloaded_ids(ids: list):
    save_json(DOWNLOADED_FILE, ids)


# ══════════════════════════════════════════════════════════
#  LOAD PRODUCTS (RESILIENT)
# ══════════════════════════════════════════════════════════

def load_products_to_process() -> list[dict]:
    """
    Load products that need processing.
    RESILIENT: If missing_products.json doesn't exist,
    falls back to the full catalog.
    """
    if MISSING_FILE.exists():
        missing = load_json(MISSING_FILE, [])
        if missing:
            logger.info(f"Loaded {len(missing)} products from missing_products.json")
            return missing

    # Fallback: load full catalog
    logger.warning("=" * 60)
    logger.warning("OpenFoodFacts results not found.")
    logger.warning("Processing complete catalog instead.")
    logger.warning("=" * 60)

    with open(PRODUCT_FILE, encoding="utf-8") as f:
        catalog = json.load(f)

    products = catalog["products"]

    # Convert to the format expected (minimal dict with id, name, brand, etc.)
    missing_format = []
    for p in products:
        missing_format.append({
            "id": p["id"],
            "name": p["name"],
            "brand": p.get("brand", ""),
            "category": p.get("category", ""),
            "swap_group": p.get("swap_group", ""),
        })

    # Save as missing_products.json for future runs
    save_json(MISSING_FILE, missing_format)
    logger.info(f"Created missing_products.json with {len(missing_format)} products")

    return missing_format


# ══════════════════════════════════════════════════════════
#  TEXT CLEANING & QUERY GENERATION
# ══════════════════════════════════════════════════════════

def clean_name(name: str) -> str:
    """Remove weights, packaging, parenthetical content."""
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"\d+\s?(kg|g|gm|ml|l|ltr|pcs|pc|pack|bags|pellets|sachets)\b", "", name, flags=re.I)
    name = re.sub(r"Pack of \d+", "", name, flags=re.I)
    name = re.sub(r"\bCombo\b", "", name, flags=re.I)
    return " ".join(name.split()).strip()


def build_queries(product: dict) -> list[str]:
    """
    Build search queries in decreasing specificity.
    IMPROVED: 5 query levels including category fallback.
    """
    brand = product.get("brand", "").strip()
    full_name = clean_name(product.get("name", ""))
    swap_group = product.get("swap_group", "").replace("_", " ").strip()
    category = product.get("category", "").replace("_", " ").strip()

    # Remove brand from name to avoid "Amul Amul..."
    name_no_brand = full_name
    if brand and full_name.lower().startswith(brand.lower()):
        name_no_brand = full_name[len(brand):].strip()

    queries = []

    # Q1: Brand + full cleaned name (most specific)
    if brand and name_no_brand:
        queries.append(f"{brand} {name_no_brand}")

    # Q2: Full cleaned name alone
    if full_name:
        queries.append(full_name)

    # Q3: Brand + swap_group (e.g., "Amul milk")
    if brand and swap_group:
        queries.append(f"{brand} {swap_group}")

    # Q4: swap_group alone (e.g., "milk")
    if swap_group:
        queries.append(swap_group)

    # Q5: category fallback (e.g., "dairy")
    if category and category != swap_group:
        queries.append(category)

    # Deduplicate preserving order
    seen = set()
    result = []
    for q in queries:
        q_key = q.lower().strip()
        if q_key and q_key not in seen:
            result.append(q)
            seen.add(q_key)

    return result


# ══════════════════════════════════════════════════════════
#  RAINFOREST API
# ══════════════════════════════════════════════════════════

def search_rainforest(query: str) -> list[dict]:
    """Search Amazon India via Rainforest API. Returns list of results."""
    global api_calls_this_run

    params = {
        "api_key": RAINFOREST_API_KEY,
        "type": "search",
        "amazon_domain": AMAZON_DOMAIN,
        "search_term": query,
        "output": "json",
    }

    for attempt in range(MAX_RETRIES):
        try:
            resp = SESSION.get(RAINFOREST_SEARCH_URL, params=params, timeout=30)
            api_calls_this_run += 1

            logger.debug(f"    API call #{api_calls_this_run} | HTTP {resp.status_code}")

            if resp.status_code == 200:
                data = resp.json()
                results = data.get("search_results", [])
                logger.debug(f"    OK — {len(results)} results returned")
                return results

            elif resp.status_code == 429:
                wait = (attempt + 1) * 10
                logger.warning(f"    Rate limited (429). Waiting {wait}s...")
                time.sleep(wait)
                continue

            elif resp.status_code == 401:
                logger.error("    INVALID API KEY (401).")
                return []

            elif resp.status_code == 403:
                logger.error("    FORBIDDEN (403). Key expired or quota exhausted.")
                return []

            else:
                logger.warning(f"    HTTP {resp.status_code}: {resp.text[:150]}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep((attempt + 1) * 3)
                continue

        except requests.exceptions.Timeout:
            logger.warning(f"    Timeout (attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep((attempt + 1) * 5)
        except requests.exceptions.ConnectionError as e:
            logger.error(f"    Connection error: {e}")
            time.sleep((attempt + 1) * 5)
        except Exception as e:
            logger.error(f"    Unexpected: {type(e).__name__}: {e}")
            break

    return []


# ══════════════════════════════════════════════════════════
#  MATCHING & SCORING
# ══════════════════════════════════════════════════════════

def compute_score(product: dict, result: dict) -> float:
    """Compute fuzzy match score between our product and a Rainforest result."""
    expected_name = clean_name(product.get("name", "")).lower()
    expected_brand = product.get("brand", "").lower()

    title = (result.get("title") or "").lower()
    link_brand = (result.get("brand") or "").lower()

    # Name similarity
    name_score = fuzz.token_set_ratio(expected_name, title)

    # Brand bonus
    brand_bonus = 0
    if expected_brand:
        if expected_brand in title or expected_brand in link_brand:
            brand_bonus = 25
        elif fuzz.partial_ratio(expected_brand, link_brand) > 80:
            brand_bonus = 15

    # Image availability bonus
    img_bonus = 5 if result.get("image") else 0

    score = min(100, name_score * 0.7 + brand_bonus + img_bonus)
    return score


def choose_best_result(product: dict, results: list[dict]) -> tuple:
    """Find the best matching result with an image."""
    best = None
    best_score = 0.0

    for r in results[:15]:
        if not r.get("image"):
            continue
        score = compute_score(product, r)
        if score > best_score:
            best_score = score
            best = r

    return best, best_score


# ══════════════════════════════════════════════════════════
#  IMAGE DOWNLOAD
# ══════════════════════════════════════════════════════════

def download_image(url: str, save_path: Path) -> bool:
    """Download image with validation and retry."""
    for attempt in range(MAX_RETRIES):
        try:
            resp = SESSION.get(url, timeout=30, stream=True)

            if resp.status_code != 200:
                logger.warning(f"    Image HTTP {resp.status_code}: {url[:80]}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2)
                continue

            tmp_path = save_path.with_suffix(".tmp")
            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Validate size
            size = tmp_path.stat().st_size
            if size < 500:
                logger.warning(f"    Image too small ({size} bytes), rejecting")
                tmp_path.unlink()
                continue

            # Validate JPEG header
            with open(tmp_path, "rb") as f:
                header = f.read(2)
            if header != b"\xff\xd8":
                logger.warning(f"    Not a valid JPEG (header: {header.hex()})")
                tmp_path.unlink()
                continue

            # Move to final path
            tmp_path.replace(save_path)
            return True

        except requests.exceptions.Timeout:
            logger.warning(f"    Download timeout (attempt {attempt + 1})")
            time.sleep(3)
        except requests.exceptions.ConnectionError:
            logger.warning(f"    Download connection error (attempt {attempt + 1})")
            time.sleep(5)
        except OSError as e:
            logger.error(f"    File write error: {e}")
            break
        except Exception as e:
            logger.error(f"    Download error: {type(e).__name__}: {e}")
            break

    # Cleanup
    tmp_path = save_path.with_suffix(".tmp")
    if tmp_path.exists():
        tmp_path.unlink()
    return False


# ══════════════════════════════════════════════════════════
#  PROCESS SINGLE PRODUCT
# ══════════════════════════════════════════════════════════

def process_product(product: dict, cache: dict, downloaded_ids: list) -> dict:
    """
    Process a single product. Returns result dict.
    Immediately persists progress on success.
    """
    global api_calls_this_run

    pid = product["id"]
    image_path = IMAGE_FOLDER / f"{pid}.jpg"

    # Skip if image already exists on disk
    if image_path.exists():
        logger.debug(f"[{pid}] SKIP — image already on disk")
        return {"id": pid, "status": "already_exists", "source": "disk"}

    # Skip if already in downloaded list
    if pid in downloaded_ids:
        logger.debug(f"[{pid}] SKIP — already in downloaded list")
        return {"id": pid, "status": "already_exists", "source": "list"}

    # Check cache — avoid duplicate API calls (Task 10)
    if pid in cache:
        cached = cache[pid]
        if cached.get("status") == "no_match":
            logger.debug(f"[{pid}] SKIP — cached as no_match (score: {cached.get('best_score', 0)})")
            return {"id": pid, "status": "cached_no_match", "score": cached.get("best_score", 0)}

        img_url = cached.get("image_url")
        if img_url and not cached.get("download_failed"):
            logger.info(f"[{pid}] Using cached URL: {img_url[:60]}...")
            if not DRY_RUN:
                success = download_image(img_url, image_path)
                if success:
                    # Immediately update downloaded list (Task 11)
                    downloaded_ids.append(pid)
                    save_downloaded_ids(downloaded_ids)
                    return {"id": pid, "status": "downloaded", "source": "cache", "url": img_url}
            else:
                logger.info(f"[{pid}] [DRY RUN] Would download from cache: {img_url[:60]}")
                return {"id": pid, "status": "dry_run", "source": "cache", "url": img_url}

    # DRY RUN mode — show queries without calling API (Task 7)
    queries = build_queries(product)
    if DRY_RUN:
        logger.info(f"[{pid}] [DRY RUN] {product.get('name', 'Unknown')}")
        logger.info(f"[{pid}]   Queries that WOULD be sent:")
        for i, q in enumerate(queries, 1):
            logger.info(f"[{pid}]     Q{i}: '{q}'")
        return {"id": pid, "status": "dry_run", "queries": queries}

    # Check API budget (Task 13)
    if api_calls_this_run >= MAX_REQUESTS_PER_RUN:
        return {"id": pid, "status": "budget_exhausted"}

    # Search via API
    logger.info(f"[{pid}] {product.get('name', 'Unknown')}")
    logger.debug(f"[{pid}]   Queries: {queries}")

    best_result = None
    best_score = 0.0
    best_query = ""

    for query in queries:
        if api_calls_this_run >= MAX_REQUESTS_PER_RUN:
            logger.warning(f"[{pid}] API budget exhausted mid-search")
            break

        logger.debug(f"[{pid}]   Searching: '{query}'")
        results = search_rainforest(query)
        time.sleep(RATE_LIMIT_SECONDS)

        if not results:
            continue

        # Log top results (Task 12)
        for i, r in enumerate(results[:5], 1):
            title = (r.get("title") or "?")[:50]
            has_img = "IMG" if r.get("image") else "---"
            sc = compute_score(product, r)
            asin = r.get("asin", "?")
            logger.debug(f"[{pid}]     #{i}: [{has_img}] ASIN:{asin} {title} (score:{sc:.0f})")

        result, score = choose_best_result(product, results)

        if result and score > best_score:
            best_result = result
            best_score = score
            best_query = query

        # Stop early if high confidence
        if best_score >= 70:
            break

    # Evaluate best match
    if not best_result or best_score < MIN_CONFIDENCE:
        reason = f"Best score {best_score:.0f} < {MIN_CONFIDENCE}" if best_result else "No results"
        logger.warning(f"[{pid}] MISS — {reason}")
        cache[pid] = {"status": "no_match", "best_score": best_score, "timestamp": datetime.now().isoformat()}
        save_cache(cache)
        return {"id": pid, "status": "no_match", "score": best_score, "reason": reason}

    # Download the image
    img_url = best_result.get("image", "")
    asin = best_result.get("asin", "")
    title = best_result.get("title", "")

    logger.info(f"[{pid}]   MATCH: '{title[:50]}' | ASIN: {asin} | Score: {best_score:.0f}")
    logger.info(f"[{pid}]   Image: {img_url[:80]}")

    success = download_image(img_url, image_path)

    if success:
        file_size = image_path.stat().st_size
        logger.info(f"[{pid}] ✓ DOWNLOADED ({file_size / 1024:.1f} KB)")

        # Cache success
        cache[pid] = {
            "asin": asin,
            "image_url": img_url,
            "query": best_query,
            "score": best_score,
            "title": title[:100],
            "downloaded": True,
            "timestamp": datetime.now().isoformat(),
        }
        save_cache(cache)

        # Immediately update downloaded list (Task 11)
        downloaded_ids.append(pid)
        save_downloaded_ids(downloaded_ids)

        return {"id": pid, "status": "downloaded", "source": "api", "asin": asin, "url": img_url, "score": best_score}
    else:
        logger.warning(f"[{pid}] FAIL — Image download failed")
        cache[pid] = {
            "asin": asin,
            "image_url": img_url,
            "query": best_query,
            "score": best_score,
            "download_failed": True,
            "timestamp": datetime.now().isoformat(),
        }
        save_cache(cache)
        return {"id": pid, "status": "download_failed", "url": img_url, "score": best_score}


# ══════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════

def main():
    global api_calls_this_run

    # Validate API key (skip in DRY_RUN)
    if not DRY_RUN and not validate_rainforest_key():
        logger.error("Exiting — no API key. Set DRY_RUN=true in .env to test without API.")
        sys.exit(1)

    # Load products (RESILIENT — Task 1)
    missing_products = load_products_to_process()

    if not missing_products:
        logger.info("No products to process!")
        sys.exit(0)

    # TEST_MODE: limit products (Task 8)
    if TEST_MODE:
        missing_products = missing_products[:TEST_PRODUCTS]
        logger.info(f"TEST MODE: Processing only first {TEST_PRODUCTS} products")

    # Load state (auto-creates if missing — Tasks 2-4)
    cache = load_cache()
    progress = load_progress()
    downloaded_ids = load_downloaded_ids()
    processed_ids = set(progress.get("processed_ids", []))

    # AUTO-REPAIR: If progress was polluted by a previous DRY_RUN bug,
    # remove IDs that were "processed" but have no image and no cache entry.
    # This ensures switching DRY_RUN off works correctly.
    if processed_ids:
        polluted = set()
        for pid in processed_ids:
            has_image = (IMAGE_FOLDER / f"{pid}.jpg").exists()
            has_cache = pid in cache
            has_download = pid in downloaded_ids
            if not has_image and not has_cache and not has_download:
                polluted.add(pid)
        if polluted:
            logger.warning(f"Auto-repair: Removing {len(polluted)} IDs from progress (DRY_RUN pollution)")
            processed_ids -= polluted
            progress["processed_ids"] = list(processed_ids)
            if not DRY_RUN:
                save_progress(progress)

    # Filter out already processed and already downloaded
    to_process = []
    for p in missing_products:
        pid = p["id"]
        if pid in processed_ids and pid in cache:
            continue
        if (IMAGE_FOLDER / f"{pid}.jpg").exists():
            continue
        if pid in downloaded_ids:
            continue
        to_process.append(p)

    logger.info("=" * 60)
    logger.info("QCart AI — Rainforest API Image Downloader (Pass 2)")
    logger.info("=" * 60)
    logger.info(f"Mode                     : {'DRY RUN' if DRY_RUN else 'TEST' if TEST_MODE else 'PRODUCTION'}")
    logger.info(f"Missing products loaded  : {len(missing_products)}")
    logger.info(f"Already processed        : {len(processed_ids)}")
    logger.info(f"Already downloaded       : {len(downloaded_ids)}")
    logger.info(f"To process this run      : {len(to_process)}")
    logger.info(f"API budget this run      : {MAX_REQUESTS_PER_RUN}")
    logger.info(f"Rate limit               : {RATE_LIMIT_SECONDS}s")
    logger.info(f"Min confidence           : {MIN_CONFIDENCE}")
    logger.info(f"Cache entries            : {len(cache)}")
    logger.info("=" * 60)

    if not to_process:
        logger.info("Nothing to process. All products attempted or downloaded.")
        sys.exit(0)

    # Process products
    results_downloaded = []
    results_missing = []
    results_failed = []
    budget_hit = False

    for product in tqdm(to_process, desc="Rainforest Pass 2", unit="product"):
        pid = product["id"]

        # Budget check (Task 13)
        if not DRY_RUN and api_calls_this_run >= MAX_REQUESTS_PER_RUN:
            logger.warning(f"\n{'=' * 60}")
            logger.warning(f"⚠ API quota exhausted ({MAX_REQUESTS_PER_RUN} calls used).")
            logger.warning(f"  Progress saved. Resume later by running this script again.")
            logger.warning(f"{'=' * 60}")
            budget_hit = True
            break

        result = process_product(product, cache, downloaded_ids)
        status = result["status"]

        # Track progress — NEVER in DRY_RUN mode
        if not DRY_RUN:
            processed_ids.add(pid)

        if status in ("downloaded", "already_exists"):
            results_downloaded.append(result)
        elif status == "download_failed":
            results_failed.append(result)
        elif status == "budget_exhausted":
            budget_hit = True
            break
        elif status == "dry_run":
            results_downloaded.append(result)  # count for display only
        else:
            results_missing.append(product)

        # Save progress immediately (Task 11) — NEVER in DRY_RUN
        if not DRY_RUN and (len(results_downloaded) % 5 == 0 or status == "downloaded"):
            progress["processed_ids"] = list(processed_ids)
            progress["total_api_calls"] = progress.get("total_api_calls", 0) + api_calls_this_run
            save_progress(progress)

    # ─── Final Save (SKIP entirely in DRY_RUN) ─────────────
    if not DRY_RUN:
        progress["processed_ids"] = list(processed_ids)
        progress["total_api_calls"] = progress.get("total_api_calls", 0) + api_calls_this_run
        save_progress(progress)
        save_cache(cache)

        # Save result files
        save_json(RF_DOWNLOADED_FILE, results_downloaded)
        save_json(RF_MISSING_FILE, results_missing)
        save_json(FAILED_FILE, results_failed)

        # Update missing_products.json — remove successfully downloaded (Task 11)
        all_missing = load_json(MISSING_FILE, [])
        remaining = [p for p in all_missing if not (IMAGE_FOLDER / f"{p['id']}.jpg").exists()]
        save_json(MISSING_FILE, remaining)
    else:
        remaining = load_json(MISSING_FILE, [])

    # ─── Summary ──────────────────────────────────────────
    logger.info(f"\n{'=' * 60}")
    logger.info("RAINFOREST PASS 2 — SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Mode              : {'DRY RUN' if DRY_RUN else 'LIVE'}")
    logger.info(f"Processed         : {len(results_downloaded) + len(results_missing) + len(results_failed)}")
    logger.info(f"Downloaded        : {len([r for r in results_downloaded if r.get('status') == 'downloaded'])}")
    logger.info(f"From cache        : {len([r for r in results_downloaded if r.get('source') == 'cache'])}")
    logger.info(f"Still missing     : {len(results_missing)}")
    logger.info(f"Failed downloads  : {len(results_failed)}")
    logger.info(f"API calls used    : {api_calls_this_run}")
    logger.info(f"Remaining         : {len(remaining)}")
    logger.info(f"Budget hit        : {'YES' if budget_hit else 'NO'}")
    logger.info("=" * 60)

    if budget_hit:
        logger.info("\n💡 Run this script again to continue processing.")
    elif results_missing:
        logger.info(f"\n💡 {len(results_missing)} products unmatched. Run: python fill_placeholders.py")


if __name__ == "__main__":
    main()
