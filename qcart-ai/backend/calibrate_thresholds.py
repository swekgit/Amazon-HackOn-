"""calibrate_thresholds.py — data-driven SIM_FLOOR / RESOLVE_MARGIN calibration.

Run AFTER a clean index rebuild (normalize=True, faiss+innerproduct).
Temporarily sets SIM_FLOOR=0.0 and RESOLVE_MARGIN=1.0 so all matches
are printed with raw scores — then you read the table to pick thresholds.

IMPORTANT — probe strings are in USER / LLM language (what extract_recipe_ingredients
actually returns), NOT the catalog's swap_group strings.  The resolver must bridge
from user language to the correct swap_group via embeddings on its own.  Using the
swap_group string as the probe input would hide real recall failures.

Examples of this principle:
  probe "cashew"  → expected swap_group "cashews"   (singular → plural group)
  probe "flour"   → expected swap_group "atta"       (English word → Hindi group name)
  probe "almond"  → expected swap_group "almonds"

If any GOOD probe resolves to the wrong group on the clean index, fix it by
raising RESOLVE_K (better recall) or adjusting SIM_FLOOR — NEVER by renaming
the probe to the answer string.

Run:
    cd qcart-ai/backend
    python calibrate_thresholds.py
"""

import os, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))
from dotenv import load_dotenv; load_dotenv()

import catalog as _cat

# ── Bypass gates for calibration only ────────────────────────────────────────
_orig_floor  = _cat.SIM_FLOOR
_orig_margin = _cat.RESOLVE_MARGIN
_cat.SIM_FLOOR      = 0.0
_cat.RESOLVE_MARGIN = 1.0


def probe(ingredient: str, expected_group: str):
    try:
        qvec = _cat.embed([ingredient], "search_query")[0]
        hits = _cat._knn_search(qvec, _cat.RESOLVE_K)
    except Exception as e:
        print(f"  {'ingredient'!r:22s}  ERROR: {e}")
        return None

    gs = defaultdict(float)
    gh = defaultdict(list)
    for h in hits:
        p  = h["product"]
        sg = p.get("swap_group") or f'__solo::{p["id"]}'
        gs[sg] += h["score"]
        gh[sg].append(h)

    ranked = sorted(gs.items(), key=lambda kv: -kv[1])
    best_grp, best_sum   = ranked[0]
    sec_grp, sec_sum     = ranked[1] if len(ranked) > 1 else ("—", 0.0)
    best_sim = max(h["score"] for h in gh[best_grp])
    margin   = best_sum / sec_sum if sec_sum > 0 else 999.0
    correct  = best_grp == expected_group

    status = "✅ CORRECT" if correct else f"❌ WRONG (expected {expected_group})"
    print(
        f"  {ingredient!r:18s}"
        f"  best_sim={best_sim:.4f}"
        f"  grp_sum={best_sum:.4f}"
        f"  margin={margin:.2f}"
        f"  winner={best_grp:20s}"
        f"  {status}"
    )
    return {"ingredient": ingredient, "expected": expected_group,
            "got": best_grp, "best_sim": best_sim,
            "grp_sum": best_sum, "margin": margin, "correct": correct}


# Swap_group names are EXACT strings from MongoDB (verified by prior query)
GOOD = [
    ("carrots",   "carrot"),
    ("carrot",    "carrot"),
    ("gajar",     "carrot"),       # Hindi — may land in unmatched; that's OK
    ("khoya",     "khoya"),
    ("mawa",      "khoya"),        # Hindi synonym
    ("sugar",     "sugar"),
    ("ghee",      "ghee"),
    ("milk",      "milk"),
    ("paneer",    "paneer"),
    ("rice",      "rice"),
    ("cashew",    "cashews"),      # user/LLM says singular → must reach swap_group "cashews"
    ("almond",    "almonds"),      # user/LLM says singular → must reach swap_group "almonds"
    ("tomato",    "tomato"),
    ("onion",     "onion"),
    ("potato",    "potato"),
    ("flour",     "atta"),         # user/LLM says "flour" → must reach swap_group "atta"
    ("tea",       "tea"),          # user/LLM says "tea" → must reach swap_group "tea"
    ("besan",     "besan"),        # Hindi stays as-is
]

BAD = [
    # These must resolve to the CORRECT group, not a wrong one
    ("sugar",     "sugar"),        # must NOT be cold_drinks
    ("cashew",    "cashews"),      # must NOT be seeds/cookies
    ("milk",      "milk"),         # must NOT be plant_milk
]

print("=" * 100)
print(f"CALIBRATION  (SIM_FLOOR=0.0 / MARGIN=1.0 — gates off)")
print(f"Index: {_cat._OS_ENDPOINT}  k={_cat.RESOLVE_K}")
print("=" * 100)

print("\n── GOOD PROBES (must resolve to expected group) ──")
results = [probe(ing, grp) for ing, grp in GOOD if probe]
results = [r for r in results if r]

correct   = [r for r in results if r["correct"]]
wrong     = [r for r in results if not r["correct"]]

print(f"\n── SUMMARY ──")
print(f"  Correct: {len(correct)}/{len(results)}")
if wrong:
    print(f"  Wrong:   {len(wrong)} → these will land in unmatched after gates are applied")

if correct:
    min_sim    = min(r["best_sim"] for r in correct)
    min_margin = min(r["margin"]   for r in correct)
    print(f"\n  Lowest best_sim   among correct matches: {min_sim:.4f}")
    print(f"  Lowest margin     among correct matches: {min_margin:.4f}")
    print(f"\n  ► Recommended SIM_FLOOR   = {min_sim * 0.97:.4f}  (3% below min correct)")
    print(f"  ► Recommended RESOLVE_MARGIN = {min_margin * 0.90:.4f}  (10% below min correct margin)")

print("\n── BAD PROBES (verify no wrong swap_group is chosen) ──")
for ing, grp in BAD:
    probe(ing, grp)

print()
print(f"Current code:  SIM_FLOOR={_orig_floor}  RESOLVE_MARGIN={_orig_margin}")
print("Update RESOLVE_K / SIM_FLOOR / RESOLVE_MARGIN in catalog.py after reading the table above.")

# Restore
_cat.SIM_FLOOR      = _orig_floor
_cat.RESOLVE_MARGIN = _orig_margin
