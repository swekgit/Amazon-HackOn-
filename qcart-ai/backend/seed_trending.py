"""One-time seed script — populates db.trending with sample city data.

Usage:
    python seed_trending.py

Uses 4-digit product IDs that exist in the Mongo catalog (db.products).
Does NOT modify db.products.
"""

import db

SEED_DATA = [
    {
        "city": "Bangalore",
        "product_ids": ["p0015", "p0066", "p0013", "p0005", "p0034"],
    },
    {
        "city": "Chennai",
        "product_ids": ["p0016", "p0020", "p0021", "p0030", "p0031"],
    },
    {
        "city": "Mumbai",
        "product_ids": ["p0005", "p0006", "p0013", "p0060", "p0064"],
    },
    {
        "city": "Delhi",
        "product_ids": ["p0023", "p0024", "p0025", "p0027", "p0030"],
    },
]


def seed():
    db.trending.delete_many({})
    result = db.trending.insert_many(SEED_DATA)
    print(f"[OK] Seeded {len(result.inserted_ids)} city trending documents")

    for doc in db.trending.find({}, {"_id": 0}):
        print(f"  {doc['city']}: {doc['product_ids']}")


if __name__ == "__main__":
    seed()
