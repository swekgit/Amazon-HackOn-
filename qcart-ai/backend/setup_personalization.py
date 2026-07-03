"""Setup script to initialize MongoDB collections for personalization testing.

Seeds:
1. Customer cycles (Meera → Period care, Ravi → Monthly staples)
2. Customer tags (behavioral tags for personalization)

Does NOT touch db.products — catalog is loaded separately (1000-product Mongo seed).

Run: python setup_personalization.py
"""

import sys
import os
from pathlib import Path

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent))

import db


def seed_cycles():
    """Seed customer_cycles with fresh dates."""
    print("\n" + "="*60)
    print("STEP 1: Seed Customer Cycles (Predicted Reorders)")
    print("="*60)
    
    from datetime import datetime, timedelta, timezone
    
    now = datetime.now(timezone.utc)
    
    cycles = [
        {
            "customer_id": "cust_meera",
            "label": "Period-care kit",
            "item_ids": [
                "p0390",  # Stayfree Secure XL Sanitary Pads
                "p0402",  # Dolo 650mg
                "p0127",  # Cadbury Dairy Milk Chocolate
                "p0808",  # Hot Water Bag
            ],
            "interval_days": 28,
            "last_purchase": (now - timedelta(days=26)).isoformat(),
            "private": True,
        },
        {
            "customer_id": "cust_ravi",
            "label": "Monthly staples",
            "item_ids": [
                "p0007",  # Mother Dairy Full Cream Milk (1L)
                "p0088",  # Patanjali Whole Wheat Atta (5kg)
                "p0013",  # India Gate Classic Basmati Rice (1kg)
                "p0058",  # Fortune Sunlite Refined Sunflower Oil (1L)
            ],
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
    print("STEP 2: Seed Customer Tags (For Personalization)")
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
    print("1. Customer cycles (Meera + Ravi predictions)")
    print("2. Customer tags (behavioral data)")
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
