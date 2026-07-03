"""Suggested shopping moments — ranked per customer using Task 1 signals.

Intents use keywords the cart brain already classifies:
  movie night | party | fever/sick | baby | groceries/restock | late night/midnight
"""

from __future__ import annotations

# ── Missions pool (hero chips + mission cards) ───────────────────────────────

MISSIONS = [
    # ── Student-only (segment-exclusive) ──────────────────────────────────────
    {
        "id": "study-session",
        "label": "Study Session",
        "intent": "Late night study session snacks and instant food",
        "emoji": "📚",
        "description": "Focus fuel till 2 AM",
        "match_tags": ["night_owl", "snacker"],
        "segments": ["student"],
        "primary_segment": "student",
    },
    {
        "id": "exam-crunch",
        "label": "Exam Week",
        "intent": "Late night exam week energy snacks and drinks",
        "emoji": "✏️",
        "description": "All-nighter survival kit",
        "match_tags": ["night_owl", "snacker"],
        "segments": ["student"],
        "primary_segment": "student",
    },
    {
        "id": "hostel-midnight",
        "label": "Hostel Midnight",
        "intent": "Midnight hostel room munchies and instant noodles",
        "emoji": "🏨",
        "description": "Roommates will be jealous",
        "match_tags": ["night_owl", "snacker"],
        "segments": ["student"],
        "primary_segment": "student",
    },
    {
        "id": "budget-binge",
        "label": "Budget Binge",
        "intent": "Cheap instant noodles and snacks for student",
        "emoji": "💸",
        "description": "Full stomach, empty wallet",
        "match_tags": ["snacker"],
        "segments": ["student"],
        "primary_segment": "student",
    },
    # ── Working-only ──────────────────────────────────────────────────────────
    {
        "id": "coffee-morning",
        "label": "Coffee Morning",
        "intent": "Morning coffee and breakfast before office",
        "emoji": "☕",
        "description": "Beat the commute rush",
        "match_tags": ["coffee_lover", "breakfast_routine", "premium_buyer"],
        "segments": ["working"],
        "primary_segment": "working",
    },
    {
        "id": "wfh-lunch",
        "label": "WFH Lunch",
        "intent": "Quick lunch groceries for work from home",
        "emoji": "💻",
        "description": "No time to cook between calls",
        "match_tags": ["premium_buyer"],
        "segments": ["working"],
        "primary_segment": "working",
    },
    {
        "id": "office-party",
        "label": "Office Party",
        "intent": "Office team party snacks for 8 people",
        "emoji": "🎉",
        "description": "Impress the team",
        "match_tags": ["party_host", "premium_buyer", "entertainer"],
        "segments": ["working"],
        "primary_segment": "working",
    },
    {
        "id": "after-office",
        "label": "After Office",
        "intent": "Late night unwind snacks after office",
        "emoji": "🌆",
        "description": "You earned this",
        "match_tags": ["night_owl", "coffee_lover", "snacker"],
        "segments": ["working"],
        "primary_segment": "working",
    },
    # ── Family-only ───────────────────────────────────────────────────────────
    {
        "id": "kids-tiffin",
        "label": "Kids Tiffin",
        "intent": "School tiffin box snacks for kids",
        "emoji": "🎒",
        "description": "Monday to Friday sorted",
        "match_tags": ["family_planner", "health_conscious"],
        "segments": ["family"],
        "primary_segment": "family",
    },
    {
        "id": "sunday-brunch",
        "label": "Sunday Brunch",
        "intent": "Sunday family breakfast groceries for 5",
        "emoji": "🥞",
        "description": "Lazy morning feast",
        "match_tags": ["family_planner", "household_planner"],
        "segments": ["family"],
        "primary_segment": "family",
    },
    {
        "id": "baby-care",
        "label": "Baby Care",
        "intent": "Baby care essentials restock",
        "emoji": "👶",
        "description": "Diapers, wipes & more",
        "match_tags": ["family_planner", "health_conscious"],
        "segments": ["family"],
        "primary_segment": "family",
    },
    {
        "id": "family-groceries",
        "label": "Family Stock-up",
        "intent": "Weekly groceries restock for family of 4",
        "emoji": "🛒",
        "description": "Pantry refill time",
        "match_tags": ["weekly_planner", "household_planner", "family_planner"],
        "segments": ["family"],
        "primary_segment": "family",
    },
    {
        "id": "guests-at-home",
        "label": "Guests at Home",
        "intent": "Guests arriving in 1 hour, party snacks and drinks",
        "emoji": "🏠",
        "description": "Impress your visitors",
        "match_tags": ["party_host", "entertainer", "family_planner", "premium_buyer"],
        "segments": ["family", "working"],
    },
    # ── Senior-only ───────────────────────────────────────────────────────────
    {
        "id": "fever-care",
        "label": "Fever Care",
        "intent": "I have fever and feel weak, what should I get",
        "emoji": "🤒",
        "description": "Feel better fast",
        "urgent": True,
        "match_tags": ["health_conscious", "family_planner"],
        "segments": ["family", "senior"],
        "primary_segment": "senior",
    },
    {
        "id": "health-restock",
        "label": "Healthy Restock",
        "intent": "Healthy groceries restock for seniors",
        "emoji": "🥗",
        "description": "Low sugar, high fibre",
        "match_tags": ["health_conscious"],
        "segments": ["senior"],
        "primary_segment": "senior",
    },
    {
        "id": "easy-meals",
        "label": "Easy Meals",
        "intent": "Easy ready to eat meals and soft food",
        "emoji": "🍲",
        "description": "No heavy cooking",
        "match_tags": ["health_conscious"],
        "segments": ["senior"],
        "primary_segment": "senior",
    },
    # ── Tag-specific (narrow audience) ────────────────────────────────────────
    {
        "id": "veg-dinner",
        "label": "Veg Dinner",
        "intent": "Pure vegetarian dinner groceries for tonight",
        "emoji": "🥬",
        "description": "100% shuddh veg",
        "match_tags": ["vegetarian", "health_conscious"],
        "segments": ["working", "family"],
    },
    {
        "id": "premium-movie",
        "label": "Premium Movie",
        "intent": "Premium movie night snacks for 2",
        "emoji": "🍿",
        "description": "Date night sorted",
        "match_tags": ["premium_buyer", "party_host"],
        "segments": ["working"],
    },
    {
        "id": "house-party",
        "label": "House Party",
        "intent": "Hosting house party for 10 people",
        "emoji": "🪩",
        "description": "Big crowd, big spread",
        "match_tags": ["party_host", "entertainer", "premium_buyer"],
        "segments": ["family", "working"],
    },
    # ── Generic fallbacks (penalized — at most one per user) ──────────────────
    {
        "id": "movie-night",
        "label": "Movie Night",
        "intent": "Movie night for 4 people",
        "emoji": "🎬",
        "description": "Snacks, drinks & something sweet",
        "match_tags": ["premium_buyer", "party_host", "snacker"],
        "segments": ["working", "student", "family", "senior"],
    },
    {
        "id": "rainy-day",
        "label": "Rainy Day",
        "intent": "Rainy day comfort food and hot drinks",
        "emoji": "🌧️",
        "description": "Cozy comfort essentials",
        "match_tags": ["household_planner", "weekly_planner"],
        "segments": ["family", "working", "student"],
        "city_boost": ["Mumbai", "Bangalore"],
    },
    {
        "id": "summer-essentials",
        "label": "Summer Cool",
        "intent": "Summer essentials to beat the heat",
        "emoji": "☀️",
        "description": "Cool drinks & frozen treats",
        "match_tags": ["premium_buyer"],
        "segments": ["working", "family", "student", "senior"],
        "city_boost": ["Delhi", "Hyderabad", "Chennai"],
    },
]

TRENDING_MOMENTS = [
    {
        "id": "study-session",
        "label": "Study Session",
        "emoji": "📚",
        "intent": "Late night study session snacks",
        "count": "756",
        "bg_color": "bg-blue-50",
        "border_color": "border-blue-200",
        "match_tags": ["night_owl", "snacker"],
        "segments": ["student"],
        "primary_segment": "student",
    },
    {
        "id": "coffee-morning",
        "label": "Coffee Morning",
        "emoji": "☕",
        "intent": "Morning coffee and breakfast essentials",
        "count": "1.8k",
        "bg_color": "bg-amber-50",
        "border_color": "border-amber-200",
        "match_tags": ["coffee_lover", "breakfast_routine"],
        "segments": ["working"],
        "primary_segment": "working",
    },
    {
        "id": "family-groceries",
        "label": "Weekly Groceries",
        "emoji": "🛒",
        "intent": "Weekly grocery run for family",
        "count": "3.1k",
        "bg_color": "bg-emerald-50",
        "border_color": "border-emerald-200",
        "match_tags": ["weekly_planner", "household_planner", "family_planner"],
        "segments": ["family"],
        "primary_segment": "family",
    },
    {
        "id": "fever-care",
        "label": "Fever Care",
        "emoji": "🤒",
        "intent": "I have fever and feel weak",
        "count": "890",
        "bg_color": "bg-red-50",
        "border_color": "border-red-200",
        "match_tags": ["health_conscious", "family_planner"],
        "segments": ["family", "senior"],
        "primary_segment": "senior",
    },
    {
        "id": "hostel-midnight",
        "label": "Hostel Munchies",
        "emoji": "🏨",
        "intent": "Midnight hostel room snacks",
        "count": "612",
        "bg_color": "bg-indigo-50",
        "border_color": "border-indigo-200",
        "match_tags": ["night_owl", "snacker"],
        "segments": ["student"],
        "primary_segment": "student",
    },
    {
        "id": "office-party",
        "label": "Office Party",
        "emoji": "🎉",
        "intent": "Office team party for 8 people",
        "count": "1.2k",
        "bg_color": "bg-pink-50",
        "border_color": "border-pink-200",
        "match_tags": ["party_host", "premium_buyer"],
        "segments": ["working"],
        "primary_segment": "working",
    },
    {
        "id": "baby-care",
        "label": "Baby Needs",
        "emoji": "👶",
        "intent": "Baby essentials restock",
        "count": "670",
        "bg_color": "bg-pink-50",
        "border_color": "border-pink-200",
        "match_tags": ["family_planner", "health_conscious"],
        "segments": ["family"],
        "primary_segment": "family",
    },
    {
        "id": "health-restock",
        "label": "Healthy Picks",
        "emoji": "🥗",
        "intent": "Healthy groceries restock",
        "count": "540",
        "bg_color": "bg-green-50",
        "border_color": "border-green-200",
        "match_tags": ["health_conscious"],
        "segments": ["senior"],
        "primary_segment": "senior",
    },
    {
        "id": "movie-night",
        "label": "Movie Night",
        "emoji": "🎬",
        "intent": "Movie night for 4 people",
        "count": "2.4k",
        "bg_color": "bg-purple-50",
        "border_color": "border-purple-200",
        "match_tags": ["premium_buyer", "party_host", "snacker"],
        "segments": ["working", "student", "family", "senior"],
    },
    {
        "id": "rainy-day",
        "label": "Rainy Day",
        "emoji": "🌧️",
        "intent": "Rainy day comfort food",
        "count": "1.5k",
        "bg_color": "bg-cyan-50",
        "border_color": "border-cyan-200",
        "match_tags": ["household_planner", "weekly_planner"],
        "segments": ["family", "working"],
        "city_boost": ["Mumbai", "Bangalore"],
    },
]

_BY_ID: dict[str, dict] = {}
for pool in (MISSIONS, TRENDING_MOMENTS):
    for moment in pool:
        _BY_ID[moment["id"]] = moment


def get_by_id(moment_id: str) -> dict | None:
    return _BY_ID.get(moment_id)


def _is_generic(moment: dict) -> bool:
    return len(moment.get("segments", [])) >= 4


def _score_moment(moment: dict, signals: dict) -> int:
    score = 0
    tag_set = set(signals.get("tags") or [])
    segment = signals.get("segment", "working")
    city = signals.get("city", "")

    for tag in moment.get("match_tags", []):
        if tag in tag_set:
            score += 4

    segs = moment.get("segments", [])
    if segment in segs:
        score += 2
        if len(segs) == 1:
            score += 6
    elif segs:
        score -= 5

    if moment.get("primary_segment") == segment:
        score += 4
    elif moment.get("primary_segment"):
        score -= 3

    if city and city in moment.get("city_boost", []):
        score += 2

    if _is_generic(moment):
        score -= 4

    return score


def _public_moment(moment: dict) -> dict:
    return {
        k: v
        for k, v in moment.items()
        if k not in ("match_tags", "segments", "city_boost", "primary_segment")
    }


def rank_for_customer(pool: str, signals: dict, limit: int = 6) -> list[dict]:
    source = MISSIONS if pool == "missions" else TRENDING_MOMENTS
    scored = sorted(
        ((m, _score_moment(m, signals)) for m in source),
        key=lambda pair: pair[1],
        reverse=True,
    )

    selected: list[dict] = []
    generic_count = 0

    for moment, score in scored:
        if score <= 0 and selected:
            break
        if _is_generic(moment) and generic_count >= 1:
            continue
        selected.append(moment)
        if _is_generic(moment):
            generic_count += 1
        if len(selected) >= limit:
            break

    if len(selected) < limit:
        for moment, score in scored:
            if moment not in selected and score > 0:
                selected.append(moment)
            if len(selected) >= limit:
                break

    return [_public_moment(m) for m in selected]
