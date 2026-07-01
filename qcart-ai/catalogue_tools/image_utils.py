"""
Image Pipeline Utilities — image_utils.py
==========================================
Shared helper functions for all image downloaders.
Every downloader script imports these to avoid code duplication.
"""

import json
import re
import time
import logging
from pathlib import Path
from datetime import datetime

import requests
from rapidfuzz import fuzz

from config import (
    IMAGE_FOLDER, LOG_FOLDER, PRODUCT_FILE,
    MAX_RETRIES, MIN_CONFIDENCE, DRY_RUN, TEST_MODE, TEST_PRODUCTS,
)

logger = logging.getLogger("image_utils")

# Shared HTTP session
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "QCartAI/1.0 (image-pipeline)"})


# ══════════════════════════════════════════════════════════
#  JSON HELPERS
# ══════════════════════════════════════════════════════════

def load_json(path: Path, default=None):
    """Load JSON file safely. Creates with default if missing."""
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load {path.name}: {e}")
    if default is not None:
        save_json(path, default)
    return default if default is not None else {}


def save_json(path: Path, data):
    """Save data as JSON atomically."""
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


# ══════════════════════════════════════════════════════════
#  PRODUCT LOADING
# ══════════════════════════════════════════════════════════

def load_missing_products() -> list[dict]:
    """Load products still needing images from missing_products.json or full catalog."""
    missing_file = LOG_FOLDER / "missing_products.json"

    if missing_file.exists():
        missing = load_json(missing_file, [])
        if missing:
            return missing

    # Fallback: full catalog
    logger.warning("missing_products.json not found. Loading full catalog.")
    with open(PRODUCT_FILE, encoding="utf-8") as f:
        catalog = json.load(f)

    products = [
        {"id": p["id"], "name": p["name"], "brand": p.get("brand", ""),
         "category": p.get("category", ""), "swap_group": p.get("swap_group", "")}
        for p in catalog["products"]
    ]
    save_json(missing_file, products)
    return products


def filter_already_downloaded(products: list[dict]) -> list[dict]:
    """Remove products that already have images on disk."""
    return [p for p in products if not (IMAGE_FOLDER / f"{p['id']}.jpg").exists()]


# ══════════════════════════════════════════════════════════
#  TEXT CLEANING
# ══════════════════════════════════════════════════════════

def clean_name(name: str) -> str:
    """Remove weights, packaging, parenthetical content."""
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"\d+\s?(kg|g|gm|ml|l|ltr|pcs|pc|pack|bags|pellets|sachets)\b", "", name, flags=re.I)
    name = re.sub(r"Pack of \d+", "", name, flags=re.I)
    name = re.sub(r"\bCombo\b", "", name, flags=re.I)
    return " ".join(name.split()).strip()


def extract_size(name: str) -> str:
    """Extract pack size from product name (e.g., '500ml', '1kg')."""
    match = re.search(r"(\d+\s?(?:kg|g|gm|ml|l|ltr|pcs|pc))", name, re.I)
    return match.group(1).lower().replace(" ", "") if match else ""


def extract_brand(product: dict) -> str:
    """Get normalized brand from product."""
    return product.get("brand", "").strip().lower()


# ══════════════════════════════════════════════════════════
#  QUERY GENERATION
# ══════════════════════════════════════════════════════════

def build_queries(product: dict) -> list[str]:
    """
    Build search queries in decreasing specificity.
    Returns 5 query levels with deduplication.
    """
    brand = product.get("brand", "").strip()
    full_name = clean_name(product.get("name", ""))
    swap_group = product.get("swap_group", "").replace("_", " ").strip()
    category = product.get("category", "").replace("_", " ").strip()

    name_no_brand = full_name
    if brand and full_name.lower().startswith(brand.lower()):
        name_no_brand = full_name[len(brand):].strip()

    queries = []
    if brand and name_no_brand:
        queries.append(f"{brand} {name_no_brand}")
    if full_name:
        queries.append(full_name)
    if brand and swap_group:
        queries.append(f"{brand} {swap_group}")
    if swap_group:
        queries.append(swap_group)
    if category and category != swap_group:
        queries.append(category)

    seen = set()
    result = []
    for q in queries:
        key = q.lower().strip()
        if key and key not in seen:
            result.append(q)
            seen.add(key)
    return result


# ══════════════════════════════════════════════════════════
#  SIMILARITY SCORING
# ══════════════════════════════════════════════════════════

def calculate_similarity(product: dict, title: str, result_brand: str = "") -> float:
    """
    Calculate similarity score between product and a search result.
    Considers name, brand, swap_group, category, and pack size.
    """
    expected_name = clean_name(product.get("name", "")).lower()
    expected_brand = product.get("brand", "").lower()
    expected_swap = product.get("swap_group", "").replace("_", " ").lower()
    expected_size = extract_size(product.get("name", ""))

    title_lower = title.lower()
    brand_lower = result_brand.lower()

    # Name similarity (primary signal)
    name_score = fuzz.token_set_ratio(expected_name, title_lower)

    # Brand bonus
    brand_bonus = 0
    if expected_brand:
        if expected_brand in title_lower or expected_brand in brand_lower:
            brand_bonus = 25
        elif fuzz.partial_ratio(expected_brand, brand_lower) > 80:
            brand_bonus = 15

    # Swap group bonus
    swap_bonus = 0
    if expected_swap and expected_swap in title_lower:
        swap_bonus = 10

    # Pack size match/penalty
    size_mod = 0
    if expected_size:
        result_size = extract_size(title)
        if result_size:
            if result_size == expected_size:
                size_mod = 10  # Exact match bonus
            else:
                size_mod = -10  # Wrong size penalty

    score = min(100, name_score * 0.6 + brand_bonus + swap_bonus + size_mod)
    return max(0, score)


# ══════════════════════════════════════════════════════════
#  CACHE HELPERS
# ══════════════════════════════════════════════════════════

def cache_lookup(cache: dict, product_id: str) -> dict | None:
    """Check if product is in cache. Returns cached entry or None."""
    return cache.get(product_id)


def cache_save(cache: dict, product_id: str, entry: dict, cache_path: Path):
    """Save a cache entry and persist to disk."""
    entry["timestamp"] = datetime.now().isoformat()
    cache[product_id] = entry
    save_json(cache_path, cache)


# ══════════════════════════════════════════════════════════
#  IMAGE DOWNLOAD & VALIDATION
# ══════════════════════════════════════════════════════════

def validate_image(path: Path, min_size: int = 1000) -> bool:
    """
    Validate a downloaded image file.
    Checks: exists, minimum size, JPEG header.
    """
    if not path.exists():
        return False
    size = path.stat().st_size
    if size < min_size:
        return False
    with open(path, "rb") as f:
        header = f.read(2)
    return header == b"\xff\xd8"


def download_image(url: str, save_path: Path, min_size: int = 1000) -> bool:
    """
    Download an image with validation and retry.
    Returns True on success.
    """
    if not url or not url.startswith("http"):
        logger.warning(f"    Invalid URL: {url}")
        return False

    for attempt in range(MAX_RETRIES):
        try:
            resp = SESSION.get(url, timeout=30, stream=True)

            if resp.status_code != 200:
                logger.warning(f"    HTTP {resp.status_code}: {url[:70]}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 * (attempt + 1))
                continue

            # Check content type
            ct = resp.headers.get("Content-Type", "")
            if "image" not in ct and "octet" not in ct:
                logger.debug(f"    Unexpected content-type: {ct}")

            # Write to temp
            tmp_path = save_path.with_suffix(".tmp")
            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Validate size
            size = tmp_path.stat().st_size
            if size < min_size:
                logger.warning(f"    Too small ({size} bytes)")
                tmp_path.unlink()
                continue

            # Validate JPEG
            with open(tmp_path, "rb") as f:
                header = f.read(2)
            if header != b"\xff\xd8":
                # Try PNG
                with open(tmp_path, "rb") as f:
                    png_header = f.read(4)
                if png_header == b"\x89PNG":
                    # Accept PNG too
                    tmp_path.replace(save_path)
                    return True
                logger.warning(f"    Invalid image format (header: {header.hex()})")
                tmp_path.unlink()
                continue

            tmp_path.replace(save_path)
            return True

        except requests.exceptions.Timeout:
            logger.warning(f"    Timeout (attempt {attempt + 1})")
            time.sleep(3 * (attempt + 1))
        except requests.exceptions.ConnectionError:
            logger.warning(f"    Connection error (attempt {attempt + 1})")
            time.sleep(5)
        except OSError as e:
            logger.error(f"    File error: {e}")
            break
        except Exception as e:
            logger.error(f"    Error: {type(e).__name__}: {e}")
            break

    # Cleanup
    tmp = save_path.with_suffix(".tmp")
    if tmp.exists():
        tmp.unlink()
    return False


# ══════════════════════════════════════════════════════════
#  LOGGING HELPERS
# ══════════════════════════════════════════════════════════

def log_success(pid: str, source: str, url: str, score: float):
    """Log a successful download."""
    logger.info(f"[{pid}] DOWNLOADED via {source} (score: {score:.0f})")


def log_failure(pid: str, source: str, reason: str):
    """Log a failed attempt."""
    logger.warning(f"[{pid}] MISS ({source}) - {reason}")


def update_downloaded(pid: str):
    """Add product to global downloaded list and remove from missing."""
    dl_file = LOG_FOLDER / "downloaded_products.json"
    downloaded = load_json(dl_file, [])
    if pid not in downloaded:
        downloaded.append(pid)
        save_json(dl_file, downloaded)

    # Remove from missing
    missing_file = LOG_FOLDER / "missing_products.json"
    missing = load_json(missing_file, [])
    missing = [p for p in missing if p.get("id") != pid]
    save_json(missing_file, missing)
