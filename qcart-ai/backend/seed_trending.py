"""One-time seed script — populates db.trending with sample city data.

Run:  python seed_trending.py
"""

import db

SEED_DATA = [
    {
        "city": "Bangalore",
        "product_ids": ["p001", "p002", "p010", "p020", "p033"],
    },
    {
        "city": "Chennai",
        "product_ids": ["p015", "p016", "p022", "p028", "p034"],
    },
    {
        "city": "Mumbai",
        "product_ids": ["p005", "p006", "p013", "p060", "p064"],
    },
    {
        "city": "Delhi",
        "product_ids": ["p023", "p024", "p025", "p027", "p030"],
    },
]


def seed():
    # Clear existing trending data to avoid duplicates
    db.trending.delete_many({})
    result = db.trending.insert_many(SEED_DATA)
    print(f"[OK] Seeded {len(result.inserted_ids)} city trending documents")

    # Verify
    for doc in db.trending.find({}, {"_id": 0}):
        print(f"  {doc['city']}: {doc['product_ids']}")


if __name__ == "__main__":
    seed()
