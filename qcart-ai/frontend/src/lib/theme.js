// Context-aware theme engine — 7 themes with smooth CSS transitions
export const THEMES = {
  morning: {
    name: "morning",
    gradientFrom: "#FFF7ED",
    gradientTo: "#FEF3C7",
    accent: "#FF9900",
    accentSoft: "#FFF4E0",
    surface: "rgba(255,255,255,0.95)",
    glow: "rgba(255,153,0,0.15)",
    label: "Good Morning ☀️",
    emoji: "☀️",
    isNight: false,
  },
  afternoon: {
    name: "afternoon",
    gradientFrom: "#DFF4FF",
    gradientTo: "#E0F2FE",
    accent: "#FF9900",
    accentSoft: "#FFF4E0",
    surface: "rgba(255,255,255,0.95)",
    glow: "rgba(255,153,0,0.15)",
    label: "Afternoon vibes 🌤️",
    emoji: "🌤️",
    isNight: false,
  },
  evening: {
    name: "evening",
    gradientFrom: "#FFF1F2",
    gradientTo: "#FFE4E6",
    accent: "#FF9900",
    accentSoft: "#FFF4E0",
    surface: "rgba(255,255,255,0.95)",
    glow: "rgba(255,153,0,0.12)",
    label: "Good Evening 🌅",
    emoji: "🌅",
    isNight: false,
  },
  night: {
    name: "night",
    gradientFrom: "#232F3E",
    gradientTo: "#131921",
    accent: "#FFD814",
    accentSoft: "#3B4755",
    surface: "rgba(255,255,255,0.95)",
    glow: "rgba(255,216,20,0.15)",
    label: "Night Mode 🌙",
    emoji: "🌙",
    isNight: false,
  },
  summer: {
    name: "summer",
    gradientFrom: "#FFF7ED",
    gradientTo: "#FFEDD5",
    accent: "#FF9900",
    accentSoft: "#FFF4E0",
    surface: "rgba(255,255,255,0.95)",
    glow: "rgba(255,153,0,0.15)",
    label: "Summer Vibes ☀️",
    emoji: "🏖️",
    isNight: false,
  },
  winter: {
    name: "winter",
    gradientFrom: "#F0F9FF",
    gradientTo: "#ECFEFF",
    accent: "#00A8E1",
    accentSoft: "#E0F7FF",
    surface: "rgba(255,255,255,0.95)",
    glow: "rgba(0,168,225,0.12)",
    label: "Winter Chill ❄️",
    emoji: "❄️",
    isNight: false,
  },
  rainy: {
    name: "rainy",
    gradientFrom: "#F1F5F9",
    gradientTo: "#E2E8F0",
    accent: "#00A650",
    accentSoft: "#E6F9ED",
    surface: "rgba(255,255,255,0.90)",
    glow: "rgba(0,166,80,0.12)",
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
  root.style.setProperty("--theme-text", "#111111");
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
