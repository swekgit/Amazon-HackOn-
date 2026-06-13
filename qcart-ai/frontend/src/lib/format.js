// ₹ formatting
export const formatINR = (n) => "₹" + Math.round(n).toLocaleString("en-IN");

// "Time & taps saved" — a defensible heuristic vs the old search-compare-add flow.
// Old way: per distinct item ≈ 4 min and ≈ 6 taps (search, scroll, compare, add),
// plus ~6 min / 8 taps of browsing overhead. New way: ~8 seconds, ~2 taps.
export function savings(cart) {
  const lines = cart.length;

  const oldMinutes = lines * 4 + 6;
  const oldTaps = lines * 6 + 8;

  return {
    oldMinutes,
    minutes: Math.max(0, oldMinutes),
    taps: Math.max(0, oldTaps - 2),
  };
}
