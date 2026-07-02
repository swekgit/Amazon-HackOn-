"""calibrate_thresholds.py — data-driven SIM_FLOOR / RESOLVE_MARGIN calibration.

Run with gates off to print true-cosine scores and group winners, then derive
thresholds from correct English probes only.

Run:
    cd qcart-ai/backend
    python calibrate_thresholds.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))
from dotenv import load_dotenv

load_dotenv()

import catalog as _cat

# ── Bypass gates for calibration only ────────────────────────────────────────
_orig_floor = _cat.SIM_FLOOR
_orig_margin = _cat.RESOLVE_MARGIN
_cat.SIM_FLOOR = 0.0
_cat.RESOLVE_MARGIN = 1.0

# English probes used for threshold derivation (Hindi may go unmatched — OK)
ENGLISH_PROBES = {
    "carrots", "carrot", "sugar", "ghee", "milk", "paneer", "rice",
    "cashew", "almond", "tomato", "onion", "potato", "tea",
}


def probe(ingredient: str, expected_group: str) -> dict | None:
    try:
        qvec = _cat.embed([ingredient], "search_query")[0]
        hits = _cat._knn_search(qvec, _cat.RESOLVE_K)
    except Exception as e:
        print(f"  {ingredient!r:18s}  ERROR: {e}")
        return None

    group_max, group_sum, _ = _cat._group_hits_by_swap_group(hits)
    ranked = _cat._rank_swap_groups(group_max, group_sum)
    best_grp = ranked[0]
    runner_grp = ranked[1] if len(ranked) > 1 else "—"
    best_sim = group_max[best_grp]
    runner_max = group_max[runner_grp] if len(ranked) > 1 else 0.0
    margin = best_sim / runner_max if runner_max > 0 else 999.0
    correct = best_grp == expected_group

    status = "✅ CORRECT" if correct else f"❌ WRONG (expected {expected_group})"
    print(
        f"  {ingredient!r:18s}"
        f"  best_sim={best_sim:.4f}"
        f"  runner_max={runner_max:.4f}"
        f"  margin={margin:.2f}"
        f"  winner={best_grp:20s}"
        f"  {status}"
    )
    return {
        "ingredient": ingredient,
        "expected": expected_group,
        "got": best_grp,
        "best_sim": best_sim,
        "runner_max": runner_max,
        "margin": margin,
        "correct": correct,
    }


GOOD = [
    ("carrots", "carrot"),
    ("carrot", "carrot"),
    ("gajar", "carrot"),
    ("khoya", "khoya"),
    ("mawa", "khoya"),
    ("sugar", "sugar"),
    ("ghee", "ghee"),
    ("milk", "milk"),
    ("paneer", "paneer"),
    ("rice", "rice"),
    ("cashew", "cashews"),
    ("almond", "almonds"),
    ("tomato", "tomato"),
    ("onion", "onion"),
    ("potato", "potato"),
    ("flour", "atta"),
    ("tea", "tea"),
    ("besan", "besan"),
]

BAD = [
    ("sugar", "sugar"),
    ("cashew", "cashews"),
    ("milk", "milk"),
]

print("=" * 100)
print("CALIBRATION  (SIM_FLOOR=0.0 / MARGIN=1.0 — gates off, true cosine scores)")
print(f"Index: {_cat._OS_ENDPOINT}  k={_cat.RESOLVE_K}")
print("=" * 100)

print("\n── GOOD PROBES ──")
results = [probe(ing, grp) for ing, grp in GOOD]
results = [r for r in results if r]

correct = [r for r in results if r["correct"]]
wrong = [r for r in results if not r["correct"]]
english_correct = [r for r in correct if r["ingredient"] in ENGLISH_PROBES]

print(f"\n── SUMMARY ──")
print(f"  Correct: {len(correct)}/{len(results)}")
if wrong:
    print(f"  Wrong:   {len(wrong)}")
    for r in wrong:
        print(f"    {r['ingredient']!r} → {r['got']!r} (expected {r['expected']!r})")

if english_correct:
    min_sim = min(r["best_sim"] for r in english_correct)
    min_margin = min(r["margin"] for r in english_correct)
    rec_floor = min_sim * 0.95
    rec_margin = min_margin * 0.90
    print(f"\n  English correct probes: {len(english_correct)}")
    print(f"  Lowest max-cosine among English correct: {min_sim:.4f}")
    print(f"  Lowest winner/runner-up ratio among English correct: {min_margin:.4f}")
    print(f"\n  ► Recommended SIM_FLOOR      = {rec_floor:.4f}  (min English correct * 0.95)")
    print(f"  ► Recommended RESOLVE_MARGIN = {rec_margin:.4f}  (min ratio * 0.90)")

print("\n── BAD PROBES (verify no wrong swap_group is chosen) ──")
for ing, grp in BAD:
    probe(ing, grp)

print()
print(f"Current code:  SIM_FLOOR={_orig_floor}  RESOLVE_MARGIN={_orig_margin}")

_cat.SIM_FLOOR = _orig_floor
_cat.RESOLVE_MARGIN = _orig_margin
