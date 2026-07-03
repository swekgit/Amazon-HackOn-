"""Setup script to initialize MongoDB collections for personalization testing.

Seeds:
1. Products catalog (including p101-p103 for Meera's period kit)
2. Customer cycles (Meera → Period care, Ravi → Monthly staples)
3. Customer tags (behavioral tags for personalization)

Run: python setup_personalization.py
"""

import sys
import os
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent))

import db


def seed_products():
    """Seed products from data/products.json into MongoDB."""
    print("\n" + "="*60)
    print("STEP 1: Seed Products Catalog")
    print("="*60)
    
    import json
    
    products_file = Path(__file__).parent / "data" / "products.json"
    
    if not products_file.exists():
        print(f"❌ ERROR: {products_file} not found")
        return False
    
    with open(products_file) as f:
        data = json.load(f)
    
    # Handle both list and {"products": [...]} formats
    products = data if isinstance(data, list) else data.get("products", [])
    
    if not products:
        print("❌ ERROR: No products in JSON")
        return False
    
    print(f"Loading {len(products)} products...")
    
    upserted = 0
    for product in products:
        result = db.products.update_one(
            {"id": product["id"]},
            {"$set": product},
            upsert=True
        )
        if result.upserted_id or result.modified_count:
            upserted += 1
    
    count = db.products.count_documents({})
    
    print(f"✓ Upserted: {upserted} products")
    print(f"✓ Total in DB: {count} products")
    
    # Verify critical products exist
    critical = ["p101", "p102", "p103", "p020", "p024", "p023", "p025"]
    missing = []
    for pid in critical:
        if not db.products.find_one({"id": pid}):
            missing.append(pid)
    
    if missing:
        print(f"⚠ WARNING: Missing products: {missing}")
        return False
    
    print(f"✓ Verified critical products: {critical}")
    return True


def seed_cycles():
    """Seed customer_cycles with fresh dates."""
    print("\n" + "="*60)
    print("STEP 2: Seed Customer Cycles (Predicted Reorders)")
    print("="*60)
    
    from datetime import datetime, timedelta, timezone
    
    now = datetime.now(timezone.utc)
    
    cycles = [
        {
            "customer_id": "cust_meera",
            "label": "Period-care kit",
            "item_ids": ["p101", "p102", "p005", "p103"],  # pads, painkiller, chocolate, hot water bag
            "interval_days": 28,
            "last_purchase": (now - timedelta(days=26)).isoformat(),
            "private": True,
        },
        {
            "customer_id": "cust_ravi",
            "label": "Monthly staples",
            "item_ids": ["p020", "p024", "p023", "p025"],  # milk, atta, rice, oil
            "interval_days": 30,
            "last_purchase": (now - timedelta(days=28)).isoformat(),
            "private": False,
        },
    ]
    
    for cycle in cycles:
        db.customer_cycles.replace_one(
            {"customer_id": cycle["customer_id"]},
            cycle,
            upsert=True
        )
        
        next_purchase = datetime.fromisoformat(cycle["last_purchase"].replace("Z", "+00:00")).date() + timedelta(days=cycle["interval_days"])
        due_in = (next_purchase - now.date()).days
        
        print(f"✓ {cycle['customer_id']}: {cycle['label']}")
        print(f"  - Items: {len(cycle['item_ids'])} products")
        print(f"  - Interval: {cycle['interval_days']} days")
        print(f"  - Due in: {due_in} days")
    
    count = db.customer_cycles.count_documents({})
    print(f"\n✓ Total cycles in DB: {count}")
    
    return True


def seed_customer_tags():
    """Seed customer_tags for personalization."""
    print("\n" + "="*60)
    print("STEP 3: Seed Customer Tags (For Personalization)")
    print("="*60)
    
    from datetime import datetime, timezone
    
    tags_data = [
        {
            "customer_id": "cust_ananya",
            "tags": ["coffee_lover", "premium_buyer", "breakfast_routine"],
        },
        {
            "customer_id": "cust_ravi",
            "tags": ["household_planner", "weekly_planner"],
        },
        {
            "customer_id": "cust_meera",
            "tags": ["health_conscious", "family_planner"],
        },
        {
            "customer_id": "cust_aarav",
            "tags": ["night_owl", "snacker"],
        },
        {
            "customer_id": "cust_priya",
            "tags": ["vegetarian", "health_conscious"],
        },
    ]
    
    for tag_doc in tags_data:
        db.customer_tags.update_one(
            {"customer_id": tag_doc["customer_id"]},
            {"$set": {
                "customer_id": tag_doc["customer_id"],
                "tags": tag_doc["tags"],
                "updated_at": datetime.now(timezone.utc),
            }},
            upsert=True
        )
        print(f"✓ {tag_doc['customer_id']}: {tag_doc['tags']}")
    
    count = db.customer_tags.count_documents({})
    print(f"\n✓ Total customer_tags in DB: {count}")
    
    return True


def verify_setup():
    """Verify all collections are properly seeded."""
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)
    
    checks = [
        ("products", db.products.count_documents({}), 80),  # Expect ~80+ products
        ("customer_cycles", db.customer_cycles.count_documents({}), 2),  # Meera + Ravi
        ("customer_tags", db.customer_tags.count_documents({}), 5),  # 5 demo customers
    ]
    
    all_ok = True
    
    for collection, count, expected in checks:
        status = "✓" if count >= expected else "❌"
        print(f"{status} {collection}: {count} documents (expected ≥{expected})")
        if count < expected:
            all_ok = False
    
    return all_ok


def main():
    """Run all setup steps."""
    print("\n" + "="*60)
    print("QCart Personalization Setup")
    print("="*60)
    print("This script will seed MongoDB with:")
    print("1. Products catalog (including period-care items)")
    print("2. Customer cycles (Meera + Ravi predictions)")
    print("3. Customer tags (behavioral data)")
    print("="*60)
    
    # Check MongoDB connection
    if not db.is_connected():
        print("\n❌ ERROR: MongoDB not connected")
        print("Set MONGODB_URI in .env file")
        print("Example: MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/qcart")
        return 1
    
    print("\n✓ MongoDB connected")
    
    # Run seeding steps
    steps = [
        ("Products", seed_products),
        ("Cycles", seed_cycles),
        ("Customer Tags", seed_customer_tags),
    ]
    
    for name, func in steps:
        try:
            if not func():
                print(f"\n❌ {name} seeding failed")
                return 1
        except Exception as e:
            print(f"\n❌ {name} seeding error: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    # Final verification
    if not verify_setup():
        print("\n⚠ WARNING: Some collections may not be fully seeded")
        return 1
    
    print("\n" + "="*60)
    print("✅ SETUP COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Start backend: python -m uvicorn main:app --reload")
    print("2. Run tests: python test_personalization.py")
    print("\nTest endpoints:")
    print("- GET /api/foryou?customer_id=cust_meera&city=Bangalore")
    print("- GET /api/predicted?customer_id=cust_meera")
    print("- POST /api/cart (with different cart values)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
