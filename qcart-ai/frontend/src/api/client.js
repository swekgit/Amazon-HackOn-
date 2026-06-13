import { mockTurn } from "./mock.js";

// Flip to false once the backend is ready. Lets frontend work fully standalone.
const USE_MOCK = false;

export async function sendTurn({ message, cart }) {
  if (!USE_MOCK) return mockTurn({ message, cart });

  const res = await fetch("/api/cart", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, cart }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Something went wrong. Try again.");
  }
  return res.json();
}


// ── City & Trending endpoints ─────────────────────────────────────────────────

const MOCK_CITIES = ["Bangalore", "Chennai", "Delhi", "Mumbai"];

const MOCK_TRENDING = {
  Bangalore: [
    { id: "p001", name: "Butter Popcorn (Microwave, 90g)", price: 65, tags: ["movie", "snack", "party", "instant"] },
    { id: "p010", name: "Cola Soft Drink (750ml)", price: 45, tags: ["movie", "party", "drink", "cold"] },
    { id: "p020", name: "Full Cream Milk (1L)", price: 72, tags: ["weekly", "staple", "dairy", "restock", "breakfast"] },
    { id: "p033", name: "Banana (6 pcs)", price: 50, tags: ["weekly", "fruit", "breakfast"] },
    { id: "p002", name: "Nachos Tortilla Chips (150g)", price: 99, tags: ["movie", "snack", "party", "chips"] },
  ],
  Chennai: [
    { id: "p015", name: "Instant Coffee Jar (100g)", price: 290, tags: ["coffee", "staple", "restock", "breakfast"] },
    { id: "p016", name: "Assam Tea (250g)", price: 150, tags: ["tea", "staple", "restock", "breakfast"] },
    { id: "p022", name: "Eggs (Pack of 12)", price: 90, tags: ["weekly", "staple", "breakfast", "protein"] },
    { id: "p028", name: "Paneer (200g)", price: 95, tags: ["weekly", "party", "dairy", "protein"] },
    { id: "p034", name: "Apple (1kg)", price: 180, tags: ["weekly", "fruit", "healthy"] },
  ],
  Delhi: [
    { id: "p023", name: "Basmati Rice (5kg)", price: 520, tags: ["weekly", "staple", "monthly"] },
    { id: "p024", name: "Whole Wheat Atta (5kg)", price: 280, tags: ["weekly", "staple", "monthly"] },
    { id: "p025", name: "Sunflower Oil (1L)", price: 160, tags: ["weekly", "staple", "monthly"] },
    { id: "p027", name: "Toor Dal (1kg)", price: 145, tags: ["weekly", "staple", "monthly"] },
    { id: "p030", name: "Onion (1kg)", price: 40, tags: ["weekly", "vegetable", "staple"] },
  ],
  Mumbai: [
    { id: "p005", name: "Dark Chocolate Bar (100g)", price: 110, tags: ["movie", "dessert", "chocolate", "sweet"] },
    { id: "p006", name: "Vanilla Ice Cream Tub (500ml)", price: 175, tags: ["movie", "dessert", "party", "sweet", "frozen"] },
    { id: "p013", name: "Fresh Orange Juice (1L)", price: 120, tags: ["drink", "breakfast", "juice", "premium"] },
    { id: "p060", name: "Frozen Cheese Pizza (Large)", price: 280, tags: ["party", "movie", "frozen", "meal"] },
    { id: "p064", name: "Chocolate Cake (500g)", price: 399, tags: ["party", "birthday", "dessert", "sweet"] },
  ],
};


export async function fetchCities() {
  if (!USE_MOCK) return { cities: MOCK_CITIES };

  const res = await fetch("/api/cities");
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to load cities.");
  }
  return res.json();
}


export async function fetchTrending(city = "Bangalore") {
  if (!USE_MOCK) {
    const products = MOCK_TRENDING[city] || MOCK_TRENDING["Bangalore"] || [];
    return { city, products };
  }

  const res = await fetch(`/api/trending?city=${encodeURIComponent(city)}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to load trending products.");
  }
  return res.json();
}
