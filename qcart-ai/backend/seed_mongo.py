"""Seed MongoDB Atlas with dummy data for the QCart AI demo.

Usage:
    python seed_mongo.py              # Contract mode: trending, customers, offers only
    python seed_mongo.py --with-tags  # Demo mode: also seeds customer_tags

Contract mode leaves customer_tags EMPTY — Dev B's rule engine populates them.
Demo mode pre-fills customer_tags so Dev C can work in parallel without waiting.
"""

import sys
from pathlib import Path

import db

DATA = Path(__file__).parent / "data"


def seed_trending():
    """City-based trending product IDs."""
    docs = [
        {
            "city": "Delhi",
            "product_ids": ["p001", "p002", "p010", "p060", "p065", "p068"],
        },
        {
            "city": "Mumbai",
            "product_ids": ["p004", "p006", "p010", "p011", "p064", "p069"],
        },
        {
            "city": "Bangalore",
            "product_ids": ["p015", "p066", "p013", "p005", "p034", "p070"],
        },
        {
            "city": "Chennai",
            "product_ids": ["p016", "p020", "p021", "p030", "p031", "p046"],
        },
    ]
    db.trending.delete_many({})
    db.trending.insert_many(docs)
    return len(docs)


def seed_customers():
    """Dummy customers with distinct order patterns."""
    docs = [
        {
            "customer_id": "cust_ravi",
            "profile": {"name": "Ravi", "city": "Delhi", "veg": False},
            "order_history": [
                {"date": "2025-06-01", "items": ["p015", "p005", "p001", "p010"]},
                {"date": "2025-06-05", "items": ["p066", "p002", "p006"]},
                {"date": "2025-06-10", "items": ["p015", "p068", "p001"]},
            ],
        },
        {
            "customer_id": "cust_priya",
            "profile": {"name": "Priya", "city": "Mumbai", "veg": True},
            "order_history": [
                {"date": "2025-06-02", "items": ["p050", "p051", "p052", "p053"]},
                {"date": "2025-06-07", "items": ["p050", "p054", "p055", "p033"]},
                {"date": "2025-06-11", "items": ["p020", "p021", "p030", "p033"]},
            ],
        },
        {
            "customer_id": "cust_aarav",
            "profile": {"name": "Aarav", "city": "Bangalore", "veg": False},
            "order_history": [
                {"date": "2025-06-01", "items": ["p001", "p002", "p004", "p010"]},
                {"date": "2025-06-06", "items": ["p065", "p060", "p011", "p007"]},
                {"date": "2025-06-12", "items": ["p001", "p072", "p010", "p008"]},
            ],
        },
        {
            "customer_id": "cust_sneha",
            "profile": {"name": "Sneha", "city": "Delhi", "veg": True},
            "order_history": [
                {"date": "2025-06-03", "items": ["p020", "p021", "p022", "p023", "p030"]},
                {"date": "2025-06-08", "items": ["p024", "p025", "p026", "p027", "p031"]},
                {"date": "2025-06-13", "items": ["p020", "p029", "p033", "p034"]},
            ],
        },
        {
            "customer_id": "cust_karan",
            "profile": {"name": "Karan", "city": "Mumbai", "veg": False},
            "order_history": [
                {"date": "2025-06-02", "items": ["p034", "p035", "p036", "p045"]},
                {"date": "2025-06-09", "items": ["p013", "p047", "p033", "p075"]},
                {"date": "2025-06-12", "items": ["p034", "p045", "p022", "p075"]},
            ],
        },
        {
            "customer_id": "cust_ananya",
            "profile": {"name": "Ananya", "city": "Bangalore", "veg": False},
            "order_history": [
                {"date": "2025-06-04", "items": ["p060", "p061", "p062", "p011", "p064"]},
                {"date": "2025-06-08", "items": ["p063", "p065", "p014", "p009"]},
                {"date": "2025-06-11", "items": ["p060", "p011", "p064", "p068"]},
            ],
        },
        {
            "customer_id": "cust_rohan",
            "profile": {"name": "Rohan", "city": "Chennai", "veg": True},
            "order_history": [
                {"date": "2025-06-01", "items": ["p016", "p021", "p029", "p022"]},
                {"date": "2025-06-06", "items": ["p016", "p020", "p033", "p076"]},
                {"date": "2025-06-10", "items": ["p015", "p021", "p022", "p029"]},
            ],
        },
        {
            "customer_id": "cust_meera",
            "profile": {"name": "Meera", "city": "Chennai", "veg": True},
            "order_history": [
                {"date": "2025-06-03", "items": ["p045", "p035", "p036", "p034"]},
                {"date": "2025-06-07", "items": ["p047", "p046", "p044", "p033"]},
                {"date": "2025-06-12", "items": ["p045", "p075", "p034", "p036"]},
            ],
        },
    ]
    db.customers.delete_many({})
    db.customers.insert_many(docs)
    return len(docs)


def seed_offers():
    """Active promotional offers tied to product IDs."""
    docs = [
        {"product_id": "p001", "discount_pct": 10, "offer_label": "Movie Night Deal"},
        {"product_id": "p010", "discount_pct": 15, "offer_label": "Combo Saver"},
        {"product_id": "p050", "discount_pct": 20, "offer_label": "New Parent Bundle"},
        {"product_id": "p060", "discount_pct": 12, "offer_label": "Party Pack"},
        {"product_id": "p066", "discount_pct": 8, "offer_label": "Premium Pick"},
        {"product_id": "p020", "discount_pct": 5, "offer_label": "Daily Essential"},
        {"product_id": "p034", "discount_pct": 10, "offer_label": "Fresh Fruits"},
        {"product_id": "p045", "discount_pct": 15, "offer_label": "Wellness Week"},
    ]
    db.offers.delete_many({})
    db.offers.insert_many(docs)
    return len(docs)


def seed_customer_tags():
    """Pre-computed tags (normally generated by Dev B's rule engine).
    Only used in --with-tags mode for parallel development / demo."""
    docs = [
        {"customer_id": "cust_ravi", "tags": ["coffee_lover", "movie_buff", "snacker"], "updated_at": "2025-06-13"},
        {"customer_id": "cust_priya", "tags": ["new_parent", "vegetarian", "weekly_planner"], "updated_at": "2025-06-13"},
        {"customer_id": "cust_aarav", "tags": ["night_owl", "snacker", "party_host"], "updated_at": "2025-06-13"},
        {"customer_id": "cust_sneha", "tags": ["family_planner", "vegetarian", "bulk_buyer"], "updated_at": "2025-06-13"},
        {"customer_id": "cust_karan", "tags": ["health_conscious", "fruit_lover", "premium_buyer"], "updated_at": "2025-06-13"},
        {"customer_id": "cust_ananya", "tags": ["party_host", "entertainer", "premium_buyer"], "updated_at": "2025-06-13"},
        {"customer_id": "cust_rohan", "tags": ["tea_lover", "breakfast_routine", "budget_conscious"], "updated_at": "2025-06-13"},
        {"customer_id": "cust_meera", "tags": ["wellness_focused", "fruit_lover", "vegetarian"], "updated_at": "2025-06-13"},
    ]
    db.customer_tags.delete_many({})
    db.customer_tags.insert_many(docs)
    return len(docs)


def main():
    with_tags = "--with-tags" in sys.argv

    if not db.is_connected():
        print("ERROR: Cannot connect to MongoDB.")
        print("Make sure MONGODB_URI is set in .env")
        print("Example: MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/qcart")
        return

    print("Connected to Atlas ✓")
    print()

    if with_tags:
        print("Mode: DEMO (--with-tags)")
        print("  Seeds: trending, customers, offers, customer_tags")
    else:
        print("Mode: CONTRACT (default)")
        print("  Seeds: trending, customers, offers")
        print("  Skips: customer_tags (left empty for rule engine)")

    print()

    count = seed_trending()
    print(f"  trending:      {count} cities seeded")

    count = seed_customers()
    print(f"  customers:     {count} customers seeded")

    count = seed_offers()
    print(f"  offers:        {count} offers seeded")

    if with_tags:
        count = seed_customer_tags()
        print(f"  customer_tags: {count} tag sets seeded")
    else:
        print(f"  customer_tags: skipped (empty — awaiting rule engine)")

    print()
    print("Done! Shared database is live.")


if __name__ == "__main__":
    main()
