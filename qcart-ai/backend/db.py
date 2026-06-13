"""Shared MongoDB connection.

Loads MONGODB_URI from .env, connects once at import time, and exposes
the database handle plus collection shortcuts.  Every other module that
needs Mongo should ``import db`` rather than creating its own client.
"""

import logging
import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

load_dotenv()

log = logging.getLogger(__name__)

MONGODB_URI = os.getenv("MONGODB_URI", "")
DB_NAME = os.getenv("MONGODB_DB", "qcart")

if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI is not set — check your .env file.")

try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    # Force a connection check so we fail fast on bad URIs
    client.admin.command("ping")
    log.info("Connected to MongoDB Atlas")
except ConnectionFailure as exc:
    log.error("MongoDB connection failed: %s", exc)
    raise

db = client[DB_NAME]

# ── Collection shortcuts ──────────────────────────────────────────────
trending = db.trending
customers = db.customers
customer_tags = db.customer_tags
offers = db.offers
