"""
Seed Product Catalog into MongoDB Atlas
=========================================
Reads data/products.json and upserts all products into the
shared MongoDB 'products' collection.

Safe to re-run: uses upsert by product id (no duplicates).

Usage:
  python seed_catalog.py
"""

import json
import sys
from pathlib import Path

import db

DATA = Path(__file__).parent / "data"
PRODUCTS_FILE = DATA / "products.json"


def main():
    # Check MongoDB connection
    if not db.is_connected():
        print("=" * 60)
        print("MongoDB not configured.")
        print("Set MONGODB_URI in .env first.")
        print("=" * 60)
        sys.exit(1)

    # Load JSON
    if not PRODUCTS_FILE.exists():
        print(f"ERROR: {PRODUCTS_FILE} not found.")
        sys.exit(1)

    with open(PRODUCTS_FILE, encoding="utf-8") as f:
        json_data = json.load(f)

    # products.json is a raw list OR {"products": [...]}
    if isinstance(json_data, list):
        products = json_data
    else:
        products = json_data.get("products", [])
    print(f"Loaded JSON: {len(products)} products")

    if not products:
        print("ERROR: No products found in JSON file.")
        sys.exit(1)

    # Upsert every product
    upserted = 0
    for product in products:
        result = db.products.update_one(
            {"id": product["id"]},
            {"$set": product},
            upsert=True,
        )
        if result.upserted_id or result.modified_count:
            upserted += 1

    print(f"Inserted/Updated: {upserted}")

    # Verify count
    count = db.products.count_documents({})
    print(f"Mongo count: {count}")

    if count == len(products):
        print(f"\nSUCCESS: Mongo contains {count} products.")
    else:
        print(f"\nWARNING: Expected {len(products)}, Found {count}")


if __name__ == "__main__":
    main()