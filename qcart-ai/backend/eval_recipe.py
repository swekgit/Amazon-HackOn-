"""eval_recipe.py — end-to-end evaluation of the recipe-to-cart feature.

Runs 20 queries through:
    detect_recipe()  →  handle_recipe()  (mirrors main.py _handle_recipe exactly)

Prints per query:
    dish, servings, already_have detected by LLM
    CART:      name  id  swap_group  category  price
    SKIPPED:   ingredient — why (already have)
    UNMATCHED: ingredients that resolve_ingredient returned None for (no confident
               vector match — correctly omitted rather than adding a wrong product)

Acceptance criteria checked inline for query #1.

Run:
    cd qcart-ai/backend
    python eval_recipe.py
"""

import os, sys
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))
from dotenv import load_dotenv; load_dotenv()

import brain
import catalog


def handle_recipe(recipe_meta: dict) -> dict:
    """Exact mirror of main.py _handle_recipe — no special-casing."""
    dish     = recipe_meta["dish"] or "the dish"
    servings = int(recipe_meta["servings"] or 2)

    # Resolve already-have items to swap_groups
    have_groups: set[str] = set()
    for item in recipe_meta.get("already_have", []):
        r = catalog.resolve_ingredient(item)
        if r:
            have_groups.add(r["swap_group"])

    ingredients = brain.extract_recipe_ingredients(dish, servings)

    cart_product_ids: set[str] = set()
    cart_lines:       list     = []
    skipped:          list     = []
    unmatched:        list     = []

    for ing in ingredients:
        r = catalog.resolve_ingredient(ing)
        if not r:
            unmatched.append(ing)
            continue
        if r["swap_group"] in have_groups:
            skipped.append({"name": ing, "why": "already have",
                            "swap_group": r["swap_group"]})
            continue
        best = r["product"]
        if best["id"] in cart_product_ids:
            continue
        line = catalog.enrich(best["id"], 1, f"for {dish}")
        if not line:
            unmatched.append(ing)
            continue
        line["alternatives"] = catalog.find_alternatives(best["id"], cart_product_ids)
        cart_product_ids.add(best["id"])
        cart_lines.append({"line": line, "swap_group": r["swap_group"]})

    return {
        "dish": dish, "servings": servings,
        "have_groups": have_groups,
        "cart": cart_lines, "skipped": skipped, "unmatched": unmatched,
    }


QUERIES = [
    "gajar ka halwa for 4, ghee already hai",           # Q1
    "gajar ka halwa for 6",                              # Q2
    "kheer for 4, rice and milk already have",           # Q3
    "gulab jamun for 8",                                 # Q4
    "besan ladoo for 4, sugar already have",             # Q5
    "paneer butter masala for 2",                        # Q6
    "veg biryani for 6, rice already have",              # Q7
    "poha for 2",                                        # Q8
    "tea for 4, milk and sugar already have",            # Q9
    "carrot halwa",                                      # Q10
    "aloo paratha for 4, flour already have",            # Q11
    "dal tadka for 4",                                   # Q12
    "cold coffee for 2",                                 # Q13
    "rajma chawal for 6, rice already have",             # Q14
    "mawa barfi for 4",                                  # Q15
    "badam milk for 2",                                  # Q16
    "pasta for 4, olive oil already have",               # Q17
    "halwa with dry fruits for 4",                       # Q18
    "sooji halwa for 2, ghee already have",              # Q19
    "french fries, potato already have",                 # Q20
]

# Acceptance criteria for Q1
Q1_MUST_HAVE_GROUPS = {"carrot", "khoya", "sugar", "milk"}
Q1_MUST_SKIP_GROUPS = {"ghee"}
Q1_MUST_NOT_HAVE    = {"ghee"}


def check_q1(result: dict) -> None:
    cart_groups = {r["swap_group"] for r in result["cart"]}
    skip_groups = {s["swap_group"] for s in result["skipped"]}
    missing  = Q1_MUST_HAVE_GROUPS - cart_groups
    not_skip = Q1_MUST_SKIP_GROUPS - skip_groups
    wrong    = cart_groups & Q1_MUST_NOT_HAVE
    ok = not missing and not not_skip and not wrong
    print(f"\n  Q1 ACCEPTANCE: {'✅ PASS' if ok else '❌ FAIL'}")
    if missing:
        print(f"    MISSING from cart: {missing}")
    if not_skip:
        print(f"    NOT SKIPPED: {not_skip}")
    if wrong:
        print(f"    WRONG PRODUCT IN CART (should be skipped): {wrong}")


def run():
    print("=" * 90)
    print("QCART AI — Recipe-to-Cart Eval  (20 queries)")
    print(f"  SIM_FLOOR={catalog.SIM_FLOOR}  "
          f"RESOLVE_MARGIN={catalog.RESOLVE_MARGIN}  "
          f"RESOLVE_K={catalog.RESOLVE_K}")
    print("=" * 90)

    for i, query in enumerate(QUERIES, 1):
        print(f"\n{'─'*90}")
        print(f"Q{i:02d}: {query}")
        print("─" * 90)

        meta = brain.detect_recipe(query)
        print(f"  is_recipe={meta['is_recipe']}  dish={meta['dish']!r}  "
              f"servings={meta['servings']}  already_have={meta['already_have']}")

        if not meta["is_recipe"]:
            print("  ⚠ NOT detected as recipe")
            continue

        result = handle_recipe(meta)

        if result["have_groups"]:
            print(f"  have_groups resolved: {result['have_groups']}")

        print(f"\n  CART ({len(result['cart'])} items):")
        for r in result["cart"]:
            line = r["line"]
            p    = catalog.BY_ID.get(line["id"], {})
            print(
                f"    [{line['id']}] {line['name']:<48s}"
                f"  sg={p.get('swap_group','?'):<22s}"
                f"  cat={p.get('category','?'):<18s}"
                f"  ₹{line['price']}"
            )

        if result["skipped"]:
            print(f"\n  SKIPPED ({len(result['skipped'])}):")
            for s in result["skipped"]:
                print(f"    {s['name']:<20s}  sg={s['swap_group']:<20s}  — {s['why']}")

        if result["unmatched"]:
            print(f"\n  UNMATCHED (no confident vector match — correctly omitted):")
            for u in result["unmatched"]:
                print(f"    {u}")

        if i == 1:
            check_q1(result)

    print("\n" + "=" * 90)
    print("EVAL COMPLETE")
    print("=" * 90)


if __name__ == "__main__":
    run()
