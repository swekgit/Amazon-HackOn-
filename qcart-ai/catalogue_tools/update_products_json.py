"""
Products JSON Verifier — PASS 5 (Verification only)
=====================================================
Verifies every product has an "image" field equal to "pXXXX.jpg".

DOES NOT:
  - Replace values with S3 URLs
  - Replace values with CloudFront URLs
  - Modify the schema

This is a consistency check, not a transformer.
"""

import json
import logging
import sys
from pathlib import Path

# ---------------- CONFIG ---------------- #

PRODUCT_FILE = "products.json"
IMAGE_FOLDER = Path("images")
LOG_FOLDER = Path("logs")

LOG_FOLDER.mkdir(exist_ok=True)

# ---------------- LOGGING --------------- #

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FOLDER / "products_json_verify.log", mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------- #


def main():
    logger.info(f"=" * 60)
    logger.info(f"QCart AI — products.json Consistency Verifier")
    logger.info(f"=" * 60)

    # Load catalog
    with open(PRODUCT_FILE, encoding="utf-8") as f:
        catalog = json.load(f)

    products = catalog["products"]
    logger.info(f"Total products: {len(products)}")

    issues = []
    ok_count = 0

    for product in products:
        pid = product.get("id", "UNKNOWN")
        image_field = product.get("image")

        # Check 1: image field exists
        if not image_field:
            issues.append({
                "id": pid,
                "issue": "missing_image_field",
                "detail": "Product has no 'image' field",
            })
            continue

        # Check 2: image field matches expected format
        expected = f"{pid}.jpg"
        if image_field != expected:
            issues.append({
                "id": pid,
                "issue": "image_field_mismatch",
                "detail": f"Expected '{expected}', got '{image_field}'",
            })
            continue

        # Check 3: corresponding file exists in images/
        image_path = IMAGE_FOLDER / expected
        if not image_path.exists():
            issues.append({
                "id": pid,
                "issue": "image_file_missing",
                "detail": f"File {image_path} does not exist",
            })
            continue

        ok_count += 1

    # Summary
    all_ok = len(issues) == 0

    logger.info(f"\n{'=' * 60}")
    logger.info(f"VERIFICATION RESULTS")
    logger.info(f"{'=' * 60}")
    logger.info(f"Products verified OK : {ok_count}")
    logger.info(f"Issues found         : {len(issues)}")
    logger.info(f"Status               : {'PASS ✓' if all_ok else 'FAIL ✗'}")
    logger.info(f"{'=' * 60}")

    if issues:
        logger.warning(f"\nIssues:")
        for issue in issues[:20]:
            logger.warning(f"  [{issue['id']}] {issue['issue']}: {issue['detail']}")

        if len(issues) > 20:
            logger.warning(f"  ... and {len(issues) - 20} more issues")

    # Save report
    report = {
        "total_products": len(products),
        "verified_ok": ok_count,
        "issues_count": len(issues),
        "all_consistent": all_ok,
        "issues": issues,
    }

    with open(LOG_FOLDER / "products_json_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"\nReport: {LOG_FOLDER / 'products_json_report.json'}")

    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
