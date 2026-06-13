"""Demo script — run the rule engine against customers in MongoDB.

Usage:
    python demo_rule_engine.py

Requires MONGODB_URI set in .env and customers seeded via seed_mongo.py.
"""

import sys
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv()

import db
import rule_engine


DEMO_CUSTOMERS = [
    "cust_ravi",
    "cust_priya",
    "cust_aarav",
    "cust_sneha",
    "cust_karan",
    "cust_ananya",
    "cust_rohan",
    "cust_meera",
]


def main():
    if not db.is_connected():
        print("ERROR: Cannot connect to MongoDB.")
        print("Make sure MONGODB_URI is set in .env and seed_mongo.py has been run.")
        return

    print("QCart AI Rule Engine Demo")
    print("=" * 50)
    print()

    for customer_id in DEMO_CUSTOMERS:
        doc = db.customers.find_one({"customer_id": customer_id})
        if not doc:
            print(f"  {customer_id}: NOT FOUND in database")
            continue

        tags = rule_engine.generate_tags(doc)
        name = doc.get("profile", {}).get("name", customer_id)
        print(f"  {name} ({customer_id})")
        print(f"    Tags: {tags}")
        print()

    print("Done.")


if __name__ == "__main__":
    main()
