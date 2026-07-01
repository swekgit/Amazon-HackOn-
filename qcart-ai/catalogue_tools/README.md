# QCart AI -- Product Image Pipeline

Production-ready multi-source pipeline to download, validate, and deploy product images for the QCart AI platform.

## Architecture

```
OpenFoodFacts (free)
       |
Google Custom Search (paid, image search)
       |
SerpAPI (Google Shopping + Images)
       |
Placeholder (guarantees 100%)
       |
Verify Dataset
       |
Generate Status
       |
Upload to S3 --> CloudFront CDN
```

Note: Rainforest API and Bing are available but temporarily bypassed.
To re-enable, run `python download_rainforest.py` or `python download_bing_images.py` manually.

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

| Variable | Description | How to get |
|----------|-------------|------------|
| `RAINFOREST_API_KEY` | Rainforest API key | https://www.rainforestapi.com |
| `GOOGLE_API_KEY` | Google Cloud API key | https://console.cloud.google.com/apis/credentials |
| `GOOGLE_SEARCH_ENGINE_ID` | Custom Search Engine ID | https://cse.google.com/cse/ (create engine, enable Image search) |
| `BING_API_KEY` | Bing Search v7 key | https://portal.azure.com (Cognitive Services > Bing Search v7) |
| `SERP_API_KEY` | SerpAPI key | https://serpapi.com/dashboard |
| `AWS_REGION` | AWS region (default: ap-south-1) | |
| `S3_BUCKET` | S3 bucket name | |
| `CLOUDFRONT_URL` | CloudFront URL | |

Verify config:
```bash
python config.py
```

## Execution Order

### Step 1: OpenFoodFacts (Free)
```bash
python download_openfoodfacts.py
```
- Downloads from OpenFoodFacts (free, ~15-30% coverage for Indian products)
- Creates `logs/downloaded_products.json` and `logs/missing_products.json`

### Step 2: Google Custom Search (Paid)
```bash
python download_google_images.py
```
- Only processes remaining missing products
- Image-specific search with quality filtering
- Budget cap: 100 API calls per run

### Step 3: SerpAPI (Google Shopping + Images)
```bash
python download_serpapi.py
```
- Tries Google Shopping first (better product images)
- Falls back to Google Images
- Budget cap: 100 API calls per run

### Step 4: Fill Placeholders (Guarantees 100% coverage)
```bash
python fill_placeholders.py
```
- Copies `placeholder.jpg` for any remaining gaps
- After this step, every product has an image

### Step 5: Verify Dataset Integrity
```bash
python verify_dataset.py
```
- Checks: duplicates, missing files, corrupt JPEGs, orphans
- Generates `logs/verification_report.json`

### Step 6: Generate Status Report
```bash
python generate_status.py
```
- Creates `PIPELINE_STATUS.md` with full breakdown by source

### Step 7: Upload to S3
```bash
aws configure  # first time only
python upload_s3.py
```
- Skips files already in S3, parallel uploads, retry with backoff

### Step 8: CloudFront Distribution
Create via AWS Console or CLI:
```bash
aws cloudfront create-distribution \
  --origin-domain-name qcart-product-images.s3.ap-south-1.amazonaws.com \
  --default-root-object index.html
```

### Optional: Re-enable Rainforest or Bing
These scripts still work and can be inserted before Google if needed:
```bash
python download_rainforest.py   # requires RAINFOREST_API_KEY
python download_bing_images.py  # requires BING_API_KEY
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
| Google Custom Search | +20-40% | $5/1000 queries |
| SerpAPI | +10-25% | $50/5000 searches |
| Placeholders | Remaining | Free |

For a 1000-product catalog, expect ~500-800 real images after all passes.

## Troubleshooting

**Google returns 403:**
- Quota exceeded. Wait 24 hours or increase quota in Google Cloud Console.
- Verify `GOOGLE_API_KEY` and `GOOGLE_SEARCH_ENGINE_ID` are correct.

**SerpAPI returns empty results:**
- Check `SERP_API_KEY` at https://serpapi.com/dashboard
- Verify remaining credits.

**S3 upload fails with 403:**
- Check IAM permissions: `s3:PutObject`, `s3:GetObject`, `s3:HeadObject`, `s3:HeadBucket`
- Verify bucket policy allows your IAM user.

**OpenFoodFacts returns 503:**
- Rate limit too aggressive. Increase `RATE_LIMIT_SECONDS` in `.env`.
- Try again later (their servers may be under load).

**All images are placeholders:**
- OpenFoodFacts has low coverage for Indian brands.
- Set up Google and SerpAPI keys to fill gaps.

**Want to re-enable Rainforest?**
- Set `RAINFOREST_API_KEY` in `.env`
- Run `python download_rainforest.py` before `download_google_images.py`
