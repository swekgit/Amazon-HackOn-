"""Test script to verify personalization fixes.

Tests:
1. For You personalization per customer (Ananya vs Ravi vs Meera)
2. Predicted kits per customer (Meera → Period care, Ravi → Monthly groceries)
3. Smart payment offers based on cart

Run: python test_personalization.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_foryou_personalization():
    """Test 1: Verify each customer gets personalized For You recommendations."""
    print("\n" + "="*80)
    print("TEST 1: FOR YOU PERSONALIZATION (segment + city + tags)")
    print("="*80)
    
    customers = ["cust_ananya", "cust_ravi", "cust_meera"]
    cities = ["Bangalore", "Delhi", "Mumbai"]
    
    for customer, city in zip(customers, cities):
        print(f"\n--- Customer: {customer} | City: {city} ---")
        
        response = requests.get(
            f"{BASE_URL}/api/foryou",
            params={"customer_id": customer, "city": city}
        )
        
        if response.status_code != 200:
            print(f"❌ FAILED: {response.status_code} {response.text}")
            continue
        
        data = response.json()
        
        print(f"✓ Name: {data['customer']['name']}")
        print(f"✓ Segment: {data['customer']['segment']}")
        print(f"✓ Tags: {data['tags']}")
        print(f"✓ Recommended products: {len(data['recommended'])}")
        
        if data['recommended']:
            print(f"  First 3 recommendations:")
            for rec in data['recommended'][:3]:
                print(f"    - {rec['name']} (₹{rec['price']}) - {rec['reason']}")
        
        print(f"✓ Deals: {len(data['deals'])}")
        print(f"✓ Trending: {len(data['trending'])}")


def test_predicted_per_customer():
    """Test 2: Verify predicted kits are customer-specific."""
    print("\n" + "="*80)
    print("TEST 2: PREDICTED KITS PER CUSTOMER")
    print("="*80)
    
    test_cases = [
        ("cust_meera", "Period-care kit"),
        ("cust_ravi", "Monthly staples"),
        ("cust_ananya", "No predictions expected"),
    ]
    
    for customer_id, expected in test_cases:
        print(f"\n--- Customer: {customer_id} ---")
        
        response = requests.get(
            f"{BASE_URL}/api/predicted",
            params={"customer_id": customer_id}
        )
        
        if response.status_code != 200:
            print(f"❌ FAILED: {response.status_code} {response.text}")
            continue
        
        data = response.json()
        predictions = data.get("predictions", [])
        
        print(f"✓ Predictions found: {len(predictions)}")
        
        if predictions:
            for pred in predictions:
                print(f"  Kit: {pred['label']}")
                print(f"  Due in: {pred['due_in_days']} days")
                print(f"  Private: {pred['private']}")
                print(f"  Items: {len(pred['cart'])} products")
                print(f"  Subtotal: ₹{pred['subtotal']}")
                
                print(f"  Cart contents:")
                for item in pred['cart']:
                    print(f"    - {item['name']} (₹{item['price']})")
                
                if expected in pred['label']:
                    print(f"  ✅ MATCH: Got expected '{expected}'")
                else:
                    print(f"  ⚠ Got '{pred['label']}', expected '{expected}'")
        else:
            if "No predictions" in expected:
                print(f"  ✅ CORRECT: {expected}")
            else:
                print(f"  ❌ MISSING: Expected '{expected}'")


def test_smart_payment_offers():
    """Test 3: Verify payment offers are cart-aware."""
    print("\n" + "="*80)
    print("TEST 3: SMART PAYMENT OFFERS (cart-aware)")
    print("="*80)
    
    test_carts = [
        {
            "name": "Small cart (₹150)",
            "message": "add milk and bread",
            "cart": []
        },
        {
            "name": "Medium cart (₹350)",
            "message": "add coffee, chips, and cola",
            "cart": []
        },
        {
            "name": "Health context (fever)",
            "message": "I have fever, need medicine",
            "cart": []
        },
        {
            "name": "Party context (₹600)",
            "message": "party snacks for 8 people",
            "cart": []
        }
    ]
    
    for test in test_carts:
        print(f"\n--- Test: {test['name']} ---")
        print(f"Message: {test['message']}")
        
        response = requests.post(
            f"{BASE_URL}/api/cart",
            json={
                "message": test["message"],
                "cart": test["cart"]
            }
        )
        
        if response.status_code != 200:
            print(f"❌ FAILED: {response.status_code} {response.text}")
            continue
        
        data = response.json()
        
        print(f"✓ Subtotal: ₹{data['subtotal']}")
        print(f"✓ Context: {data['context']}")
        print(f"✓ Payment offers:")
        
        for offer in data.get("payment_offers", []):
            eligible_mark = "✓" if offer.get("eligible", False) else "⏳"
            print(f"  {eligible_mark} {offer['title']}")
            print(f"     {offer['detail']}")
            
            if offer.get("eligible"):
                print(f"     💰 Save: ₹{offer.get('saved_amount', 0)}")
            else:
                print(f"     📊 Gap: ₹{offer.get('gap_amount', 0)}")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("QCart Backend Personalization Tests")
    print("="*80)
    print("Testing 3 fixes:")
    print("1. For You personalization (segment + city + tags)")
    print("2. Predicted kits per customer")
    print("3. Smart payment offers (cart-aware)")
    print("="*80)
    
    try:
        # Health check
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print(f"\n❌ Backend not responding at {BASE_URL}")
            print("Start backend with: cd backend && python -m uvicorn main:app --reload")
            return
        
        print(f"✓ Backend is running at {BASE_URL}")
        
        # Run tests
        test_foryou_personalization()
        test_predicted_per_customer()
        test_smart_payment_offers()
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED")
        print("="*80)
        print("\nVerify:")
        print("✓ Different customers return different For You recommendations")
        print("✓ Meera gets Period-care kit, Ravi gets Monthly staples")
        print("✓ Payment offers adapt to cart subtotal and context")
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to {BASE_URL}")
        print("Start backend with: cd backend && python -m uvicorn main:app --reload")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
