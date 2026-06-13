import { useEffect, useState } from "react";
import { Clock } from "lucide-react";
import { savings } from "../lib/format.js";

// The "proof" metric: how much friction this cart just removed.
export default function SavedCounter({ cart }) {
  const [animatedMinutes, setAnimatedMinutes] = useState(0);
  const [animatedTaps, setAnimatedTaps] = useState(0);

  if (!cart || cart.length === 0) return null;

  const { minutes, taps, oldMinutes } = savings(cart);

  useEffect(() => {
    let frame;
    const duration = 700;
    const start = performance.now();

    const animate = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);

      setAnimatedMinutes(Math.round(minutes * eased));
      setAnimatedTaps(Math.round(taps * eased));

      if (progress < 1) {
        frame = requestAnimationFrame(animate);
      }
    };

    setAnimatedMinutes(0);
    setAnimatedTaps(0);

    frame = requestAnimationFrame(animate);

    return () => cancelAnimationFrame(frame);
  }, [cart, minutes, taps]);

  return (
    <div className="animate-fade-up rounded-2xl bg-smart-soft px-4 py-3 text-smart-dark">
      <div className="flex items-center gap-2 text-sm">
        <Clock size={16} />
        <span>
          Built in seconds — saved you about{" "}
          <b className="font-display">{animatedMinutes} min</b> and{" "}
          <b className="font-display">{animatedTaps} taps</b>.
        </span>
      </div>

      <div className="mt-1 pl-6 text-xs text-smart-dark/70">
        Old way ~{oldMinutes} min · Now seconds
      </div>
    </div>
  );
}