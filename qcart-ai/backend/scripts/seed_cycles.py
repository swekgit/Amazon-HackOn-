"""Seed the customer_cycles collection with predicted reorder data.

Usage:
    python scripts/seed_cycles.py

Safe to run multiple times (idempotent via upsert).
"""

import sys
import os
from datetime import datetime, timedelta, timezone

# Allow imports from parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db

# --- Real catalog IDs (from products.json) ---
DARK_CHOCOLATE_ID = "p005"
MILK_ID = "p020"
ATTA_ID = "p024"
RICE_ID = "p023"
OIL_ID = "p025"

# New health products added for cycle-aware reorder
PADS_ID = "p101"
PAINKILLER_ID = "p102"
HOT_WATER_BAG_ID = "p103"


def seed():
    if db.customer_cycles is None:
        print("ERROR: MongoDB not connected. Set MONGODB_URI in .env")
        sys.exit(1)

    now = datetime.now(timezone.utc)

    documents = [
        {
            "customer_id": "cust_meera",
            "label": "Period-care kit",
            "item_ids": [PADS_ID, PAINKILLER_ID, DARK_CHOCOLATE_ID, HOT_WATER_BAG_ID],
            "interval_days": 28,
            "last_purchase": (now - timedelta(days=26)).isoformat(),
            "private": True,
        },
        {
            "customer_id": "cust_ravi",
            "label": "Monthly staples",
            "item_ids": [MILK_ID, ATTA_ID, RICE_ID, OIL_ID],
            "interval_days": 30,
            "last_purchase": (now - timedelta(days=28)).isoformat(),
            "private": False,
        },
    ]

    for doc in documents:
        db.customer_cycles.replace_one(
            {"customer_id": doc["customer_id"]},
            doc,
            upsert=True,
        )

    print("Seeded customer_cycles:")
    for doc in documents:
        print(f"  - {doc['customer_id']}")

    # Verification
    count = db.customer_cycles.count_documents({})
    print(f"\nVerification: customer_cycles contains {count} document(s)")


if __name__ == "__main__":
    seed()
