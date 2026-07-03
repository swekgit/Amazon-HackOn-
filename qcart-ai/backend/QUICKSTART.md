# Personalization Fixes - Quick Start

## One-Time Setup

```bash
cd backend

# 1. Seed MongoDB with all data (products, cycles, tags)
python setup_personalization.py

# Expected output:
# ✓ Upserted: 80+ products
# ✓ cust_meera: Period-care kit (due in 2 days)
# ✓ cust_ravi: Monthly staples (due in 2 days)
# ✓ 5 customer tags seeded
```

## Start Backend

```bash
python -m uvicorn main:app --reload
```

Backend runs at `http://localhost:8000`

## Run Tests

```bash
# Automated test suite
python test_personalization.py

# Expected: Tests for For You, Predicted, Payment Offers
```

## Manual Testing

### Test 1: For You Personalization (different per customer)
```bash
# Meera (family, health_conscious)
curl "http://localhost:8000/api/foryou?customer_id=cust_meera&city=Bangalore"

# Ravi (working, household_planner)
curl "http://localhost:8000/api/foryou?customer_id=cust_ravi&city=Delhi"

# Ananya (working, coffee_lover, premium_buyer)
curl "http://localhost:8000/api/foryou?customer_id=cust_ananya&city=Mumbai"
```

**✅ Verify:** Each returns different `recommended` products with unique reasons.

### Test 2: Predicted Reorders (customer-specific kits)
```bash
# Meera → Period-care kit
curl "http://localhost:8000/api/predicted?customer_id=cust_meera"

# Ravi → Monthly staples
curl "http://localhost:8000/api/predicted?customer_id=cust_ravi"

# Other customers → Empty predictions
curl "http://localhost:8000/api/predicted?customer_id=cust_ananya"
```

**✅ Verify:** 
- Meera: `"label": "Period-care kit"`, cart has pads (p101), painkiller (p102), chocolate (p005), hot water bag (p103)
- Ravi: `"label": "Monthly staples"`, cart has milk (p020), atta (p024), rice (p023), oil (p025)

### Test 3: Smart Payment Offers (cart-aware)
```bash
# Small cart (₹150) → shows gaps
curl -X POST http://localhost:8000/api/cart \
  -H "Content-Type: application/json" \
  -d '{"message": "add milk and bread", "cart": []}'

# Large cart (₹350+) → shows eligible offers
curl -X POST http://localhost:8000/api/cart \
  -H "Content-Type: application/json" \
  -d '{"message": "add coffee, chips, cola, and pizza", "cart": []}'

# Health context → bonus health offer
curl -X POST http://localhost:8000/api/cart \
  -H "Content-Type: application/json" \
  -d '{"message": "I have fever, need medicine", "cart": []}'

# Party context → bonus party offer
curl -X POST http://localhost:8000/api/cart \
  -H "Content-Type: application/json" \
  -d '{"message": "party snacks for 8 people", "cart": []}'
```

**✅ Verify:** `payment_offers` array shows:
- Different `eligible`/`gap_amount` based on subtotal
- Savings calculated dynamically
- Context-specific bonus offers

## Troubleshooting

### MongoDB not connected
```bash
# Check .env file has:
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/qcart

# Test connection:
python -c "import db; print('Connected' if db.is_connected() else 'Failed')"
```

### Products not found (p101-p103)
```bash
# Re-seed products:
python seed_catalog.py

# Verify:
python -c "import catalog; print(catalog.get('p101'))"
```

### Predictions not showing
```bash
# Re-seed with fresh dates:
python scripts/seed_cycles.py

# Check cycles:
python -c "import db; print(list(db.customer_cycles.find({}, {'_id': 0})))"
```

## What Changed

**Modified Files:**
- `main.py` - 4 functions updated, 1 function added
- `seed_catalog.py` - Fixed JSON loading bug

**New Files:**
- `setup_personalization.py` - All-in-one seeding
- `test_personalization.py` - Automated tests
- `PERSONALIZATION_FIXES.md` - Full documentation
- `QUICKSTART.md` - This file

**Untouched (still works):**
- Recipe flow (`/api/cart` with recipe detection)
- Brain/RAG (semantic search, LLM)
- Gap engine (free delivery nudges)
- Trending (city-based)
- Cache (response caching)

## Success Criteria ✅

- [x] Different customers → different For You feeds
- [x] Meera → Period-care kit prediction
- [x] Ravi → Monthly staples prediction
- [x] Payment offers adapt to cart value
- [x] Recipe/cart/RAG flow still works

---

Ready to test! 🚀
