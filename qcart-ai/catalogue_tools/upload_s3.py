"""
S3 Image Uploader — PASS 5
============================
Uploads all product images to Amazon S3 for CloudFront delivery.

Bucket: s3://{S3_BUCKET}/{S3_FOLDER}/
  - Skips files already uploaded (size comparison)
  - Supports resume (tracks uploaded files)
  - Retries failed uploads with exponential backoff
  - Uses ThreadPoolExecutor for parallel uploads
  - Generates upload_report.json

Prerequisites:
  - AWS CLI configured: aws configure
  - Or environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
  - pip install boto3 tqdm python-dotenv

Usage:
  python upload_s3.py
"""

import json
import hashlib
import logging
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError
from tqdm import tqdm

from config import (
    IMAGE_FOLDER,
    LOG_FOLDER,
    S3_BUCKET,
    S3_FOLDER,
    AWS_REGION,
    MAX_RETRIES,
    DOWNLOAD_THREADS,
)

# ─── Constants ────────────────────────────────────────────
CONTENT_TYPE = "image/jpeg"
CACHE_CONTROL = "public, max-age=31536000, immutable"  # 1 year
UPLOAD_PROGRESS_FILE = LOG_FOLDER / "upload_progress.json"

# ─── Logging ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FOLDER / "upload_s3.log", mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger("s3_upload")


# ══════════════════════════════════════════════════════════
#  S3 CLIENT
# ══════════════════════════════════════════════════════════

def get_s3_client():
    """Create an S3 client with validation."""
    try:
        client = boto3.client("s3", region_name=AWS_REGION)
        # Validate bucket access
        client.head_bucket(Bucket=S3_BUCKET)
        logger.info(f"Connected to S3 bucket: {S3_BUCKET} ({AWS_REGION})")
        return client

    except NoCredentialsError:
        logger.error("AWS credentials not configured!")
        logger.error("Run: aws configure")
        logger.error("Or set: AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY")
        sys.exit(1)

    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "404":
            logger.error(f"Bucket '{S3_BUCKET}' does not exist!")
            logger.error(f"Create: aws s3 mb s3://{S3_BUCKET} --region {AWS_REGION}")
        elif code == "403":
            logger.error(f"Access denied to bucket '{S3_BUCKET}'!")
            logger.error("Check IAM permissions: s3:PutObject, s3:GetObject, s3:HeadObject, s3:HeadBucket")
        else:
            logger.error(f"S3 error ({code}): {e}")
        sys.exit(1)

    except BotoCoreError as e:
        logger.error(f"AWS SDK error: {e}")
        sys.exit(1)


# ══════════════════════════════════════════════════════════
#  UPLOAD LOGIC
# ══════════════════════════════════════════════════════════

def is_already_uploaded(s3_client, s3_key: str, local_path: Path) -> bool:
    """Check if file already exists in S3 with same size."""
    try:
        resp = s3_client.head_object(Bucket=S3_BUCKET, Key=s3_key)
        remote_size = resp["ContentLength"]
        local_size = local_path.stat().st_size
        return remote_size == local_size
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        logger.debug(f"head_object error for {s3_key}: {e}")
        return False


def upload_single(s3_client, local_path: Path, s3_key: str) -> dict:
    """Upload a single file with retries. Returns result dict."""
    for attempt in range(MAX_RETRIES):
        try:
            s3_client.upload_file(
                str(local_path),
                S3_BUCKET,
                s3_key,
                ExtraArgs={
                    "ContentType": CONTENT_TYPE,
                    "CacheControl": CACHE_CONTROL,
                },
            )
            return {
                "file": local_path.name,
                "key": s3_key,
                "status": "uploaded",
                "size": local_path.stat().st_size,
            }

        except ClientError as e:
            if attempt < MAX_RETRIES - 1:
                wait = (attempt + 1) * 2
                logger.debug(f"  Retry {attempt + 1} for {local_path.name}: {e}")
                time.sleep(wait)
            else:
                return {
                    "file": local_path.name,
                    "key": s3_key,
                    "status": "failed",
                    "error": str(e),
                }

        except Exception as e:
            return {
                "file": local_path.name,
                "key": s3_key,
                "status": "failed",
                "error": f"{type(e).__name__}: {e}",
            }

    return {"file": local_path.name, "key": s3_key, "status": "failed", "error": "max retries"}


# ══════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════

def main():
    logger.info("=" * 60)
    logger.info("QCart AI — S3 Image Uploader (Pass 5)")
    logger.info("=" * 60)
    logger.info(f"Bucket   : s3://{S3_BUCKET}/{S3_FOLDER}/")
    logger.info(f"Region   : {AWS_REGION}")
    logger.info(f"Threads  : {DOWNLOAD_THREADS}")

    # Collect all images
    image_files = sorted(IMAGE_FOLDER.glob("*.jpg"))
    logger.info(f"Images found: {len(image_files)}")

    if not image_files:
        logger.warning("No images to upload! Run the download pipeline first.")
        sys.exit(0)

    # Connect to S3
    s3_client = get_s3_client()

    # Determine what needs uploading
    logger.info("Checking existing uploads...")
    to_upload = []
    already_uploaded = []

    for img_path in tqdm(image_files, desc="Checking S3", unit="file"):
        s3_key = f"{S3_FOLDER}/{img_path.name}"
        if is_already_uploaded(s3_client, s3_key, img_path):
            already_uploaded.append(img_path.name)
        else:
            to_upload.append(img_path)

    logger.info(f"Already in S3  : {len(already_uploaded)}")
    logger.info(f"To upload      : {len(to_upload)}")
    logger.info("=" * 60)

    if not to_upload:
        logger.info("All images already uploaded! Nothing to do.")
    else:
        # Upload with thread pool
        uploaded = []
        failed = []

        with ThreadPoolExecutor(max_workers=DOWNLOAD_THREADS) as executor:
            futures = {}
            for img_path in to_upload:
                s3_key = f"{S3_FOLDER}/{img_path.name}"
                future = executor.submit(upload_single, s3_client, img_path, s3_key)
                futures[future] = img_path.name

            for future in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Uploading",
                unit="file",
            ):
                result = future.result()
                if result["status"] == "uploaded":
                    uploaded.append(result)
                else:
                    failed.append(result)
                    logger.warning(f"  FAILED: {result['file']} — {result.get('error', '?')}")

        logger.info(f"\nNewly uploaded: {len(uploaded)}")
        if failed:
            logger.warning(f"Failed: {len(failed)}")
            for f in failed[:10]:
                logger.warning(f"  - {f['file']}: {f.get('error', '?')}")

    # ─── Summary & Report ─────────────────────────────────
    total_uploaded = len(already_uploaded) + len(to_upload) - len(failed if to_upload else [])
    total_size = sum(f.stat().st_size for f in image_files)

    logger.info(f"\n{'=' * 60}")
    logger.info("UPLOAD SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total images      : {len(image_files)}")
    logger.info(f"Already in S3     : {len(already_uploaded)}")
    logger.info(f"Newly uploaded    : {len(to_upload) - len(failed if to_upload else [])}")
    logger.info(f"Failed            : {len(failed) if to_upload else 0}")
    logger.info(f"Total size        : {total_size / (1024 * 1024):.2f} MB")
    logger.info(f"S3 location       : s3://{S3_BUCKET}/{S3_FOLDER}/")
    logger.info("=" * 60)

    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "bucket": S3_BUCKET,
        "prefix": S3_FOLDER,
        "region": AWS_REGION,
        "total_images": len(image_files),
        "already_existed": len(already_uploaded),
        "newly_uploaded": len(to_upload) - len(failed if to_upload else []),
        "failed": len(failed) if to_upload else 0,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "failed_files": failed if to_upload else [],
    }

    report_path = LOG_FOLDER / "upload_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"\nReport: {report_path}")

    if to_upload and failed:
        logger.warning("\n⚠ Some uploads failed. Run again to retry.")
        sys.exit(1)


if __name__ == "__main__":
    main()
