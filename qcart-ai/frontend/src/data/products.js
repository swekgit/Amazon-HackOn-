// Product catalog — mirrors backend/data/products.json
export const PRODUCTS = [
  { id: "p001", name: "Butter Popcorn (Microwave, 90g)", category: "snacks", price: 65, tags: ["movie", "snack", "party", "instant"] },
  { id: "p002", name: "Nachos Tortilla Chips (150g)", category: "snacks", price: 99, tags: ["movie", "snack", "party", "chips"] },
  { id: "p003", name: "Cheese & Salsa Dip (200g)", category: "snacks", price: 129, tags: ["movie", "dip", "party", "nachos"] },
  { id: "p004", name: "Potato Chips Classic Salted (Large)", category: "snacks", price: 50, tags: ["movie", "snack", "party", "chips"] },
  { id: "p005", name: "Dark Chocolate Bar (100g)", category: "snacks", price: 110, tags: ["movie", "dessert", "chocolate", "sweet"] },
  { id: "p006", name: "Vanilla Ice Cream Tub (500ml)", category: "snacks", price: 175, tags: ["movie", "dessert", "party", "sweet", "frozen"] },
  { id: "p007", name: "Salted Peanuts (200g)", category: "snacks", price: 60, tags: ["snack", "party", "namkeen"] },
  { id: "p008", name: "Mixed Namkeen (400g)", category: "snacks", price: 95, tags: ["snack", "party", "namkeen", "tea"] },
  { id: "p009", name: "Premium Belgian Chocolate Box (250g)", category: "snacks", price: 499, tags: ["movie", "dessert", "premium", "sweet", "gift"] },
  { id: "p010", name: "Cola Soft Drink (750ml)", category: "beverages", price: 45, tags: ["movie", "party", "drink", "cold"] },
  { id: "p011", name: "Cola Soft Drink (2.25L)", category: "beverages", price: 99, tags: ["party", "drink", "cold", "bulk"] },
  { id: "p012", name: "Lemon Soda (750ml)", category: "beverages", price: 45, tags: ["party", "drink", "cold"] },
  { id: "p013", name: "Fresh Orange Juice (1L)", category: "beverages", price: 120, tags: ["drink", "breakfast", "juice", "premium"] },
  { id: "p014", name: "Mineral Water (1L, Pack of 6)", category: "beverages", price: 120, tags: ["party", "water", "bulk"] },
  { id: "p015", name: "Instant Coffee Jar (100g)", category: "beverages", price: 290, tags: ["coffee", "staple", "restock", "breakfast"] },
  { id: "p016", name: "Assam Tea (250g)", category: "beverages", price: 150, tags: ["tea", "staple", "restock", "breakfast"] },
  { id: "p017", name: "Energy Drink (250ml)", category: "beverages", price: 110, tags: ["drink", "party"] },
  { id: "p020", name: "Full Cream Milk (1L)", category: "staples", price: 72, tags: ["weekly", "staple", "dairy", "restock", "breakfast"] },
  { id: "p021", name: "Brown Bread (400g)", category: "staples", price: 50, tags: ["weekly", "staple", "breakfast", "restock"] },
  { id: "p022", name: "Eggs (Pack of 12)", category: "staples", price: 90, tags: ["weekly", "staple", "breakfast", "protein"] },
  { id: "p023", name: "Basmati Rice (5kg)", category: "staples", price: 520, tags: ["weekly", "staple", "monthly"] },
  { id: "p024", name: "Whole Wheat Atta (5kg)", category: "staples", price: 280, tags: ["weekly", "staple", "monthly"] },
  { id: "p025", name: "Sunflower Oil (1L)", category: "staples", price: 160, tags: ["weekly", "staple", "monthly"] },
  { id: "p026", name: "Sugar (1kg)", category: "staples", price: 50, tags: ["weekly", "staple", "restock"] },
  { id: "p027", name: "Toor Dal (1kg)", category: "staples", price: 145, tags: ["weekly", "staple", "monthly"] },
  { id: "p028", name: "Paneer (200g)", category: "staples", price: 95, tags: ["weekly", "party", "dairy", "protein"] },
  { id: "p029", name: "Butter (100g)", category: "staples", price: 60, tags: ["weekly", "dairy", "breakfast", "restock"] },
  { id: "p030", name: "Onion (1kg)", category: "produce", price: 40, tags: ["weekly", "vegetable", "staple"] },
  { id: "p031", name: "Tomato (1kg)", category: "produce", price: 45, tags: ["weekly", "vegetable", "staple"] },
  { id: "p032", name: "Potato (1kg)", category: "produce", price: 35, tags: ["weekly", "vegetable", "staple"] },
  { id: "p033", name: "Banana (6 pcs)", category: "produce", price: 50, tags: ["weekly", "fruit", "breakfast"] },
  { id: "p034", name: "Apple (1kg)", category: "produce", price: 180, tags: ["weekly", "fruit", "healthy"] },
  { id: "p035", name: "Lemon (4 pcs)", category: "produce", price: 30, tags: ["fever", "vegetable", "immunity"] },
  { id: "p036", name: "Ginger (100g)", category: "produce", price: 25, tags: ["fever", "immunity", "tea"] },
  { id: "p040", name: "Paracetamol 500mg (Strip of 10)", category: "health", price: 30, tags: ["fever", "medicine", "pain", "emergency"] },
  { id: "p041", name: "ORS Hydration Powder (Pack of 5)", category: "health", price: 95, tags: ["fever", "medicine", "hydration", "emergency"] },
  { id: "p042", name: "Digital Thermometer", category: "health", price: 199, tags: ["fever", "medicine", "emergency"] },
  { id: "p043", name: "Cough Syrup (100ml)", category: "health", price: 110, tags: ["fever", "cold", "medicine"] },
  { id: "p044", name: "Tissue Box (100 pulls)", category: "health", price: 60, tags: ["fever", "cold", "essentials"] },
  { id: "p045", name: "Honey (250g)", category: "health", price: 199, tags: ["fever", "immunity", "cold", "breakfast"] },
  { id: "p046", name: "Tomato Soup (Instant, 2 packs)", category: "health", price: 80, tags: ["fever", "comfort", "soup", "instant"] },
  { id: "p047", name: "Vitamin C Tablets (Strip of 10)", category: "health", price: 120, tags: ["fever", "immunity", "medicine"] },
  { id: "p050", name: "Baby Diapers (Medium, Pack of 30)", category: "baby", price: 599, tags: ["baby", "newparent", "essentials"] },
  { id: "p051", name: "Baby Wet Wipes (72 pcs)", category: "baby", price: 199, tags: ["baby", "newparent", "essentials"] },
  { id: "p052", name: "Baby Lotion (200ml)", category: "baby", price: 250, tags: ["baby", "newparent", "skincare"] },
  { id: "p053", name: "Baby Cereal (300g)", category: "baby", price: 220, tags: ["baby", "newparent", "food"] },
  { id: "p054", name: "Baby Shampoo (200ml)", category: "baby", price: 230, tags: ["baby", "newparent", "bath"] },
  { id: "p055", name: "Baby Feeding Bottle (250ml)", category: "baby", price: 320, tags: ["baby", "newparent", "feeding"] },
  { id: "p060", name: "Frozen Cheese Pizza (Large)", category: "party", price: 280, tags: ["party", "movie", "frozen", "meal"] },
  { id: "p061", name: "Paper Plates (Pack of 25)", category: "party", price: 75, tags: ["party", "disposable"] },
  { id: "p062", name: "Disposable Cups (Pack of 50)", category: "party", price: 60, tags: ["party", "disposable"] },
  { id: "p063", name: "Birthday Candles (Pack of 10)", category: "party", price: 40, tags: ["party", "birthday"] },
  { id: "p064", name: "Chocolate Cake (500g)", category: "party", price: 399, tags: ["party", "birthday", "dessert", "sweet"] },
  { id: "p065", name: "Garlic Bread (Frozen, 2 packs)", category: "party", price: 150, tags: ["party", "movie", "frozen", "snack"] },
];

const BY_ID = Object.fromEntries(PRODUCTS.map((p) => [p.id, p]));

export const getProductById = (id) => BY_ID[id] || null;

export const getProductsByCategory = (cat) =>
  PRODUCTS.filter((p) => p.category === cat);

export const getProductsByTags = (tags) => {
  const t = new Set(tags);
  return PRODUCTS.filter((p) => p.tags.some((tag) => t.has(tag)));
};

const CATEGORY_EMOJI = {
  snacks: "🍿",
  beverages: "🥤",
  staples: "🛒",
  produce: "🥬",
  health: "💊",
  baby: "👶",
  party: "🎉",
};

const CATEGORY_GRADIENT = {
  snacks: "from-amber-400 to-orange-500",
  beverages: "from-sky-400 to-blue-500",
  staples: "from-emerald-400 to-green-500",
  produce: "from-lime-400 to-emerald-500",
  health: "from-rose-400 to-red-500",
  baby: "from-pink-300 to-fuchsia-400",
  party: "from-violet-400 to-purple-500",
};

export const getCategoryEmoji = (cat) => CATEGORY_EMOJI[cat] || "📦";
export const getCategoryGradient = (cat) =>
  CATEGORY_GRADIENT[cat] || "from-gray-400 to-gray-500";
