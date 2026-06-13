// Context-aware theme engine — 7 themes with smooth CSS transitions
export const THEMES = {
  morning: {
    name: "morning",
    gradientFrom: "#FFF7ED",
    gradientTo: "#FEF3C7",
    accent: "#F59E0B",
    accentSoft: "#FEF3C7",
    surface: "rgba(255,255,255,0.85)",
    glow: "rgba(245,158,11,0.15)",
    label: "Good Morning ☀️",
    emoji: "☀️",
    isNight: false,
  },
  afternoon: {
    name: "afternoon",
    gradientFrom: "#F0F9FF",
    gradientTo: "#E0F2FE",
    accent: "#0EA5E9",
    accentSoft: "#E0F2FE",
    surface: "rgba(255,255,255,0.85)",
    glow: "rgba(14,165,233,0.15)",
    label: "Afternoon vibes 🌤️",
    emoji: "🌤️",
    isNight: false,
  },
  evening: {
    name: "evening",
    gradientFrom: "#FFF1F2",
    gradientTo: "#FFE4E6",
    accent: "#FB7185",
    accentSoft: "#FFE4E6",
    surface: "rgba(255,255,255,0.85)",
    glow: "rgba(251,113,133,0.15)",
    label: "Good Evening 🌅",
    emoji: "🌅",
    isNight: false,
  },
  night: {
    name: "night",
    gradientFrom: "#1E1B2E",
    gradientTo: "#0F172A",
    accent: "#818CF8",
    accentSoft: "#312E81",
    surface: "rgba(30,27,46,0.9)",
    glow: "rgba(129,140,248,0.2)",
    label: "Night Mode 🌙",
    emoji: "🌙",
    isNight: true,
  },
  summer: {
    name: "summer",
    gradientFrom: "#FFF7ED",
    gradientTo: "#FFEDD5",
    accent: "#F97316",
    accentSoft: "#FFEDD5",
    surface: "rgba(255,255,255,0.85)",
    glow: "rgba(249,115,22,0.15)",
    label: "Summer Vibes ☀️",
    emoji: "🏖️",
    isNight: false,
  },
  winter: {
    name: "winter",
    gradientFrom: "#F0F9FF",
    gradientTo: "#ECFEFF",
    accent: "#22D3EE",
    accentSoft: "#CFFAFE",
    surface: "rgba(255,255,255,0.9)",
    glow: "rgba(34,211,238,0.15)",
    label: "Winter Chill ❄️",
    emoji: "❄️",
    isNight: false,
  },
  rainy: {
    name: "rainy",
    gradientFrom: "#F1F5F9",
    gradientTo: "#E2E8F0",
    accent: "#14B8A6",
    accentSoft: "#CCFBF1",
    surface: "rgba(255,255,255,0.6)",
    glow: "rgba(20,184,166,0.15)",
    label: "Rainy Day 🌧️",
    emoji: "🌧️",
    isNight: false,
  },
};

const DEFAULT_THEME = "afternoon";

export function detectTimeTheme() {
  const hour = new Date().getHours();
  if (hour >= 5 && hour < 11) return "morning";
  if (hour >= 11 && hour < 16) return "afternoon";
  if (hour >= 16 && hour < 20) return "evening";
  return "night";
}

const KEYWORD_MAP = {
  rainy: "rainy", rain: "rainy", monsoon: "rainy",
  summer: "summer", hot: "summer", heat: "summer",
  winter: "winter", cold: "winter", chill: "winter",
  morning: "morning", breakfast: "morning",
  evening: "evening", sunset: "evening",
  night: "night", late: "night", midnight: "night",
};

export function detectContextTheme(text) {
  if (!text) return null;
  const lower = text.toLowerCase();
  for (const [keyword, theme] of Object.entries(KEYWORD_MAP)) {
    if (lower.includes(keyword)) return theme;
  }
  return null;
}

export function applyTheme(themeName) {
  const theme = THEMES[themeName] || THEMES[DEFAULT_THEME];
  const root = document.documentElement;
  root.style.setProperty("--theme-gradient-from", theme.gradientFrom);
  root.style.setProperty("--theme-gradient-to", theme.gradientTo);
  root.style.setProperty("--theme-accent", theme.accent);
  root.style.setProperty("--theme-accent-soft", theme.accentSoft);
  root.style.setProperty("--theme-surface", theme.surface);
  root.style.setProperty("--theme-glow", theme.glow);
  root.style.setProperty("--theme-text", theme.isNight ? "#F1F5F9" : "#16161A");
}

// Urgency-based button/chip styling (preserved from original)
export function themeFor(urgency) {
  if (urgency === "high") {
    return {
      urgent: true,
      btn: "bg-rose-600 hover:bg-rose-700",
      ring: "focus-visible:ring-rose-600",
      chip: "bg-rose-50 text-rose-700",
      dot: "bg-rose-600",
      label: "Care mode · essentials first",
    };
  }
  return {
    urgent: false,
    btn: "bg-smart hover:bg-smart-dark",
    ring: "focus-visible:ring-smart",
    chip: "bg-smart-soft text-smart-dark",
    dot: "bg-smart",
    label: "Moment-aware",
  };
}
