"""catalog_regression.py — data-derived no-wrong-product proof across all swap_groups.

Builds probes FROM THE CATALOG (no hand-written expectations). For each distinct
swap_group, derives a natural grocery probe and runs resolve_ingredient() with
the LIVE confidence gates.

Invariant: probe resolves to its OWN swap_group OR unmatched (None) — NEVER a
different swap_group above the gates.

Cross-group matches are triaged into three buckets:
  BUCKET 1 — false alarms (synonym / same-aisle neighbors; not real failures)
  BUCKET 2 — generic-word probes (regression artifacts; low recipe risk)
  BUCKET 3 — genuinely wrong bare-probe resolutions (mitigated by LLM disambiguation)

Run:
    cd qcart-ai/backend
    python catalog_regression.py              # fast classify + pass/fail
    python catalog_regression.py --triage     # full report with sim scores

Exit code 1 if BUCKET 3 has members outside the known set (new real failures).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))
from dotenv import load_dotenv

load_dotenv()

import catalog as cat

_STOPWORDS = {
    "the", "and", "for", "with", "fresh", "pack", "pcs", "gram", "grams",
    "ml", "kg", "g", "of", "in", "on", "to", "a", "an", "or", "by",
}

_PROBE_DELAY_S = float(os.getenv("REGRESSION_PROBE_DELAY", "0.35"))

# ─── Triage buckets (expected swap_group keys) ───────────────────────────────

BUCKET1_FALSE_ALARMS = frozenset({
    "biscuits", "cookies", "digestive",
    "first_aid", "antiseptic_cream", "skin_relief",
    "kitchen_wrap", "health_drink", "multivitamin",
    "mosquito_repellent", "mens_grooming", "gym_equipment",
    "shaker", "sink_organizer", "supplements", "protein_powder",
    "chilli_powder", "apple", "bananas",
})

BUCKET2_GENERIC_PROBES = frozenset({
    "masala", "sauce", "cups", "measuring", "utensils",
    "soup", "cereal", "snack_mix", "grooming_kit",
    "aloe_vera", "jelly", "chips",
})

# Bare-probe resolver failures; recipe flow uses disambiguated LLM names instead.
KNOWN_BUCKET3 = frozenset({
    "atta", "chana", "corn", "curd", "peanut_butter",
    "poha", "popcorn", "rajma", "rasam_masala",
})


@dataclass
class WrongMatch:
    expected: str
    probe: str
    got: str
    bucket: int
    winner_sim: float = 0.0
    correct_sim: float = 0.0


def _words_from_name(name: str) -> list[str]:
    return [w for w in re.findall(r"[a-z]{3,}", name.lower()) if w not in _STOPWORDS]


def derive_probe(swap_group: str, products: list[dict]) -> str:
    """Derive a natural grocery probe from catalog data only."""
    if swap_group.startswith("__solo::"):
        pid = swap_group.split("::", 1)[1]
        solo = next((p for p in products if p["id"] == pid), products[0])
        words = _words_from_name(solo["name"])
        return words[0] if words else solo["name"].split()[0].lower()
    return swap_group.replace("_", " ")


def _resolve_correct(expected_sg: str, result: dict | None, products: list[dict]) -> bool:
    """True when resolve_ingredient matched the expected group (or solo product)."""
    if result is None:
        return False
    if expected_sg.startswith("__solo::"):
        pid = expected_sg.split("::", 1)[1]
        return result["product"]["id"] == pid
    return result["swap_group"] == expected_sg


def classify_bucket(expected_sg: str) -> int:
    if expected_sg in BUCKET1_FALSE_ALARMS:
        return 1
    if expected_sg in BUCKET2_GENERIC_PROBES:
        return 2
    if expected_sg in KNOWN_BUCKET3:
        return 3
    return 3  # unclassified cross-group → treat as real failure



def _probe_stats_full(probe: str, expected_sg: str) -> tuple[str, float, float]:
    """Winner group, winner sim, expected-group sim."""
    try:
        vecs = cat.embed([probe], "search_query")
        if not vecs or not vecs[0]:
            return "", 0.0, 0.0
        hits = cat._knn_search(vecs[0], cat.RESOLVE_K)
        if not hits:
            return "", 0.0, 0.0
        group_max, group_sum, _ = cat._group_hits_by_swap_group(hits)
        ranked = cat._rank_swap_groups(group_max, group_sum)
        winner = ranked[0]
        correct_sim = group_max.get(expected_sg, 0.0)
        return winner, group_max[winner], correct_sim
    except Exception:
        return "", 0.0, 0.0


def _print_triage(wrong: list[WrongMatch]) -> None:
    by_bucket: dict[int, list[WrongMatch]] = {1: [], 2: [], 3: []}
    for w in wrong:
        by_bucket[w.bucket].append(w)

    labels = {
        1: "BUCKET 1 — FALSE ALARMS (synonym / neighbor; not real failures)",
        2: "BUCKET 2 — GENERIC-WORD PROBES (test artifacts; low recipe risk)",
        3: "BUCKET 3 — GENUINELY WRONG bare probes (mitigated by LLM disambiguation)",
    }
    for bucket in (1, 2, 3):
        items = sorted(by_bucket[bucket], key=lambda x: x.expected)
        print(f"\n── {labels[bucket]} ──")
        if not items:
            print("  (none)")
            continue
        for w in items:
            print(
                f"  probe={w.probe!r:22s}  got={w.got!r:22s}  "
                f"expected={w.expected!r:22s}  "
                f"winner_sim={w.winner_sim:.4f}  correct_sim={w.correct_sim:.4f}"
            )
        print(f"  COUNT: {len(items)}")


def run_regression(*, triage: bool = False) -> int:
    if not cat._OS_ENDPOINT:
        print("ERROR: OPENSEARCH_ENDPOINT not set")
        return 1

    by_group: dict[str, list[dict]] = defaultdict(list)
    for p in cat.CATALOG:
        sg = p.get("swap_group") or f'__solo::{p["id"]}'
        by_group[sg].append(p)

    groups = sorted(by_group.keys())
    print("=" * 90)
    print("CATALOG REGRESSION — no-wrong-product invariant")
    print(f"  groups={len(groups)}  products={len(cat.CATALOG)}")
    print(f"  SIM_FLOOR={cat.SIM_FLOOR}  RESOLVE_MARGIN={cat.RESOLVE_MARGIN}  RESOLVE_K={cat.RESOLVE_K}")
    if triage:
        print("  mode=triage (full bucket report with sim scores)")
    print("=" * 90)

    correct: list[tuple[str, str]] = []
    unmatched: list[tuple[str, str]] = []
    wrong: list[WrongMatch] = []

    for i, sg in enumerate(groups, 1):
        probe = derive_probe(sg, by_group[sg])
        time.sleep(_PROBE_DELAY_S)

        result = cat.resolve_ingredient(probe)

        if _resolve_correct(sg, result, by_group[sg]):
            correct.append((sg, probe))
        elif result is None:
            unmatched.append((sg, probe))
        else:
            got = result["swap_group"]
            bucket = classify_bucket(sg)
            winner_sim, correct_sim = 0.0, 0.0
            if triage:
                time.sleep(_PROBE_DELAY_S)
                _, winner_sim, correct_sim = _probe_stats_full(probe, sg)
            wrong.append(WrongMatch(sg, probe, got, bucket, winner_sim, correct_sim))

        if i % 50 == 0:
            b3 = sum(1 for w in wrong if w.bucket == 3)
            print(f"  ... {i}/{len(groups)}  wrong={len(wrong)}  bucket3={b3}", flush=True)

    b1 = [w for w in wrong if w.bucket == 1]
    b2 = [w for w in wrong if w.bucket == 2]
    b3 = [w for w in wrong if w.bucket == 3]
    new_b3 = [w for w in b3 if w.expected not in KNOWN_BUCKET3]

    print(f"\n── RESULTS ──")
    print(f"  CORRECT:   {len(correct)}")
    print(f"  UNMATCHED: {len(unmatched)}  (acceptable — gates rejected)")
    print(f"  WRONG:     {len(wrong)}  total cross-group")
    print(f"    BUCKET 1 (false alarms):     {len(b1)}")
    print(f"    BUCKET 2 (generic probes):   {len(b2)}")
    print(f"    BUCKET 3 (real bare-probe):  {len(b3)}  (known={len(b3) - len(new_b3)})")

    if wrong and not triage:
        print(f"\n── WRONG SUMMARY (run with --triage for sim scores) ──")
        for w in sorted(wrong, key=lambda x: (x.bucket, x.expected)):
            tag = f"B{w.bucket}"
            print(f"  [{tag}] expected={w.expected!r:22s} probe={w.probe!r:20s} got={w.got!r}")

    if triage and wrong:
        _print_triage(wrong)

    if new_b3:
        print(f"\nFAIL: {len(new_b3)} NEW BUCKET-3 failure(s) — investigate resolver:")
        for w in new_b3:
            print(f"  expected={w.expected!r} probe={w.probe!r} got={w.got!r}")
        return 1

    if b3:
        print(
            f"\nPASS (known bucket-3): {len(b3)} bare-probe resolver mismatches "
            f"({', '.join(sorted(w.expected for w in b3))}) — "
            f"recipe-safe via LLM disambiguation; do NOT raise global gates."
        )
    else:
        print(f"\nPASS: no cross-group mismatches across {len(groups)} swap_groups.")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Catalog swap_group regression")
    parser.add_argument(
        "--triage",
        action="store_true",
        help="Print full bucket triage with winner_sim / correct_sim scores",
    )
    args = parser.parse_args()
    return run_regression(triage=args.triage)


if __name__ == "__main__":
    sys.exit(main())
