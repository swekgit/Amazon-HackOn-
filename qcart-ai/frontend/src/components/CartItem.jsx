import { Minus, Plus, X } from "lucide-react";
import { formatINR } from "../lib/format.js";

export default function CartItem({ item, index, onQty, onRemove }) {
  return (
    <div
   className="flex items-start gap-3 rounded-3xl bg-white px-4 py-3.5 shadow-sm ring-1 ring-black/5 animate-fade-up"      style={{
  animationDelay: `${120 + index * 90}ms`,
  animationFillMode: "both",
}}
    >
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium text-ink">{item.name}</p>
        {item.reason && (
          <span className="mt-1 inline-block rounded-full bg-canvas px-2.5 py-0.5 text-xs text-ink/55">
            {item.reason}
          </span>
        )}
      </div>
      <div className="flex flex-col items-end gap-2">
        <button
          onClick={() => onRemove(item.id)}
          aria-label={`Remove ${item.name}`}
          className="text-black/25 transition hover:text-ink"
        >
          <X size={15} />
        </button>
        <div className="flex items-center gap-2">
          <div className="flex items-center rounded-full ring-1 ring-black/10">
            <button onClick={() => onQty(item.id, item.quantity - 1)} aria-label="Decrease"
          className="grid h-9 w-9 place-items-center rounded-full transition hover:bg-canvas active:scale-95">
              <Minus size={13} />
            </button>
            <span className="w-8 text-center font-display text-sm font-medium">{item.quantity}</span>
            <button onClick={() => onQty(item.id, item.quantity + 1)} aria-label="Increase"
              className="grid h-7 w-7 place-items-center rounded-full hover:bg-canvas">
              <Plus size={13} />
            </button>
          </div>
          <span className="w-20 text-right font-display font-semibold whitespace-nowrap">
            {formatINR(item.price * item.quantity)}
          </span>
        </div>
      </div>
    </div>
  );
}
