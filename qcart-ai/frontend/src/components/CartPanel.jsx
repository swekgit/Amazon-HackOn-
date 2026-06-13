import { useState } from "react";
import { Zap, CheckCircle2, Plus } from "lucide-react";
import CartItem from "./CartItem.jsx";
import ReadinessPanel from "./ReadinessPanel.jsx";
import { formatINR } from "../lib/format.js";

export default function CartPanel({ cart, subtotal, suggestions, readiness, theme, onQty, onRemove, onAdd }) {
  const [placed, setPlaced] = useState(false);

  if (placed) {
    return (
      <div className="animate-pop-in rounded-3xl bg-white p-10 text-center ring-1 ring-black/5">
        <div className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-fresh-soft">
          <CheckCircle2 className="text-fresh" size={34} />
        </div>
        <h2 className="mt-5 font-display text-2xl font-semibold">Order placed</h2>
        <p className="mt-1.5 flex items-center justify-center gap-1.5 text-ink/60">
          <Zap size={16} className="text-fresh" /> Arriving in 10 minutes
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* Readiness score — renders above cart items */}
      <ReadinessPanel readiness={readiness} onAdd={onAdd} />

      <div className="space-y-3">
        {cart.map((item, i) => (
          <CartItem key={item.id} item={item} index={i} onQty={onQty} onRemove={onRemove} />
        ))}
      </div>

      {suggestions?.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {suggestions.map((s) => (
            <button key={s.id} onClick={() => onAdd(s)}
              className="inline-flex min-h-[40px] items-center gap-1.5 rounded-full bg-white px-3.5 py-2 text-sm text-ink/70 ring-1 ring-black/10 transition hover:ring-smart active:scale-[0.98]">
              <Plus size={13} /> {s.name} · {formatINR(s.price)}
            </button>
          ))}
        </div>
      )}

      <div className="mt-6 rounded-3xl bg-ink p-5 text-white shadow-lg">
        <div className="flex items-end justify-between">
          <span className="text-sm text-white/60">Subtotal</span>
          <span className="font-display text-2xl font-semibold">{formatINR(subtotal)}</span>
        </div>
        <button
          onClick={() => setPlaced(true)}
          className={`mt-4 flex min-h-[52px] w-full items-center justify-center gap-2 rounded-2xl py-3.5 font-display font-semibold text-white transition focus:outline-none focus-visible:ring-2 ${theme.btn} ${theme.ring}`}
        >
          <Zap size={18} /> Place order · 10 min delivery
        </button>
      </div>
    </div>
  );
}
