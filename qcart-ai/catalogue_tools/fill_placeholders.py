"""
Placeholder Image Filler — PASS 3
===================================
Ensures EVERY product in products.json has an image file.

For any product where images/pXXXX.jpg does not exist:
  - Copies placeholder.jpg → images/pXXXX.jpg

After this script, the images/ folder is guaranteed to have
one .jpg for every product. No frontend 404s ever.

Usage:
  python fill_placeholders.py
"""

import json
import shutil
import logging
import sys
from pathlib import Path
from datetime import datetime

from config import PRODUCT_FILE, IMAGE_FOLDER, LOG_FOLDER, PLACEHOLDER_FILE

# ─── Logging ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FOLDER / "fill_placeholders.log", mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger("placeholders")


# ══════════════════════════════════════════════════════════
#  PLACEHOLDER CREATION
# ══════════════════════════════════════════════════════════

def ensure_placeholder_exists():
    """
    If placeholder.jpg doesn't exist, create a minimal valid JPEG.
    This is a tiny 1x1 gray pixel so the pipeline never fails.
    In production, replace this with a real branded placeholder.
    """
    if PLACEHOLDER_FILE.exists() and PLACEHOLDER_FILE.stat().st_size > 100:
        return

    logger.warning("placeholder.jpg missing or invalid — creating minimal default")

    # Minimal valid JFIF JPEG (1x1 gray pixel)
    jpeg_bytes = bytes([
        0xFF, 0xD8,  # SOI
        0xFF, 0xE0,  # APP0
        0x00, 0x10,
        0x4A, 0x46, 0x49, 0x46, 0x00,  # "JFIF\0"
        0x01, 0x01, 0x00,
        0x00, 0x01, 0x00, 0x01,
        0x00, 0x00,
        0xFF, 0xDB,  # DQT
        0x00, 0x43, 0x00,
    ] + [0x08] * 64 + [  # Quantization table
        0xFF, 0xC0,  # SOF0
        0x00, 0x0B, 0x08,
        0x00, 0x01, 0x00, 0x01,  # 1x1
        0x01, 0x01, 0x11, 0x00,
        0xFF, 0xC4,  # DHT
        0x00, 0x1F, 0x00,
        0x00, 0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01,
        0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
        0x08, 0x09, 0x0A, 0x0B,
        0xFF, 0xDA,  # SOS
        0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00,
        0x7F, 0x50,  # Image data
        0xFF, 0xD9,  # EOI
    ])

    with open(PLACEHOLDER_FILE, "wb") as f:
        f.write(jpeg_bytes)

    logger.info(f"Created placeholder.jpg ({len(jpeg_bytes)} bytes)")


# ══════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════

def main():
    ensure_placeholder_exists()

    placeholder_size = PLACEHOLDER_FILE.stat().st_size
    logger.info(f"Placeholder file: {PLACEHOLDER_FILE} ({placeholder_size} bytes)")

    # Load catalog
    with open(PRODUCT_FILE, encoding="utf-8") as f:
        catalog = json.load(f)

    products = catalog["products"]

    logger.info("=" * 60)
    logger.info("QCart AI — Placeholder Image Filler (Pass 3)")
    logger.info("=" * 60)
    logger.info(f"Total products: {len(products)}")

    already_exist = 0
    filled = 0
    errors = []

    for product in products:
        pid = product["id"]
        image_path = IMAGE_FOLDER / f"{pid}.jpg"

        if image_path.exists():
            already_exist += 1
            continue

        try:
            shutil.copy2(PLACEHOLDER_FILE, image_path)
            filled += 1
        except OSError as e:
            logger.error(f"[{pid}] Copy failed: {e}")
            errors.append({"id": pid, "error": str(e)})

    # Final verification
    all_present = all(
        (IMAGE_FOLDER / f"{p['id']}.jpg").exists()
        for p in products
    )

    # Summary
    logger.info(f"\n{'=' * 60}")
    logger.info("PLACEHOLDER FILL SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Already had images       : {already_exist}")
    logger.info(f"Filled with placeholder  : {filled}")
    logger.info(f"Errors                   : {len(errors)}")
    logger.info(f"100% coverage achieved   : {'YES' if all_present else 'NO'}")
    logger.info("=" * 60)

    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_products": len(products),
        "already_had_images": already_exist,
        "filled_with_placeholder": filled,
        "errors": len(errors),
        "all_images_present": all_present,
        "error_details": errors,
    }

    report_path = LOG_FOLDER / "placeholder_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Report: {report_path}")

    if not all_present:
        sys.exit(1)


if __name__ == "__main__":
    main()
