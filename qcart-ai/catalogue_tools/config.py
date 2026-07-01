"""
Centralized Configuration — config.py
=======================================
Loads environment variables from .env using python-dotenv.
All pipeline scripts import this module for configuration.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env from the same directory as this file
_ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(_ENV_PATH)

# ─── Rainforest API ───────────────────────────────────────
RAINFOREST_API_KEY: str = os.getenv("RAINFOREST_API_KEY", "")
AMAZON_DOMAIN: str = os.getenv("AMAZON_DOMAIN", "amazon.in")

# ─── AWS ──────────────────────────────────────────────────
AWS_REGION: str = os.getenv("AWS_REGION", "ap-south-1")
S3_BUCKET: str = os.getenv("S3_BUCKET", "qcart-product-images")
S3_FOLDER: str = os.getenv("S3_FOLDER", "products")

# ─── CloudFront ──────────────────────────────────────────
CLOUDFRONT_URL: str = os.getenv("CLOUDFRONT_URL", "https://cdn.qcart.ai")

# ─── Paths ────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
PRODUCT_FILE = BASE_DIR / "products.json"
IMAGE_FOLDER = BASE_DIR / "images"
LOG_FOLDER = BASE_DIR / "logs"
PLACEHOLDER_FILE = BASE_DIR / "placeholder.jpg"

# Ensure directories exist
IMAGE_FOLDER.mkdir(exist_ok=True)
LOG_FOLDER.mkdir(exist_ok=True)

# ─── Pipeline Limits ─────────────────────────────────────
MAX_REQUESTS_PER_RUN: int = int(os.getenv("MAX_REQUESTS_PER_RUN", "49"))
RATE_LIMIT_SECONDS: float = float(os.getenv("RATE_LIMIT_SECONDS", "1.5"))
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
DOWNLOAD_THREADS: int = int(os.getenv("DOWNLOAD_THREADS", "4"))
MIN_CONFIDENCE: int = int(os.getenv("MIN_CONFIDENCE", "45"))

# ─── Modes ────────────────────────────────────────────────
DRY_RUN: bool = os.getenv("DRY_RUN", "false").lower() in ("true", "1", "yes")
TEST_MODE: bool = os.getenv("TEST_MODE", "false").lower() in ("true", "1", "yes")
TEST_PRODUCTS: int = int(os.getenv("TEST_PRODUCTS", "5"))


def validate_rainforest_key() -> bool:
    """Check if Rainforest API key is configured."""
    if not RAINFOREST_API_KEY:
        print("=" * 60)
        print("ERROR: RAINFOREST_API_KEY not set!")
        print("")
        print("Set it in catalogue_tools/.env:")
        print("  RAINFOREST_API_KEY=your_key_here")
        print("")
        print("Or via environment variable:")
        print("  export RAINFOREST_API_KEY=your_key_here")
        print("=" * 60)
        return False
    return True


if __name__ == "__main__":
    print("QCart AI — Pipeline Configuration")
    print("=" * 50)
    print(f"RAINFOREST_API_KEY : {'SET (' + RAINFOREST_API_KEY[:8] + '...)' if RAINFOREST_API_KEY else 'NOT SET'}")
    print(f"AMAZON_DOMAIN      : {AMAZON_DOMAIN}")
    print(f"AWS_REGION         : {AWS_REGION}")
    print(f"S3_BUCKET          : {S3_BUCKET}")
    print(f"S3_FOLDER          : {S3_FOLDER}")
    print(f"CLOUDFRONT_URL     : {CLOUDFRONT_URL}")
    print(f"MAX_REQUESTS       : {MAX_REQUESTS_PER_RUN}")
    print(f"RATE_LIMIT         : {RATE_LIMIT_SECONDS}s")
    print(f"MIN_CONFIDENCE     : {MIN_CONFIDENCE}")
    print(f"DRY_RUN            : {DRY_RUN}")
    print(f"TEST_MODE          : {TEST_MODE}")
    print(f"TEST_PRODUCTS      : {TEST_PRODUCTS}")
    print(f"IMAGE_FOLDER       : {IMAGE_FOLDER}")
    print(f"LOG_FOLDER         : {LOG_FOLDER}")
    print("=" * 50)
