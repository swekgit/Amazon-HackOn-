import { getProductById } from "./products.js";

export const ORDER_HISTORY = {
  preferences: {
    diet: "vegetarian",
    household_size: 3,
    notes: "Prefers value packs. Coffee drinker. Has a toddler at home.",
  },
  recent_orders: [
    { date: "2026-06-06", items: ["p020", "p021", "p022", "p015", "p030", "p031"] },
    { date: "2026-05-30", items: ["p020", "p021", "p015", "p029", "p033"] },
    { date: "2026-05-23", items: ["p020", "p021", "p015", "p016", "p053"] },
  ],
  frequently_bought: ["p020", "p021", "p015", "p022"],
};

export function getFrequentlyBought() {
  return ORDER_HISTORY.frequently_bought
    .map((id) => getProductById(id))
    .filter(Boolean);
}

export function getRecentOrders() {
  return ORDER_HISTORY.recent_orders.map((order) => ({
    ...order,
    products: order.items.map((id) => getProductById(id)).filter(Boolean),
  }));
}

export function getLastPurchaseDate(productId) {
  for (const order of ORDER_HISTORY.recent_orders) {
    if (order.items.includes(productId)) return order.date;
  }
  return null;
}

export function getPurchaseFrequency(productId) {
  return ORDER_HISTORY.recent_orders.filter((o) =>
    o.items.includes(productId)
  ).length;
}
