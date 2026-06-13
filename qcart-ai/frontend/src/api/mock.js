// Mock that mirrors the real /api/cart contract. Lets Dev 2 & Dev 3 build the
// whole UI before the backend is wired. Crude keyword matching is fine here.
const line = (id, name, price, quantity, reason) => ({
  id, name, price, quantity, reason, line_total: price * quantity,
});

function build(message) {
  const m = message.toLowerCase();

  if (m.includes("fever") || m.includes("sick") || m.includes("emergency")) {
    return {
      reply: "Sorry you're unwell — here are the essentials.",
      context: "health", urgency: "high",
      cart: [
        line("p040", "Paracetamol 500mg (Strip of 10)", 30, 1, "for fever"),
        line("p041", "ORS Hydration Powder (Pack of 5)", 95, 1, "stay hydrated"),
        line("p046", "Tomato Soup (Instant, 2 packs)", 80, 1, "easy comfort food"),
      ],
      suggestions: [{ id: "p045", name: "Honey (250g)", price: 199, reason: "soothes throat" }],
    };
  }

  if (m.includes("snack") || m.includes("chips") || m.includes("cold drink")) {
    return {
      reply: "Quick snack run, sorted.",
      context: "late_night", urgency: "normal",
      cart: [
        line("p004", "Potato Chips Classic Salted (Large)", 50, 1, "classic"),
        line("p010", "Cola Soft Drink (750ml)", 45, 1, "to go with it"),
      ],
      suggestions: [{ id: "p001", name: "Butter Popcorn", price: 65, reason: "movie staple" }],
    };
  }

  // default: movie night
  return {
    reply: "Movie night for 4 — snacks, drinks & something sweet.",
    context: "movie_night", urgency: "normal",
    cart: [
      line("p001", "Butter Popcorn (Microwave, 90g)", 65, 2, "movie staple"),
      line("p002", "Nachos Tortilla Chips (150g)", 99, 1, "to share"),
      line("p010", "Cola Soft Drink (750ml)", 45, 4, "one each"),
      line("p005", "Dark Chocolate Bar (100g)", 110, 1, "something sweet"),
    ],
    suggestions: [{ id: "p006", name: "Vanilla Ice Cream Tub", price: 175, reason: "dessert upgrade" }],
  };
}

export async function mockTurn({ message }) {
  await new Promise((r) => setTimeout(r, 600)); // fake latency
  const base = build(message);
  const subtotal = base.cart.reduce((s, i) => s + i.line_total, 0);
  const threshold = 199;
  const gap = Math.max(0, threshold - subtotal);
  return {
    ...base,
    subtotal,
    free_delivery_threshold: threshold,
    gap_amount: gap,
    gap_fillers: gap > 0
      ? [{ id: "p001", name: "Butter Popcorn", price: 65, reason: "rounds you up to free delivery" }]
      : [],
    cached: false,
  };
}
