import { Truck, Plus } from "lucide-react";
import { formatINR } from "../lib/format.js";

// Shows only when the cart is below the free-delivery threshold.
export default function GapNudge({ gapAmount, fillers, onAdd }) {
  if (!gapAmount || gapAmount <= 0) return null;

  return (
    <div className="animate-fade-up rounded-2xl bg-fresh-soft p-4 ring-1 ring-fresh/20">
      <p className="flex items-center gap-2 font-medium text-fresh">
        <Truck size={17} /> {formatINR(gapAmount)} away from free delivery
      </p>
      {fillers?.length > 0 && (
        <div className="mt-2.5 flex flex-wrap gap-2">
          {fillers.map((f) => (
            <button key={f.id} onClick={() => onAdd(f)}
              className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1.5 text-sm text-ink/80 ring-1 ring-black/10 transition hover:ring-fresh">
              <Plus size={13} /> {f.name} · {formatINR(f.price)}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
