import { PRODUCTS, getProductById, getProductsByTags } from "../data/products.js";

const line = (id, qty, reason) => {
  const p = getProductById(id);
  if (!p) return null;
  return { id: p.id, name: p.name, price: p.price, category: p.category, tags: p.tags, quantity: qty, reason, line_total: p.price * qty };
};

const pick = (ids, reasons) =>
  ids.map((id, i) => line(id, 1, reasons[i] || "")).filter(Boolean);

function buildCart(message) {
  const m = message.toLowerCase();

  if (m.includes("fever") || m.includes("sick") || m.includes("unwell") || m.includes("cold medicine")) {
    return {
      reply: "I'm sorry you're not feeling well. Here are essentials to help you recover fast. 💊",
      context: "health", urgency: "high",
      cart: [
        line("p040", 1, "fever relief"), line("p041", 1, "stay hydrated"),
        line("p046", 2, "comfort food"), line("p044", 1, "you'll need these"),
        line("p045", 1, "soothes throat"), line("p035", 1, "immunity boost"),
      ].filter(Boolean),
      suggestions: [
        { ...getProductById("p047"), reason: "immunity support" },
        { ...getProductById("p043"), reason: "cough relief" },
      ].filter(Boolean),
    };
  }

  if (m.includes("party") || m.includes("guests") || m.includes("hosting")) {
    const people = parseInt(m.match(/(\d+)/)?.[1]) || 6;
    return {
      reply: `Party mode activated! Got everything for ${people} guests — snacks, drinks & more. 🎉`,
      context: "party", urgency: "normal",
      cart: [
        line("p002", 2, "crowd favorite"), line("p003", 1, "perfect with nachos"),
        line("p011", Math.ceil(people / 3), "one per group"), line("p012", Math.ceil(people / 3), "non-cola option"),
        line("p060", Math.ceil(people / 4), "easy hot meal"), line("p065", 1, "garlic bread side"),
        line("p061", 1, "easy cleanup"), line("p062", 1, "for drinks"),
        line("p014", 1, "stay hydrated"),
      ].filter(Boolean),
      suggestions: [
        { ...getProductById("p064"), reason: "celebration dessert" },
        { ...getProductById("p009"), reason: "premium chocolate" },
      ].filter(Boolean),
    };
  }

  if (m.includes("movie") || m.includes("film") || m.includes("watch")) {
    const people = parseInt(m.match(/(\d+)/)?.[1]) || 4;
    return {
      reply: `Movie night for ${people} — popcorn, drinks & treats! 🎬`,
      context: "movie_night", urgency: "normal",
      cart: [
        line("p001", Math.ceil(people / 2), "movie staple"),
        line("p002", 1, "to share"), line("p003", 1, "dip for nachos"),
        line("p010", people, "one each"), line("p005", 1, "something sweet"),
        line("p006", 1, "dessert time"),
      ].filter(Boolean),
      suggestions: [
        { ...getProductById("p060"), reason: "frozen pizza break" },
        { ...getProductById("p009"), reason: "premium upgrade" },
      ].filter(Boolean),
    };
  }

  if (m.includes("baby") || m.includes("toddler") || m.includes("newborn")) {
    return {
      reply: "Baby essentials packed and ready! 👶",
      context: "baby", urgency: "normal",
      cart: [
        line("p050", 1, "daily essential"), line("p051", 1, "always needed"),
        line("p053", 1, "meal time"), line("p052", 1, "gentle care"),
        line("p054", 1, "bath time"),
      ].filter(Boolean),
      suggestions: [
        { ...getProductById("p055"), reason: "feeding essential" },
        { ...getProductById("p020"), reason: "for cereal mixing" },
      ].filter(Boolean),
    };
  }

  if (m.includes("breakfast") || m.includes("morning")) {
    return {
      reply: "Perfect morning spread coming right up! ☀️",
      context: "routine", urgency: "normal",
      cart: [
        line("p020", 1, "fresh milk"), line("p021", 1, "toast ready"),
        line("p022", 1, "protein boost"), line("p029", 1, "butter up"),
        line("p015", 1, "morning caffeine"), line("p033", 1, "healthy start"),
        line("p013", 1, "fresh juice"),
      ].filter(Boolean),
      suggestions: [
        { ...getProductById("p045"), reason: "healthy sweetener" },
        { ...getProductById("p034"), reason: "fruit boost" },
      ].filter(Boolean),
    };
  }

  if (m.includes("study") || m.includes("exam") || m.includes("focus")) {
    return {
      reply: "Brain fuel loaded — stay focused! 📚",
      context: "routine", urgency: "normal",
      cart: [
        line("p015", 1, "stay alert"), line("p017", 1, "energy boost"),
        line("p005", 1, "brain food"), line("p008", 1, "study snack"),
        line("p033", 1, "healthy energy"),
      ].filter(Boolean),
      suggestions: [
        { ...getProductById("p034"), reason: "brain health" },
        { ...getProductById("p007"), reason: "protein snack" },
      ].filter(Boolean),
    };
  }

  if (m.includes("rain") || m.includes("monsoon")) {
    return {
      reply: "Rainy day comfort coming your way! 🌧️",
      context: "late_night", urgency: "normal",
      cart: [
        line("p016", 1, "hot chai time"), line("p046", 1, "warm soup"),
        line("p008", 1, "tea-time snack"), line("p005", 1, "chocolate comfort"),
        line("p015", 1, "hot coffee"),
      ].filter(Boolean),
      suggestions: [
        { ...getProductById("p045"), reason: "honey ginger tea" },
        { ...getProductById("p036"), reason: "add to chai" },
      ].filter(Boolean),
    };
  }

  if (m.includes("summer") || m.includes("hot") || m.includes("heat")) {
    return {
      reply: "Beat the heat with these cooling essentials! ☀️",
      context: "routine", urgency: "normal",
      cart: [
        line("p006", 1, "frozen treat"), line("p010", 2, "cold & fizzy"),
        line("p012", 2, "refreshing"), line("p013", 1, "fresh juice"),
        line("p014", 1, "stay hydrated"),
      ].filter(Boolean),
      suggestions: [
        { ...getProductById("p035"), reason: "nimbu pani" },
        { ...getProductById("p033"), reason: "potassium boost" },
      ].filter(Boolean),
    };
  }

  if (m.includes("grocery") || m.includes("weekly") || m.includes("restock")) {
    return {
      reply: "Weekly grocery run sorted for your family of 3! 🛒",
      context: "routine", urgency: "normal",
      cart: [
        line("p020", 2, "double for the week"), line("p021", 2, "daily bread"),
        line("p022", 1, "breakfast protein"), line("p025", 1, "cooking oil"),
        line("p030", 1, "kitchen staple"), line("p031", 1, "kitchen staple"),
        line("p032", 1, "kitchen staple"), line("p029", 1, "toast & cooking"),
        line("p026", 1, "sweetener"),
      ].filter(Boolean),
      suggestions: [
        { ...getProductById("p027"), reason: "dal for the week" },
        { ...getProductById("p033"), reason: "healthy snacking" },
      ].filter(Boolean),
    };
  }

  if (m.includes("snack") || m.includes("chips") || m.includes("hungry") || m.includes("craving") || m.includes("late night") || m.includes("midnight")) {
    return {
      reply: "Midnight munchies sorted! 🌙",
      context: "late_night", urgency: "normal",
      cart: [
        line("p004", 1, "classic crunch"), line("p001", 1, "quick & easy"),
        line("p010", 1, "to wash it down"), line("p005", 1, "sweet fix"),
        line("p008", 1, "namkeen variety"),
      ].filter(Boolean),
      suggestions: [
        { ...getProductById("p006"), reason: "ice cream upgrade" },
        { ...getProductById("p002"), reason: "more crunch" },
      ].filter(Boolean),
    };
  }

  // Refinement commands
  if (m.includes("premium") || m.includes("upgrade")) {
    return {
      reply: "Upgraded your cart to premium picks! ✨",
      context: "movie_night", urgency: "normal",
      cart: [
        line("p009", 1, "premium chocolate"), line("p002", 2, "quality chips"),
        line("p003", 1, "artisan dip"), line("p013", 2, "fresh juice"),
        line("p006", 1, "premium dessert"),
      ].filter(Boolean),
      suggestions: [
        { ...getProductById("p060"), reason: "gourmet pizza" },
      ].filter(Boolean),
    };
  }

  // Default: movie night
  return {
    reply: "Here's what I picked for you — snacks, drinks & treats! ✨",
    context: "movie_night", urgency: "normal",
    cart: [
      line("p001", 2, "classic pick"), line("p002", 1, "crunchy & shareable"),
      line("p010", 4, "one for everyone"), line("p005", 1, "sweet treat"),
    ].filter(Boolean),
    suggestions: [
      { ...getProductById("p006"), reason: "dessert upgrade" },
      { ...getProductById("p003"), reason: "dip for chips" },
    ].filter(Boolean),
  };
}

export async function mockTurn({ message }) {
  await new Promise((r) => setTimeout(r, 600 + Math.random() * 900));
  const base = buildCart(message);
  const subtotal = base.cart.reduce((s, i) => s + i.line_total, 0);
  const threshold = 199;
  const gap = Math.max(0, threshold - subtotal);
  const inCart = new Set(base.cart.map((i) => i.id));
  const gapFillers = gap > 0
    ? PRODUCTS
        .filter((p) => !inCart.has(p.id) && p.price <= gap + 60)
        .slice(0, 3)
        .map((p) => ({ id: p.id, name: p.name, price: p.price, reason: "rounds up to free delivery" }))
    : [];

  return {
    ...base,
    subtotal,
    free_delivery_threshold: threshold,
    gap_amount: gap,
    gap_fillers: gapFillers,
    cached: false,
    recipe: null,
    payment_offers: [
      { id: "po1", title: "10% off with HDFC Credit Card", code: "HDFC10", savings: Math.round(subtotal * 0.1) },
      { id: "po2", title: "5% cashback with Amazon Pay", code: "AMZPAY5", savings: Math.round(subtotal * 0.05) },
      { id: "po3", title: "Flat ₹30 off on UPI", code: "UPI30", savings: 30 },
    ],
    saved_payments: [
      { id: "sp1", type: "card", label: "HDFC Visa •••• 4242", icon: "💳" },
      { id: "sp2", type: "upi",  label: "ravi@okaxis", icon: "📱" },
      { id: "sp3", type: "wallet", label: "Amazon Pay ₹240 balance", icon: "🪙" },
    ],
  };
}
