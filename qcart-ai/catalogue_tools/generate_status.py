"""
Pipeline Status Report Generator — PIPELINE_STATUS.md
======================================================
Generates a markdown status report of the image pipeline.

Usage:
  python generate_status.py
"""

import json
from pathlib import Path
from datetime import datetime

from config import PRODUCT_FILE, IMAGE_FOLDER, LOG_FOLDER

def load_json_safe(path: Path, default=None):
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return default


def main():
    # Load data
    with open(PRODUCT_FILE, encoding="utf-8") as f:
        catalog = json.load(f)
    products = catalog["products"]
    total = len(products)

    # Count images on disk
    images_on_disk = set(f.stem for f in IMAGE_FOLDER.glob("*.jpg"))
    products_with_images = [p for p in products if p["id"] in images_on_disk]
    products_without_images = [p for p in products if p["id"] not in images_on_disk]

    # Classify by size (placeholder vs real)
    placeholders = 0
    real_images = 0
    for p in products_with_images:
        img = IMAGE_FOLDER / f"{p['id']}.jpg"
        if img.stat().st_size < 300:
            placeholders += 1
        else:
            real_images += 1

    # Load log files
    off_downloaded = load_json_safe(LOG_FOLDER / "downloaded_products.json", [])
    rf_downloaded = load_json_safe(LOG_FOLDER / "rainforest_downloaded.json", [])
    rf_progress = load_json_safe(LOG_FOLDER / "rainforest_progress.json", {})
    rf_cache = load_json_safe(LOG_FOLDER / "rainforest_cache.json", {})
    missing = load_json_safe(LOG_FOLDER / "missing_products.json", [])

    off_count = len(off_downloaded) if isinstance(off_downloaded, list) else 0
    rf_count = len([r for r in rf_downloaded if isinstance(r, dict) and r.get("status") == "downloaded"])
    api_calls_total = rf_progress.get("total_api_calls", 0)

    # Ready for S3?
    ready_for_s3 = len(products_without_images) == 0

    # Generate report
    report = f"""# QCart AI — Pipeline Status

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Overview

| Metric | Value |
|--------|-------|
| Total Products | {total} |
| Images on Disk | {len(products_with_images)} |
| Missing Images | {len(products_without_images)} |
| Coverage | {len(products_with_images) / total * 100:.1f}% |

## Image Sources

| Source | Count | Percentage |
|--------|-------|------------|
| OpenFoodFacts | {off_count} | {off_count / total * 100:.1f}% |
| Rainforest API | {rf_count} | {rf_count / total * 100:.1f}% |
| Placeholders | {placeholders} | {placeholders / total * 100:.1f}% |
| Real Images | {real_images} | {real_images / total * 100:.1f}% |
| Still Missing | {len(products_without_images)} | {len(products_without_images) / total * 100:.1f}% |

## API Usage

| Metric | Value |
|--------|-------|
| Rainforest API Calls (total) | {api_calls_total} |
| Cached Responses | {len(rf_cache)} |
| Products in Queue | {len(missing)} |

## Status

| Check | Result |
|-------|--------|
| All images present | {'YES' if ready_for_s3 else 'NO'} |
| Ready for S3 upload | {'YES' if ready_for_s3 else 'NO'} |

## Next Steps

"""

    if len(products_without_images) > 0:
        report += f"""- [ ] Run `python download_rainforest.py` ({len(products_without_images)} products need images)
- [ ] Run `python fill_placeholders.py` (guarantee 100% coverage)
- [ ] Run `python verify_dataset.py`
- [ ] Run `python upload_s3.py`
"""
    elif placeholders > 0:
        report += f"""- [x] All products have images
- [ ] Consider running Rainforest to replace {placeholders} placeholders with real images
- [ ] Run `python upload_s3.py`
"""
    else:
        report += """- [x] All products have real images
- [x] Ready for S3 upload
- [ ] Run `python upload_s3.py`
"""

    # Write file
    status_path = Path(__file__).parent / "PIPELINE_STATUS.md"
    with open(status_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    print(f"\nSaved to: {status_path}")


if __name__ == "__main__":
    main()
