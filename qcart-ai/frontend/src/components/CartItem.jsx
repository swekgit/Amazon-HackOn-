import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Minus, Plus, X, ArrowUp, ArrowDown } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import { formatINR } from "../lib/format.js";
import { getCategoryEmoji } from "../data/products.js";

const SAMPLE_ALTERNATIVES = {
  cheaper: { id: "p004", name: "Potato Chips", price: 50 },
  premium: { id: "p009", name: "Premium Belgian Chocolate", price: 499 },
};

export default function CartItem({ item, index, onQty, onRemove }) {
  const emoji = getCategoryEmoji(item.category);
  const { swapItem } = useApp();
  const alternatives = item.alternatives || SAMPLE_ALTERNATIVES;
  const [candidate, setCandidate] = useState(null);

  // Show only ONE direction — cheaper if item is expensive, premium if cheap
  const showCheaper = alternatives.cheaper && item.price > 80;
  const showPremium = !showCheaper && alternatives.premium;

  const confirmSwap = () => {
    if (!candidate) return;
    swapItem(item.id, {
      ...candidate.product,
      category: item.category,
      quantity: item.quantity,
      reason: candidate.type === "premium" ? "Upgraded" : "Money Saver",
    });
    setCandidate(null);
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ delay: index * 0.03, duration: 0.25 }}
      className="rounded-card bg-white ring-1 ring-line overflow-hidden"
    >
      <div className="flex items-start gap-3 p-3">
        {/* Large emoji tile */}
        <div className="shrink-0 grid h-12 w-12 place-items-center rounded-xl bg-canvas text-2xl">
          {emoji}
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          {/* Name + remove */}
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-ink">{item.name}</p>
              <p className="text-[11px] text-muted capitalize">{item.category}</p>
            </div>
            <button
              onClick={() => onRemove(item.id)}
              aria-label={`Remove ${item.name}`}
              className="shrink-0 p-3 -m-2 rounded-lg text-muted hover:text-rose hover:bg-rose-soft transition"
            >
              <X size={14} />
            </button>
          </div>

          {/* Swap action — only ONE direction */}
          <div className="mt-1.5">
            {showCheaper && (
              <button
                onClick={() => setCandidate({ type: "cheaper", product: alternatives.cheaper })}
                className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium bg-green-soft text-green ring-1 ring-green/10 hover:ring-green/30 transition"
              >
                <ArrowDown size={9} />
                Cheaper · {formatINR(alternatives.cheaper.price)}
              </button>
            )}
            {showPremium && (
              <button
                onClick={() => setCandidate({ type: "premium", product: alternatives.premium })}
                className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium bg-brand-soft text-brand-deep ring-1 ring-brand/10 hover:ring-brand/30 transition"
              >
                <ArrowUp size={9} />
                Premium · {formatINR(alternatives.premium.price)}
              </button>
            )}
          </div>

          {/* Price + Qty stepper */}
          <div className="flex items-center justify-between mt-2.5">
            <div className="flex items-center rounded-full ring-1 ring-line bg-canvas h-11">
              <button
                onClick={() => onQty(item.id, item.quantity - 1)}
                aria-label="Decrease"
                className="grid h-full w-11 place-items-center rounded-full hover:bg-white transition"
              >
                <Minus size={14} />
              </button>
              <span className="w-6 text-center font-display text-sm font-semibold text-ink">
                {item.quantity}
              </span>
              <button
                onClick={() => onQty(item.id, item.quantity + 1)}
                aria-label="Increase"
                className="grid h-full w-11 place-items-center rounded-full hover:bg-white transition"
              >
                <Plus size={14} />
              </button>
            </div>

            <span className="font-display font-bold text-sm text-ink">
              {formatINR(item.price * item.quantity)}
            </span>
          </div>
        </div>
      </div>

      {/* Swap confirmation */}
      <AnimatePresence>
        {candidate && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-line overflow-hidden"
          >
            <div className="p-3 bg-canvas">
              <p className="text-xs text-ink mb-2">
                Switch to <span className="font-semibold">{candidate.product.name}</span> for {formatINR(candidate.product.price)}?
              </p>
              <div className="flex gap-2">
                <button
                  onClick={confirmSwap}
                  className="flex-1 rounded-lg bg-brand py-2 text-xs font-semibold text-white transition hover:bg-brand-deep"
                >
                  Confirm
                </button>
                <button
                  onClick={() => setCandidate(null)}
                  className="flex-1 rounded-lg bg-white py-2 text-xs font-semibold text-ink ring-1 ring-line transition hover:bg-canvas"
                >
                  Cancel
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
