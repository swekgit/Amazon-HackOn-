export const MISSIONS = [
  {
    label: "Movie Night",
    intent: "Movie night for 4 people",
    emoji: "🎬",
    gradient: "from-violet-500 to-purple-700",
    description: "Snacks, drinks & something sweet",
    matchTags: ["premium_buyer", "party_host", "entertainer", "snacker"],
    segments: ["working", "student", "family"],
  },
  {
    label: "Rainy Day",
    intent: "Rainy day comfort food and hot drinks",
    emoji: "🌧️",
    gradient: "from-slate-400 to-cyan-600",
    description: "Cozy comfort essentials",
    matchTags: ["household_planner", "weekly_planner"],
    segments: ["family", "working"],
    cityBoost: ["Mumbai", "Bangalore"],
  },
  {
    label: "Guests at Home",
    intent: "Guests arriving in 1 hour, need snacks and drinks",
    emoji: "🏠",
    gradient: "from-amber-400 to-orange-600",
    description: "Impress your visitors",
    matchTags: ["party_host", "entertainer", "household_planner", "family_planner", "premium_buyer"],
    segments: ["family", "working"],
  },
  {
    label: "Study Session",
    intent: "Late night study session fuel",
    emoji: "📚",
    gradient: "from-blue-500 to-indigo-600",
    description: "Focus fuel & brain food",
    matchTags: ["night_owl", "snacker"],
    segments: ["student"],
  },
  {
    label: "Fever Care",
    intent: "I have fever and feel weak, what should I get",
    emoji: "🤒",
    gradient: "from-red-400 to-rose-600",
    description: "Feel better fast",
    urgent: true,
    matchTags: ["health_conscious", "family_planner"],
    segments: ["family", "senior"],
  },
  {
    label: "Summer Essentials",
    intent: "Summer essentials to beat the heat",
    emoji: "☀️",
    gradient: "from-yellow-400 to-orange-500",
    description: "Cool drinks & frozen treats",
    matchTags: ["premium_buyer"],
    segments: ["working", "family", "student", "senior"],
    cityBoost: ["Delhi", "Hyderabad", "Chennai"],
  },
  {
    label: "Late Night Cravings",
    intent: "Late night snack cravings",
    emoji: "🌙",
    gradient: "from-indigo-600 to-slate-800",
    description: "Midnight munchies sorted",
    matchTags: ["night_owl", "snacker", "coffee_lover"],
    segments: ["student", "working"],
  },
];

export const TRENDING_MOMENTS = [
  {
    label: "Movie Night",
    emoji: "🎬",
    intent: "Movie night for 4 people",
    count: "2.4k",
    bgColor: "bg-purple-50",
    borderColor: "border-purple-200",
    matchTags: ["premium_buyer", "party_host", "entertainer", "snacker"],
    segments: ["working", "student", "family"],
  },
  {
    label: "Morning Essentials",
    emoji: "☀️",
    intent: "Morning breakfast for family",
    count: "1.8k",
    bgColor: "bg-amber-50",
    borderColor: "border-amber-200",
    matchTags: ["breakfast_routine", "coffee_lover", "household_planner"],
    segments: ["working", "family"],
  },
  {
    label: "Party Time",
    emoji: "🎉",
    intent: "Party for 6 people",
    count: "1.2k",
    bgColor: "bg-pink-50",
    borderColor: "border-pink-200",
    matchTags: ["party_host", "entertainer", "premium_buyer"],
    segments: ["family", "working"],
  },
  {
    label: "Fever Care",
    emoji: "🤒",
    intent: "I have fever and feel weak",
    count: "890",
    bgColor: "bg-red-50",
    borderColor: "border-red-200",
    matchTags: ["health_conscious", "family_planner"],
    segments: ["family", "senior"],
  },
  {
    label: "Study Session",
    emoji: "📚",
    intent: "Study session fuel",
    count: "756",
    bgColor: "bg-blue-50",
    borderColor: "border-blue-200",
    matchTags: ["night_owl", "snacker"],
    segments: ["student"],
  },
  {
    label: "Rainy Day Comfort",
    emoji: "🌧️",
    intent: "Rainy day comfort food",
    count: "1.5k",
    bgColor: "bg-cyan-50",
    borderColor: "border-cyan-200",
    matchTags: ["household_planner", "weekly_planner"],
    segments: ["family", "working"],
    cityBoost: ["Mumbai", "Bangalore"],
  },
  {
    label: "Weekly Groceries",
    emoji: "🛒",
    intent: "Weekly grocery run for family",
    count: "3.1k",
    bgColor: "bg-emerald-50",
    borderColor: "border-emerald-200",
    matchTags: ["weekly_planner", "household_planner", "family_planner"],
    segments: ["family", "working"],
  },
  {
    label: "Baby Needs",
    emoji: "👶",
    intent: "Baby essentials",
    count: "670",
    bgColor: "bg-pink-50",
    borderColor: "border-pink-200",
    matchTags: ["family_planner", "health_conscious"],
    segments: ["family"],
  },
];

function scoreMoment(moment, { segment = "working", tags = [], city = "" }) {
  let score = 0;
  const tagSet = new Set(tags);

  for (const tag of moment.matchTags || []) {
    if (tagSet.has(tag)) score += 3;
  }
  if ((moment.segments || []).includes(segment)) score += 2;
  if (city && (moment.cityBoost || []).includes(city)) score += 2;

  return score;
}

function rankMoments(pool, profile, city, limit) {
  const ranked = pool
    .map((moment) => ({
      ...moment,
      score: scoreMoment(moment, { ...profile, city }),
    }))
    .sort((a, b) => b.score - a.score);

  const matched = ranked.filter((moment) => moment.score > 0);
  const selected = (matched.length >= 4 ? matched : ranked).slice(0, limit);
  return selected.map(({ score, matchTags, segments, cityBoost, ...moment }) => moment);
}

export function getMomentsForCustomer(profile = {}, city = "") {
  return rankMoments(MISSIONS, profile, city, 6);
}

export function getTrendingForCustomer(profile = {}, city = "") {
  return rankMoments(TRENDING_MOMENTS, profile, city, 6);
}
