"""
Recommendation Engine
======================
Pure rules-based recommendations using segment, tags, city, and time of day.
No LLM calls. Uses catalog.retrieve() for product selection.
"""

from datetime import datetime, timezone, timedelta

import catalog

# ══════════════════════════════════════════════════════════
#  TIME BUCKETS
# ══════════════════════════════════════════════════════════

def get_time_bucket() -> str:
    """Get current time bucket based on IST (UTC+5:30)."""
    ist = timezone(timedelta(hours=5, minutes=30))
    hour = datetime.now(ist).hour

    if 5 <= hour < 11:
        return "morning"
    elif 11 <= hour < 15:
        return "afternoon"
    elif 15 <= hour < 20:
        return "evening"
    else:
        return "night"


# Tags associated with each time bucket
TIME_BUCKET_TAGS = {
    "morning": ["breakfast", "dairy", "coffee", "tea", "bread"],
    "afternoon": ["lunch", "cooking", "staple", "rice", "dal"],
    "evening": ["snack", "tea", "biscuit", "namkeen", "fruit"],
    "night": ["instant", "noodles", "ready_to_eat", "snack", "ice_cream"],
}

# Tags associated with each segment
SEGMENT_TAGS = {
    "student": ["budget", "instant", "snack", "noodles", "quick"],
    "working": ["coffee", "ready_to_eat", "convenience", "premium", "protein"],
    "family": ["bulk", "staple", "household", "family", "cooking"],
    "senior": ["healthy", "organic", "low_sugar", "diabetic", "fiber"],
}


# Shared behavioral-tag -> product-vocabulary tag mapping.
# Customer tags are behavioral IDs (health_conscious, coffee_lover, ...) that
# never equal catalog tag strings (healthy, coffee, ...). This mapping bridges
# them and is the single source of truth reused by main._score_product().
BEHAVIORAL_TAG_MAP = {
    "party_host": {"party"},
    "entertainer": {"party", "snack"},
    "premium_buyer": {"premium"},
    "coffee_lover": {"coffee"},
    "snacker": {"snack"},
    "fruit_lover": {"fruit"},
    "health_conscious": {"healthy"},
    "vegetarian": {"vegetarian"},
    "breakfast_routine": {"breakfast"},
    "night_owl": {"instant", "snack"},
    "household_planner": {"household", "cleaning", "staple"},
    "weekly_planner": {"staple", "household"},
    "family_planner": {"family", "bulk"},
    "tea_lover": {"tea"},
    "new_parent": {"baby"},
}


def map_behavioral_tags(tags: list[str]) -> set[str]:
    """Translate customer behavioral tag IDs to product-vocabulary tags."""
    mapped: set[str] = set()
    for tag in tags or []:
        mapped |= BEHAVIORAL_TAG_MAP.get(tag, set())
    return mapped


# ══════════════════════════════════════════════════════════
#  RECOMMENDATION GENERATION
# ══════════════════════════════════════════════════════════

def get_recommendations(
    tags: list[str],
    segment: str,
    city: str = "Bangalore",
) -> list[dict]:
    """
    Generate personalized recommendations combining:
    1. Customer tags (from rule engine)
    2. Customer segment (student/working/family/senior)
    3. Time of day

    Returns list of {id, name, price, reason} dicts (max 8).
    """
    time_bucket = get_time_bucket()
    time_tags = TIME_BUCKET_TAGS.get(time_bucket, [])
    segment_tags = SEGMENT_TAGS.get(segment, [])

    # Translate behavioral customer tags -> product-vocabulary tags so both the
    # embed query and the re-rank reflect real catalog tags (e.g. coffee_lover
    # -> "coffee", health_conscious -> "healthy").
    mapped_tags = map_behavioral_tags(tags)

    # Build a combined query from all signals. Time-of-day tags are deliberately
    # NOT added here: they used to flood the query with "instant noodles" and
    # dominate retrieval for everyone. Customer + segment product tags drive it.
    query_parts = []
    query_parts.extend(sorted(mapped_tags))  # Mapped customer product tags
    query_parts.extend(segment_tags[:3])     # Segment-specific tags

    query = " ".join(query_parts) if query_parts else "staple breakfast daily"

    # Use existing catalog.retrieve() for smart scoring
    import json
    candidates_json = catalog.retrieve(query, limit=30)
    candidates = json.loads(candidates_json)

    if not candidates:
        return []

    # Score and pick top 8. Customer tags dominate; time bucket is only a minor
    # tiebreaker so time-of-day never overrides personalization.
    scored = []
    for p in candidates:
        ptags = set(p.get("tags", []))
        score = 0

        # Mapped customer tag overlap (highest weight)
        score += len(ptags.intersection(mapped_tags)) * 5

        # Segment tag overlap
        score += len(ptags.intersection(set(segment_tags))) * 2

        # Time bucket overlap (minor tiebreaker only)
        score += len(ptags.intersection(set(time_tags))) * 1

        scored.append((score, p))

    scored.sort(key=lambda x: -x[0])
    top = scored[:8]

    results = []
    for _, p in top:
        reason = _generate_reason(p, tags, segment, time_bucket)
        results.append({
            "id": p["id"],
            "name": p["name"],
            "price": p["price"],
            "reason": reason,
        })

    return results


def get_trending(city: str = "Bangalore") -> list[dict]:
    """
    Get trending products based on city + time of day.
    Pure rules, no LLM.
    """
    time_bucket = get_time_bucket()
    time_tags = TIME_BUCKET_TAGS.get(time_bucket, [])

    # Build query for time-relevant trending
    query = f"{city} {' '.join(time_tags[:3])}"

    import json
    candidates_json = catalog.retrieve(query, limit=20)
    candidates = json.loads(candidates_json)

    if not candidates:
        return catalog.CATALOG[:6]

    # Pick top 6 by rating (simulate "trending")
    sorted_by_pop = sorted(candidates, key=lambda p: -p.get("price", 0))[:6]

    return [
        {
            "id": p["id"],
            "name": p["name"],
            "price": p["price"],
            "reason": f"Trending in {city} this {time_bucket}",
        }
        for p in sorted_by_pop
    ]


def _generate_reason(product: dict, tags: list, segment: str, time_bucket: str) -> str:
    """Generate a human-readable reason for a recommendation."""
    ptags = set(product.get("tags", []))

    # Segment-specific reasons
    if segment == "student" and "budget" in ptags:
        return "Budget-friendly pick for you"
    if segment == "student" and "instant" in ptags:
        return "Quick meal for busy schedules"
    if segment == "working" and "coffee" in ptags:
        return "Perfect for your coffee routine"
    if segment == "working" and "protein" in ptags:
        return "High-protein for your active day"
    if segment == "family" and "bulk" in ptags:
        return "Great value for the whole family"
    if segment == "family" and "staple" in ptags:
        return "Household essential"
    if segment == "senior" and "healthy" in ptags:
        return "Fits your healthy lifestyle"
    if segment == "senior" and "diabetic" in ptags:
        return "Suitable for your health goals"

    # Time-based reasons
    if time_bucket == "morning" and "breakfast" in ptags:
        return "Perfect for breakfast"
    if time_bucket == "evening" and "snack" in ptags:
        return "Great evening snack"
    if time_bucket == "night" and "instant" in ptags:
        return "Quick late-night option"

    # Tag-based reasons
    if "premium_buyer" in tags and "premium" in ptags:
        return "Matches your premium taste"
    if "health_conscious" in tags and "healthy" in ptags:
        return "Fits your healthy lifestyle"

    return "Picked for you"
