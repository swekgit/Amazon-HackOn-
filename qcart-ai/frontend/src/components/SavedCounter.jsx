import { Clock } from "lucide-react";
import { savings } from "../lib/format.js";

// The "proof" metric: how much friction this cart just removed.
export default function SavedCounter({ cart }) {
  if (!cart || cart.length === 0) return null;
  const { minutes, taps } = savings(cart);

  return (
    <div className="flex items-center gap-2 rounded-2xl bg-smart-soft px-4 py-2.5 text-sm text-smart-dark animate-fade-up">
      <Clock size={16} />
      <span>
        Built in seconds — saved you about <b>{minutes} min</b> and <b>{taps} taps</b>.
      </span>
    </div>
  );
}
