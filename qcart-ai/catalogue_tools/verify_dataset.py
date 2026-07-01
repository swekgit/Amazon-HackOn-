"""
Dataset Verifier — PASS 4
===========================
Comprehensive integrity checks on the product image dataset.

Checks:
  1. Every product has an 'image' field
  2. Every image file exists in images/
  3. No duplicate product IDs
  4. No corrupt images (validates JPEG SOI header)
  5. Image field format consistency (pXXXX.jpg)
  6. No orphan images
  7. File size validation

Generates: logs/verification_report.json

Usage:
  python verify_dataset.py
"""

import json
import re
import logging
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter

from config import PRODUCT_FILE, IMAGE_FOLDER, LOG_FOLDER

# ─── Logging ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FOLDER / "verify_dataset.log", mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger("verifier")

# ─── Constants ────────────────────────────────────────────
JPEG_SOI = b"\xff\xd8"
MIN_IMAGE_SIZE = 100  # bytes


# ══════════════════════════════════════════════════════════
#  VALIDATION FUNCTIONS
# ══════════════════════════════════════════════════════════

def is_valid_jpeg(path: Path) -> tuple[bool, str]:
    """Check JPEG validity. Returns (valid, reason)."""
    try:
        size = path.stat().st_size
        if size < MIN_IMAGE_SIZE:
            return False, f"Too small ({size} bytes)"

        with open(path, "rb") as f:
            header = f.read(2)

        if header != JPEG_SOI:
            return False, f"Invalid header: {header.hex()}"

        return True, "OK"
    except OSError as e:
        return False, f"Read error: {e}"


def classify_image_source(path: Path) -> str:
    """Classify whether an image is a real download or placeholder."""
    try:
        size = path.stat().st_size
        if size < 300:
            return "placeholder"
        elif size < 5000:
            return "thumbnail"
        else:
            return "full_image"
    except OSError:
        return "error"


# ══════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════

def main():
    logger.info("=" * 60)
    logger.info("QCart AI — Dataset Verifier (Pass 4)")
    logger.info("=" * 60)

    # Load catalog
    with open(PRODUCT_FILE, encoding="utf-8") as f:
        catalog = json.load(f)

    products = catalog["products"]
    total = len(products)
    logger.info(f"Total products: {total}")

    checks = {}
    issues_total = 0

    # ─── CHECK 1: Duplicate IDs ───────────────────────────
    ids = [p["id"] for p in products]
    id_counts = Counter(ids)
    duplicates = {k: v for k, v in id_counts.items() if v > 1}
    checks["duplicate_ids"] = {
        "pass": len(duplicates) == 0,
        "count": len(duplicates),
        "items": list(duplicates.keys())[:20],
    }
    if duplicates:
        logger.error(f"[X] Duplicate IDs: {list(duplicates.keys())[:10]}")
        issues_total += len(duplicates)
    else:
        logger.info("[OK] No duplicate IDs")

    # ─── CHECK 2: ID Format ──────────────────────────────
    bad_ids = [pid for pid in ids if not re.match(r"^p\d{4}$", pid)]
    checks["id_format"] = {
        "pass": len(bad_ids) == 0,
        "count": len(bad_ids),
        "items": bad_ids[:20],
    }
    if bad_ids:
        logger.warning(f"[!] Non-standard IDs: {bad_ids[:10]}")
        issues_total += len(bad_ids)
    else:
        logger.info("[OK] All IDs match pXXXX format")

    # ─── CHECK 3: Missing 'image' Field ──────────────────
    missing_field = [p["id"] for p in products if "image" not in p or not p["image"]]
    checks["missing_image_field"] = {
        "pass": len(missing_field) == 0,
        "count": len(missing_field),
        "items": missing_field[:20],
    }
    if missing_field:
        logger.error(f"[X] Missing 'image' field: {len(missing_field)} products")
        issues_total += len(missing_field)
    else:
        logger.info("[OK] All products have 'image' field")

    # ─── CHECK 4: Image Field Consistency ─────────────────
    inconsistent = []
    for p in products:
        expected = f"{p['id']}.jpg"
        if p.get("image") != expected:
            inconsistent.append({"id": p["id"], "has": p.get("image"), "expected": expected})

    checks["image_field_consistency"] = {
        "pass": len(inconsistent) == 0,
        "count": len(inconsistent),
        "items": inconsistent[:20],
    }
    if inconsistent:
        logger.warning(f"[!] Inconsistent image fields: {len(inconsistent)}")
        issues_total += len(inconsistent)
    else:
        logger.info("[OK] All image fields match pXXXX.jpg format")

    # ─── CHECK 5: Missing Image Files ─────────────────────
    missing_files = []
    for p in products:
        path = IMAGE_FOLDER / f"{p['id']}.jpg"
        if not path.exists():
            missing_files.append(p["id"])

    checks["missing_image_files"] = {
        "pass": len(missing_files) == 0,
        "count": len(missing_files),
        "items": missing_files[:50],
    }
    if missing_files:
        logger.error(f"[X] Missing image files: {len(missing_files)}")
        issues_total += len(missing_files)
    else:
        logger.info("[OK] All image files exist")

    # ─── CHECK 6: Corrupted Images ────────────────────────
    corrupted = []
    valid_count = 0
    total_size = 0

    source_stats = {"full_image": 0, "thumbnail": 0, "placeholder": 0, "error": 0}

    for p in products:
        path = IMAGE_FOLDER / f"{p['id']}.jpg"
        if not path.exists():
            continue

        valid, reason = is_valid_jpeg(path)
        if valid:
            valid_count += 1
            total_size += path.stat().st_size
            source = classify_image_source(path)
            source_stats[source] += 1
        else:
            corrupted.append({"id": p["id"], "reason": reason})

    checks["corrupted_images"] = {
        "pass": len(corrupted) == 0,
        "count": len(corrupted),
        "items": corrupted[:20],
    }
    if corrupted:
        logger.warning(f"[!] Corrupted images: {len(corrupted)}")
        issues_total += len(corrupted)
    else:
        logger.info("[OK] All images are valid JPEGs")

    # ─── CHECK 7: Orphan Images ───────────────────────────
    all_ids_set = set(ids)
    image_files = list(IMAGE_FOLDER.glob("*.jpg"))
    orphans = [f.stem for f in image_files if f.stem not in all_ids_set]

    checks["orphan_images"] = {
        "pass": len(orphans) == 0,
        "count": len(orphans),
        "items": orphans[:20],
    }
    if orphans:
        logger.warning(f"[!] Orphan images (no product): {len(orphans)}")
    else:
        logger.info("[OK] No orphan images")

    # ─── OVERALL RESULT ───────────────────────────────────
    all_pass = all(c["pass"] for c in checks.values())

    logger.info(f"\n{'=' * 60}")
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total products       : {total}")
    logger.info(f"Valid images          : {valid_count}")
    logger.info(f"  - Full images       : {source_stats['full_image']}")
    logger.info(f"  - Thumbnails        : {source_stats['thumbnail']}")
    logger.info(f"  - Placeholders      : {source_stats['placeholder']}")
    logger.info(f"Total image size     : {total_size / (1024 * 1024):.2f} MB")
    logger.info(f"Missing files        : {len(missing_files)}")
    logger.info(f"Corrupted            : {len(corrupted)}")
    logger.info(f"Duplicate IDs        : {len(duplicates)}")
    logger.info(f"Orphan images        : {len(orphans)}")
    logger.info(f"Overall              : {'PASS' if all_pass else 'ISSUES FOUND'}")
    logger.info("=" * 60)

    # ─── Save Report ──────────────────────────────────────
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_products": total,
        "overall_pass": all_pass,
        "stats": {
            "valid_images": valid_count,
            "full_images": source_stats["full_image"],
            "thumbnails": source_stats["thumbnail"],
            "placeholders": source_stats["placeholder"],
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "missing_files": len(missing_files),
            "corrupted": len(corrupted),
            "duplicate_ids": len(duplicates),
            "orphan_images": len(orphans),
        },
        "checks": checks,
    }

    report_path = LOG_FOLDER / "verification_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"\nFull report: {report_path}")

    if not all_pass:
        logger.warning("\n[!] Issues found. Review report before uploading to S3.")

        # Task 14: Recommend next command
        if missing_files:
            logger.info("\n" + "-" * 60)
            logger.info("RECOMMENDED NEXT STEPS:")
            logger.info("-" * 60)
            if len(missing_files) == total:
                logger.info("  No images detected at all.")
                logger.info("  Option 1: python download_rainforest.py")
                logger.info("  Option 2: python fill_placeholders.py  (fast, uses placeholder)")
            elif len(missing_files) > total * 0.5:
                logger.info(f"  {len(missing_files)}/{total} images missing (>{50}%).")
                logger.info("  Recommended: python download_rainforest.py")
                logger.info("  Then:        python fill_placeholders.py")
            else:
                logger.info(f"  {len(missing_files)}/{total} images missing.")
                logger.info("  Recommended: python fill_placeholders.py")
            logger.info("-" * 60)

        sys.exit(1)
    else:
        logger.info("\nDataset is clean. Ready for S3 upload.")
        logger.info("  Next: python upload_s3.py")


if __name__ == "__main__":
    main()
