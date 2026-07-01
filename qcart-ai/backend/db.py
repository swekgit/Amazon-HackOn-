"""Shared MongoDB Atlas connection module.

All Mongo access goes through this file — never create a second connection.
Import collections directly:
    import db
    db.trending.find_one({"city": "Delhi"})
    db.customers.find_one({"customer_id": "cust_ravi"})
    db.customer_tags.update_one(...)
    db.offers.find({})
"""

import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "")

if MONGODB_URI:
    _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    _db = _client["qcart"]

    # Collections — the shared contract
    trending = _db["trending"]
    customers = _db["customers"]
    customer_tags = _db["customer_tags"]
    offers = _db["offers"]
    customer_cycles = _db["customer_cycles"]
    products = _db["products"]
else:
    # Graceful degradation: if no Mongo URI, expose None collections
    # This allows the existing backend to run without Mongo configured
    _client = None
    _db = None
    trending = None
    customers = None
    customer_tags = None
    offers = None
    customer_cycles = None
    products = None


def is_connected() -> bool:
    """Check if MongoDB is connected and responsive."""
    if _client is None:
        return False
    try:
        _client.admin.command("ping")
        return True
    except Exception:
        return False