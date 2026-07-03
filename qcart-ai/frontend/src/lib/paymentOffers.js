const BASE_TIERS = [
  {
    id: "po_amazonpay",
    title: "Amazon Pay 5% cashback",
    minSubtotal: 200,
    rate: 0.05,
    maxSavings: 50,
  },
  {
    id: "po_icici",
    title: "ICICI Bank 10% off",
    minSubtotal: 299,
    rate: 0.1,
    maxSavings: 75,
  },
];

function buildTiers(context, cart) {
  const tiers = [...BASE_TIERS];
  const categories = new Set(cart.map((item) => item.category));
  const tags = new Set(cart.flatMap((item) => item.tags || []));

  if (
    context === "health" ||
    categories.has("health") ||
    tags.has("medicine") ||
    tags.has("fever")
  ) {
    tiers.push({
      id: "po_health",
      title: "Health Essentials 15% off",
      minSubtotal: 0,
      rate: 0.15,
      maxSavings: 9999,
    });
  } else if (context === "party" || categories.has("party") || tags.has("party")) {
    tiers.push({
      id: "po_party",
      title: "Party Combo Offer",
      minSubtotal: 500,
      flatSavings: 100,
    });
  }

  return tiers;
}

function pickSuggestedItems(gapAmount, cart, fillerPool, limit = 2) {
  const inCart = new Set(cart.map((item) => item.id));
  const seen = new Set();
  const candidates = [];

  for (const item of fillerPool) {
    if (!item?.id || inCart.has(item.id) || seen.has(item.id)) continue;
    seen.add(item.id);
    candidates.push(item);
  }

  const covering = candidates
    .filter((item) => item.price >= gapAmount)
    .sort((a, b) => a.price - b.price);

  const pool = covering.length
    ? covering
    : [...candidates].sort(
        (a, b) => Math.abs(a.price - gapAmount) - Math.abs(b.price - gapAmount)
      );

  return pool.slice(0, limit).map((item) => ({
    id: item.id,
    name: item.name,
    price: item.price,
  }));
}

/** Cart-aware payment offers based on the live cart subtotal.
 *  Shows the best already-unlocked offer plus the next upsell nudge. */
export function computePaymentOffers(cart, subtotal, context, fillerPool = []) {
  const tiers = buildTiers(context, cart);
  const unlocked = [];
  const locked = [];

  for (const tier of tiers) {
    const maxLabel = tier.flatSavings ?? tier.maxSavings;

    if (subtotal >= tier.minSubtotal) {
      const applied = tier.flatSavings != null
        ? tier.flatSavings
        : Math.round(Math.min(subtotal * (tier.rate ?? 0), tier.maxSavings));

      unlocked.push({
        id: tier.id,
        title: tier.title,
        detail: `Save ₹${applied} • Applied at checkout ✓`,
        eligible: true,
        savings: applied,
        gap_amount: 0,
        suggested_items: [],
      });
    } else {
      const gap = Math.ceil(tier.minSubtotal - subtotal);
      const suggested = pickSuggestedItems(gap, cart, fillerPool);
      const names = suggested.map((item) => item.name).join(", ");

      let detail = `Add ₹${gap} more to avail ${tier.title} (save up to ₹${maxLabel})`;
      if (names) {
        detail += ` — try ${names}`;
      }

      locked.push({
        id: tier.id,
        title: tier.title,
        detail,
        eligible: false,
        savings: 0,
        gap_amount: gap,
        suggested_items: suggested,
      });
    }
  }

  unlocked.sort((a, b) => b.savings - a.savings);
  locked.sort((a, b) => a.gap_amount - b.gap_amount);

  return [...unlocked.slice(0, 1), ...locked.slice(0, 1), ...unlocked.slice(1)].slice(0, 2);
}
