import { useState, useEffect } from "react";

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

export function formatDeliveryTime() {
  const d = new Date(Date.now() + 10 * 60 * 1000);
  return d.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}

export function formatTimeAgo(dateString) {
  if (!dateString) return "";
  const then = new Date(dateString);
  const now = new Date();
  const diffDays = Math.floor((now - then) / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  return `${Math.floor(diffDays / 30)} months ago`;
}

export function useAnimatedCounter(target, duration = 1000) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    if (!target) return;
    const startTime = performance.now();
    let raf;
    function step(now) {
      const progress = Math.min((now - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
      setDisplay(Math.round(eased * target));
      if (progress < 1) raf = requestAnimationFrame(step);
    }
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return display;
}
