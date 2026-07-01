# QCart AI — Product Image Pipeline

Production-ready pipeline to download, validate, and deploy product images for the QCart AI platform.

## Architecture

```
OpenFoodFacts (free)  →  Rainforest API (paid)  →  Placeholder  →  Verify  →  S3  →  CloudFront
       Pass 1                  Pass 2                 Pass 3        Pass 4    Pass 5     CDN
```

The backend never knows where an image came from. It simply reads:
```json
{"image": "p0001.jpg"}
```

And constructs at runtime:
```
https://cdn.qcart.ai/products/p0001.jpg
```

## Prerequisites

```bash
pip install requests rapidfuzz tqdm python-dotenv boto3
```

## Configuration

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

Required variables:
| Variable | Description |
|----------|-------------|
| `RAINFOREST_API_KEY` | API key from rainforestapi.com |
| `AMAZON_DOMAIN` | Amazon marketplace (default: amazon.in) |
| `AWS_REGION` | AWS region for S3 (default: ap-south-1) |
| `S3_BUCKET` | S3 bucket name |
| `S3_FOLDER` | Prefix/folder inside bucket (default: products) |
| `CLOUDFRONT_URL` | CloudFront distribution URL |

Verify config:
```bash
python config.py
```

## Execution Order

### Step 1: OpenFoodFacts (Free — already completed)
```bash
python download_openfoodfacts.py
```
- Downloads from OpenFoodFacts (free, ~15-30% coverage for Indian products)
- Creates `logs/downloaded_products.json` and `logs/missing_products.json`
- Rate limited: ~1 request/second

### Step 2: Rainforest API (Paid — processes ONLY missing products)
```bash
python download_rainforest.py
```
- **Only reads** `logs/missing_products.json`
- Never re-searches downloaded products
- Budget cap: 300 API calls per run (configurable)
- Fully resumable — run again to continue
- Uses cache (`logs/rainforest_cache.json`) to avoid duplicate calls

### Step 3: Fill Placeholders (Guarantees 100% coverage)
```bash
python fill_placeholders.py
```
- Copies `placeholder.jpg` for any remaining gaps
- After this step, every product has an image

### Step 4: Verify Dataset Integrity
```bash
python verify_dataset.py
```
- Checks: duplicates, missing files, corrupt JPEGs, orphans
- Generates `logs/verification_report.json`
- Exit code 0 = all clear, 1 = issues found

### Step 5: Upload to S3
```bash
# First time: configure AWS
aws configure

# Then upload
python upload_s3.py
```
- Skips files already in S3
- Parallel uploads (4 threads)
- Retry with exponential backoff
- Generates `logs/upload_report.json`

### Step 6: CloudFront Distribution
Create via AWS Console or CLI:
```bash
aws cloudfront create-distribution \
  --origin-domain-name qcart-product-images.s3.ap-south-1.amazonaws.com \
  --default-root-object index.html
```

Update `.env` with the CloudFront URL once created.

## File Structure

```
catalogue_tools/
├── config.py                    # Centralized configuration
├── .env                         # Secrets (git-ignored)
├── .env.example                 # Template for .env
├── download_openfoodfacts.py    # Pass 1: Free source
├── download_rainforest.py       # Pass 2: Paid source (missing only)
├── fill_placeholders.py         # Pass 3: 100% coverage guarantee
├── verify_dataset.py            # Pass 4: Integrity checks
├── upload_s3.py                 # Pass 5: Deploy to S3
├── products.json                # Product catalog (DO NOT MODIFY)
├── placeholder.jpg              # Fallback image
├── README.md                    # This file
├── images/                      # Downloaded images (p0001.jpg, p0002.jpg, ...)
└── logs/
    ├── download_debug.log       # OpenFoodFacts debug log
    ├── downloaded_products.json # IDs successfully downloaded (OFF)
    ├── missing_products.json    # IDs not found in OFF
    ├── rainforest_cache.json    # API response cache
    ├── rainforest_progress.json # Resume state
    ├── rainforest_debug.log     # Rainforest debug log
    ├── rainforest_downloaded.json
    ├── rainforest_missing.json
    ├── rainforest_failed.json
    ├── placeholder_report.json
    ├── verification_report.json
    └── upload_report.json
```

## Key Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Never modify products.json** | Schema is frozen. Backend constructs URLs. |
| **Minimize API costs** | Cache, progress tracking, budget limits |
| **Resumable** | Every script picks up where it left off |
| **Idempotent** | Running twice has no side effects |
| **Observable** | Detailed logs and reports for every step |
| **Fault tolerant** | Retries, exponential backoff, graceful exits |

## Coverage Expectations

| Source | Expected Coverage | Cost |
|--------|-------------------|------|
| OpenFoodFacts | 15-30% | Free |
| Rainforest API | +30-50% | ~$50/1000 calls |
| Placeholders | Remaining | Free |

For a 1000-product catalog, expect ~400-700 real images after both passes.

## Troubleshooting

**Rainforest returns 401:**
- Check `RAINFOREST_API_KEY` in `.env`
- Verify key at https://www.rainforestapi.com/dashboard

**S3 upload fails with 403:**
- Check IAM permissions: `s3:PutObject`, `s3:GetObject`, `s3:HeadObject`, `s3:HeadBucket`
- Verify bucket policy allows your IAM user

**OpenFoodFacts returns 503:**
- Rate limit too aggressive. Increase `RATE_LIMIT_SECONDS` in `.env`
- Try again later (their servers may be under load)

**All images are placeholders:**
- OpenFoodFacts has low coverage for Indian brands
- Get a Rainforest API key to fill gaps
