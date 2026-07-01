"""
OpenFoodFacts Image Downloader for QCart AI
============================================
Downloads product images from OpenFoodFacts using fuzzy matching.
Saves images as images/p0001.jpg, images/p0002.jpg, etc.

Debug mode: prints detailed info for every search attempt.
"""

import json
import re
import time
import logging
import sys
from pathlib import Path

import requests
from rapidfuzz import fuzz
from tqdm import tqdm

# ---------------- CONFIG ---------------- #

PRODUCT_FILE = "products.json"
IMAGE_FOLDER = Path("images")
LOG_FOLDER = Path("logs")

IMAGE_FOLDER.mkdir(exist_ok=True)
LOG_FOLDER.mkdir(exist_ok=True)

# OpenFoodFacts search endpoint
SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"

# Minimum fuzzy score to accept a match (0-100)
MIN_CONFIDENCE = 50

# Rate limit: seconds between API calls
RATE_LIMIT = 1.0

# Max products to process (set to None for all)
MAX_PRODUCTS = None

# HTTP session with User-Agent (OpenFoodFacts requires this)
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "QCartAI/1.0 (image-downloader; contact@qcart.ai)"
})

# ---------------- LOGGING --------------- #

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FOLDER / "download_debug.log", mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------- #


def clean_name(name: str) -> str:
    """Remove weights, packaging info, and parenthetical text."""
    # Remove parenthetical content: (500ml), (1L), etc.
    name = re.sub(r"\(.*?\)", "", name)
    # Remove standalone weights: 500g, 1kg, 200ml, etc.
    name = re.sub(r"\d+\s?(kg|g|gm|ml|l|ltr|pcs|pc|pack|bags|pellets|sachets)\b", "", name, flags=re.I)
    # Remove "Pack of N"
    name = re.sub(r"Pack of \d+", "", name, flags=re.I)
    # Remove "Combo"
    name = re.sub(r"\bCombo\b", "", name, flags=re.I)
    # Collapse whitespace
    return " ".join(name.split()).strip()


def build_queries(product: dict) -> list[str]:
    """
    Build multiple search queries in decreasing specificity.
    Strategy:
      1. "Brand ProductName" (cleaned)
      2. ProductName only (cleaned)
      3. "Brand Category" (e.g., "Amul Milk")
      4. swap_group generic (e.g., "milk", "bread")
    """
    brand = product.get("brand", "").strip()
    full_name = clean_name(product["name"])
    category = product.get("category", "").strip()
    swap_group = product.get("swap_group", "").replace("_", " ").strip()

    # Remove brand prefix from name to avoid "Amul Amul Taaza..."
    name_without_brand = full_name
    if brand and full_name.lower().startswith(brand.lower()):
        name_without_brand = full_name[len(brand):].strip()

    queries = []

    # Query 1: brand + cleaned name (most specific)
    if brand and name_without_brand:
        queries.append(f"{brand} {name_without_brand}")

    # Query 2: just the cleaned full name
    if full_name:
        queries.append(full_name)

    # Query 3: cleaned name without brand (if different from full_name)
    if name_without_brand and name_without_brand != full_name:
        queries.append(name_without_brand)

    # Query 4: brand + swap_group (e.g., "Amul butter")
    if brand and swap_group:
        queries.append(f"{brand} {swap_group}")

    # Query 5: just the swap_group (most generic fallback)
    if swap_group:
        queries.append(swap_group)

    # Deduplicate preserving order
    seen = set()
    final = []
    for q in queries:
        q_lower = q.lower().strip()
        if q_lower and q_lower not in seen:
            final.append(q)
            seen.add(q_lower)

    return final


def search_openfoodfacts(query: str) -> list[dict]:
    """Search OpenFoodFacts. Returns list of product dicts."""
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 20,
        "fields": "product_name,brands,image_front_url,image_url,categories_tags,code",
    }

    try:
        resp = SESSION.get(SEARCH_URL, params=params, timeout=20)
        logger.debug(f"  API Status: {resp.status_code} | URL: {resp.url}")

        if resp.status_code != 200:
            logger.warning(f"  HTTP {resp.status_code} for query '{query}'")
            return []

        data = resp.json()
        products = data.get("products", [])
        return products

    except requests.exceptions.Timeout:
        logger.error(f"  TIMEOUT for query '{query}'")
        return []
    except requests.exceptions.ConnectionError as e:
        logger.error(f"  CONNECTION ERROR for query '{query}': {e}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"  JSON DECODE ERROR for query '{query}': {e}")
        return []
    except Exception as e:
        logger.error(f"  UNEXPECTED ERROR in search for '{query}': {type(e).__name__}: {e}")
        return []


def compute_match_score(product: dict, result: dict) -> float:
    """
    Compute a confidence score (0-100) for how well a search result
    matches our product. Uses fuzzy matching on name, brand, and category.
    """
    expected_name = clean_name(product["name"]).lower()
    expected_brand = product.get("brand", "").lower()
    expected_category = product.get("category", "").lower()
    expected_swap = product.get("swap_group", "").replace("_", " ").lower()

    result_name = (result.get("product_name") or "").lower()
    result_brand = (result.get("brands") or "").lower()
    result_categories = " ".join(result.get("categories_tags") or []).lower()

    # Name similarity (weighted most heavily)
    name_score = fuzz.token_set_ratio(expected_name, result_name)

    # Brand match bonus
    brand_bonus = 0
    if expected_brand and expected_brand in result_brand:
        brand_bonus = 20
    elif expected_brand and fuzz.partial_ratio(expected_brand, result_brand) > 80:
        brand_bonus = 10

    # Category/swap_group match bonus
    category_bonus = 0
    if expected_swap and expected_swap in result_categories:
        category_bonus = 10
    elif expected_category and expected_category in result_categories:
        category_bonus = 5

    # Final score (capped at 100)
    score = min(100, name_score * 0.7 + brand_bonus + category_bonus)
    return score


def choose_best(product: dict, results: list[dict]) -> tuple:
    """
    Choose the best matching result using fuzzy scoring.
    Returns (best_result, best_score) or (None, 0).
    """
    best = None
    best_score = 0.0

    for r in results:
        score = compute_match_score(product, r)
        if score > best_score:
            best_score = score
            best = r

    return best, best_score


def get_image_url(result: dict) -> str | None:
    """Extract the best available image URL from a result."""
    # Prefer front image, fall back to generic image
    url = result.get("image_front_url") or result.get("image_url")
    if url and url.startswith("http"):
        return url
    return None


def download_image(url: str, save_path: Path) -> bool:
    """Download an image and save it. Returns True on success."""
    try:
        resp = SESSION.get(url, timeout=30, stream=True)
        if resp.status_code != 200:
            logger.warning(f"  Image download failed: HTTP {resp.status_code} | URL: {url}")
            return False

        content_type = resp.headers.get("Content-Type", "")
        if "image" not in content_type and "octet" not in content_type:
            logger.warning(f"  Unexpected content-type: {content_type} | URL: {url}")
            # Still try to save — sometimes content-type is wrong

        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        # Verify file is not empty
        if save_path.stat().st_size < 100:
            logger.warning(f"  Downloaded file too small ({save_path.stat().st_size} bytes), deleting")
            save_path.unlink()
            return False

        return True

    except requests.exceptions.Timeout:
        logger.error(f"  Image download TIMEOUT: {url}")
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error(f"  Image download CONNECTION ERROR: {e}")
        return False
    except OSError as e:
        logger.error(f"  File save ERROR: {e}")
        return False
    except Exception as e:
        logger.error(f"  Image download UNEXPECTED ERROR: {type(e).__name__}: {e}")
        return False


def process_product(product: dict) -> bool:
    """
    Attempt to find and download an image for a product.
    Returns True if successful.
    """
    pid = product["id"]
    image_path = IMAGE_FOLDER / f"{pid}.jpg"

    # Skip if already downloaded
    if image_path.exists():
        logger.info(f"[{pid}] SKIP — already exists: {image_path}")
        return True

    logger.info(f"[{pid}] Processing: {product['name']}")
    logger.info(f"[{pid}]   Brand: {product.get('brand', 'N/A')} | Category: {product.get('category', 'N/A')} | Swap: {product.get('swap_group', 'N/A')}")

    queries = build_queries(product)
    logger.info(f"[{pid}]   Queries: {queries}")

    overall_best = None
    overall_best_score = 0.0
    overall_best_query = ""

    for i, query in enumerate(queries, 1):
        logger.debug(f"[{pid}]   Query {i}/{len(queries)}: '{query}'")

        results = search_openfoodfacts(query)
        time.sleep(RATE_LIMIT)  # Rate limiting

        logger.debug(f"[{pid}]   Results count: {len(results)}")

        if not results:
            logger.debug(f"[{pid}]   No results for query '{query}'")
            continue

        # Log top 5 results
        for j, r in enumerate(results[:5], 1):
            rname = r.get("product_name", "N/A")
            rbrand = r.get("brands", "N/A")
            rimg = "YES" if get_image_url(r) else "NO"
            score = compute_match_score(product, r)
            logger.debug(f"[{pid}]     #{j}: '{rname}' | Brand: '{rbrand}' | Has Image: {rimg} | Score: {score:.1f}")

        # Find best match in this result set
        best, score = choose_best(product, results)

        if best and score > overall_best_score:
            overall_best = best
            overall_best_score = score
            overall_best_query = query

        # If we found a high-confidence match, stop searching
        if score >= 70:
            logger.debug(f"[{pid}]   High confidence match ({score:.1f}), stopping search")
            break

    # Evaluate the best match we found
    if overall_best is None:
        logger.warning(f"[{pid}] MISS — No results from any query")
        return False

    if overall_best_score < MIN_CONFIDENCE:
        logger.warning(
            f"[{pid}] MISS — Best score {overall_best_score:.1f} < threshold {MIN_CONFIDENCE} | "
            f"Match: '{overall_best.get('product_name', 'N/A')}' from query '{overall_best_query}'"
        )
        return False

    # Check for image URL
    img_url = get_image_url(overall_best)
    if not img_url:
        logger.warning(
            f"[{pid}] MISS — Best match has no image URL | "
            f"Match: '{overall_best.get('product_name', 'N/A')}' (score: {overall_best_score:.1f})"
        )
        return False

    # Download the image
    logger.info(
        f"[{pid}]   MATCH: '{overall_best.get('product_name', 'N/A')}' | "
        f"Brand: '{overall_best.get('brands', 'N/A')}' | Score: {overall_best_score:.1f}"
    )
    logger.info(f"[{pid}]   Image URL: {img_url}")

    success = download_image(img_url, image_path)

    if success:
        logger.info(f"[{pid}] ✓ DOWNLOADED: {image_path} ({image_path.stat().st_size / 1024:.1f} KB)")
    else:
        logger.warning(f"[{pid}] MISS — Image download failed")

    return success


# ============== MAIN ============== #

def main():
    # Load catalog
    with open(PRODUCT_FILE, encoding="utf-8") as f:
        catalog = json.load(f)

    products = catalog["products"]

    if MAX_PRODUCTS:
        products = products[:MAX_PRODUCTS]

    logger.info(f"=" * 60)
    logger.info(f"QCart AI — OpenFoodFacts Image Downloader")
    logger.info(f"=" * 60)
    logger.info(f"Total products in catalog: {catalog['total_products']}")
    logger.info(f"Products to process: {len(products)}")
    logger.info(f"Min confidence threshold: {MIN_CONFIDENCE}")
    logger.info(f"Rate limit: {RATE_LIMIT}s between API calls")
    logger.info(f"Output folder: {IMAGE_FOLDER.resolve()}")
    logger.info(f"=" * 60)

    # Check existing downloads
    existing = [p for p in products if (IMAGE_FOLDER / f"{p['id']}.jpg").exists()]
    logger.info(f"Already downloaded: {len(existing)} / {len(products)}")

    downloaded = [p["id"] for p in existing]
    missing = []

    # Process each product
    for product in tqdm(products, desc="Downloading images", unit="product"):
        pid = product["id"]

        # Skip already downloaded
        if pid in downloaded:
            continue

        success = process_product(product)

        if success:
            downloaded.append(pid)
        else:
            missing.append({
                "id": pid,
                "name": product["name"],
                "brand": product.get("brand", ""),
                "category": product.get("category", ""),
                "swap_group": product.get("swap_group", ""),
            })

    # Save logs
    with open(LOG_FOLDER / "downloaded_products.json", "w", encoding="utf-8") as f:
        json.dump(downloaded, f, indent=2)

    with open(LOG_FOLDER / "missing_products.json", "w", encoding="utf-8") as f:
        json.dump(missing, f, indent=2)

    # Summary
    logger.info(f"\n{'=' * 60}")
    logger.info(f"SUMMARY")
    logger.info(f"{'=' * 60}")
    logger.info(f"Total processed : {len(products)}")
    logger.info(f"Downloaded      : {len(downloaded)}")
    logger.info(f"Missing         : {len(missing)}")
    logger.info(f"Success rate    : {len(downloaded) / len(products) * 100:.1f}%")
    logger.info(f"{'=' * 60}")

    if missing:
        logger.info(f"\nFirst 10 missing products:")
        for m in missing[:10]:
            logger.info(f"  - [{m['id']}] {m['name']} ({m['brand']})")


if __name__ == "__main__":
    main()
