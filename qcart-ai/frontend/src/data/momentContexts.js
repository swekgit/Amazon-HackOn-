/**
 * Moment context data for keyword inference + contextual AI panel.
 */

export const MOMENT_CONTEXTS = {
  "Rainy Day": {
    icon: "🌧️",
    keywords: ["rain", "rainy", "monsoon"],
    loadingSteps: [
      { emoji: "🌧️", text: "Rainy Day detected" },
      { emoji: "☕", text: "Adding comfort beverages" },
      { emoji: "🍜", text: "Finding comfort food" },
      { emoji: "⚡", text: "Optimizing delivery" },
    ],
    resultInsights: ["Added comfort food", "Added hot beverages"],
  },
  "Movie Night": {
    icon: "🎬",
    keywords: ["movie", "film", "cinema", "watch", "binge"],
    loadingSteps: [
      { emoji: "🎬", text: "Movie Night detected" },
      { emoji: "🍿", text: "Finding crowd-favorite snacks" },
      { emoji: "🥤", text: "Adding drinks" },
      { emoji: "⚡", text: "Optimizing delivery" },
    ],
    resultInsights: ["Added crowd-favorite snacks", "Added drinks"],
  },
  "Party for 6": {
    icon: "🎉",
    keywords: ["party", "birthday", "gathering", "celebration", "hosting"],
    loadingSteps: [
      { emoji: "🎉", text: "Party detected" },
      { emoji: "🍿", text: "Adding sharing snacks" },
      { emoji: "🥤", text: "Adding beverages" },
      { emoji: "🎂", text: "Suggesting cake" },
      { emoji: "⚡", text: "Optimizing delivery" },
    ],
    resultInsights: ["Added sharing snacks", "Added beverages", "Suggested cake"],
  },
  "Summer Essentials": {
    icon: "☀️",
    keywords: ["summer", "heat", "hot day", "sunny"],
    loadingSteps: [
      { emoji: "☀️", text: "Summer mode activated" },
      { emoji: "🥤", text: "Finding cold drinks" },
      { emoji: "🍦", text: "Adding frozen treats" },
      { emoji: "⚡", text: "Optimizing delivery" },
    ],
    resultInsights: ["Added cooling beverages", "Added frozen treats"],
  },
  "Fever Care": {
    icon: "🤒",
    keywords: ["fever", "sick", "unwell", "cold", "flu", "medicine", "ill"],
    loadingSteps: [
      { emoji: "🤒", text: "Fever Care activated" },
      { emoji: "💊", text: "Finding essential medicines" },
      { emoji: "🍲", text: "Adding recovery food" },
      { emoji: "⚡", text: "Prioritizing fast delivery" },
    ],
    resultInsights: ["Added essential medicines", "Added recovery food"],
  },
  "Late Night Cravings": {
    icon: "🌙",
    keywords: ["night", "midnight", "craving", "late", "hungry"],
    loadingSteps: [
      { emoji: "🌙", text: "Late Night mode" },
      { emoji: "🍿", text: "Finding midnight snacks" },
      { emoji: "🍫", text: "Adding sweet treats" },
      { emoji: "⚡", text: "Optimizing delivery" },
    ],
    resultInsights: ["Added midnight munchies", "Added sweet treats"],
  },
  "Study Session": {
    icon: "📚",
    keywords: ["study", "exam", "homework", "assignment"],
    loadingSteps: [
      { emoji: "📚", text: "Study Session detected" },
      { emoji: "☕", text: "Adding focus fuel" },
      { emoji: "🍫", text: "Finding brain food" },
      { emoji: "⚡", text: "Optimizing delivery" },
    ],
    resultInsights: ["Added focus fuel", "Added brain food"],
  },
  "Guests at Home": {
    icon: "🏠",
    keywords: ["guest", "guests", "visitor", "hosting", "company"],
    loadingSteps: [
      { emoji: "🏠", text: "Guests mode activated" },
      { emoji: "🍵", text: "Adding refreshments" },
      { emoji: "🍪", text: "Finding premium snacks" },
      { emoji: "⚡", text: "Optimizing delivery" },
    ],
    resultInsights: ["Added impressive snacks", "Added refreshments"],
  },
};

/**
 * Given text, detect the best-matching moment. Returns key or null.
 */
export function detectMomentFromText(text) {
  if (!text) return null;
  const lower = text.toLowerCase();
  for (const [key, ctx] of Object.entries(MOMENT_CONTEXTS)) {
    for (const kw of ctx.keywords) {
      if (lower.includes(kw)) return key;
    }
  }
  return null;
}
