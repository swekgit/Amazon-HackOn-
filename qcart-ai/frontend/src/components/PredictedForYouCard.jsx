import { useState } from "react";
import { Lock } from "lucide-react";

export default function PredictedForYouCard({ predictions, onAddKit }) {
  const [dismissed, setDismissed] = useState(new Set());

  if (!predictions || predictions.length === 0) return null;

  const visible = predictions.filter((p) => !dismissed.has(p.customer_id + p.label));

  if (visible.length === 0) return null;

  return (
    <section className="space-y-4">
      {visible.map((prediction) => {
        const subtotal = prediction.cart?.reduce((s, item) => s + item.price, 0) || 0;
        const key = prediction.customer_id + prediction.label;

        return (
          <div
            key={key}
            className="rounded-3xl bg-white p-6 ring-1 ring-black/5 shadow-sm"
          >
            {/* Top row */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xl">🔮</span>
                <h3 className="font-display text-lg text-ink">
                  {prediction.label}
                </h3>
              </div>

              {prediction.private && (
                <span className="inline-flex items-center gap-1 rounded-full bg-smart-soft px-2.5 py-1 text-xs font-medium text-smart">
                  <Lock className="h-3 w-3" />
                  Private to you
                </span>
              )}
            </div>

            {/* Subtitle */}
            <p className="mt-1 text-sm text-ink/60">
              Due in ~{prediction.days_until_due} days · you usually reorder every{" "}
              {prediction.interval_days} days
            </p>

            {/* Kit items */}
            <div className="mt-4 space-y-2">
              {prediction.cart?.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-ink/80">{item.name}</span>
                  <span className="font-display text-ink">₹{item.price}</span>
                </div>
              ))}
            </div>

            {/* Subtotal */}
            <div className="mt-3 flex items-center justify-between border-t border-black/5 pt-3">
              <span className="text-sm font-medium text-ink/60">Subtotal</span>
              <span className="font-display text-lg text-ink">₹{subtotal}</span>
            </div>

            {/* Actions */}
            <div className="mt-4 flex gap-3">
              <button
                onClick={() => onAddKit(prediction)}
                className="flex-1 rounded-xl bg-smart px-4 py-2.5 text-sm font-medium text-white transition hover:scale-[1.02]"
              >
                Add Kit
              </button>

              <button
                onClick={() =>
                  setDismissed((prev) => new Set([...prev, key]))
                }
                className="rounded-xl px-4 py-2.5 text-sm font-medium text-ink/50 transition hover:text-ink/80"
              >
                Not now
              </button>
            </div>
          </div>
        );
      })}
    </section>
  );
}
