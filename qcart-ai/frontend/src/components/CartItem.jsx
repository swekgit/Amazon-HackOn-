import { useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Minus,
  Plus,
  X,
  ArrowDown,
  ArrowUp,
} from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import { formatINR } from "../lib/format.js";
import { getCategoryEmoji } from "../data/products.js";

function ProductBadge({ item }) {
  if (item.price < 60)
    return <span className="rounded-md bg-fresh text-white text-[8px] font-bold px-1.5 py-0.5 uppercase">Best Value</span>;
  if (item.tags?.includes("instant"))
    return <span className="rounded-md bg-prime text-white text-[8px] font-bold px-1.5 py-0.5 uppercase">Fastest</span>;
  if (item.price > 200)
    return <span className="rounded-md bg-smart text-white text-[8px] font-bold px-1.5 py-0.5 uppercase">Premium</span>;
  return null;
}
const SAMPLE_ALTERNATIVES = {
  cheaper: {
    id: "p004",
    name: "Potato Chips",
    price: 50,
  },
  premium: {
    id: "p009",
    name: "Premium Belgian Chocolate",
    price: 499,
  },
};

export default function CartItem({ item, index, onQty, onRemove }) {
  const emoji = getCategoryEmoji(item.category);
  const { swapItem } = useApp();

const alternatives =
  item.alternatives || SAMPLE_ALTERNATIVES;

const [candidate, setCandidate] = useState(null);

const startX = useRef(0);

const handlePointerDown = (e) => {
  startX.current = e.clientX;
};

const handlePointerUp = (e) => {
  const diff = e.clientX - startX.current;

  if (diff > 70 && alternatives.premium) {
    setCandidate({
      type: "premium",
      product: alternatives.premium,
    });
  }

  if (diff < -70 && alternatives.cheaper) {
    setCandidate({
      type: "cheaper",
      product: alternatives.cheaper,
    });
  }
};

const confirmSwap = () => {
  if (!candidate) return;

  swapItem(item.id, {
    ...candidate.product,
    category: item.category,
    quantity: item.quantity,
    reason:
      candidate.type === "premium"
        ? "Upgraded"
        : "Money Saver",
  });

  setCandidate(null);
};

  return (
  <motion.div
    layout
    initial={{ opacity: 0, x: 20 }}
    animate={{ opacity: 1, x: 0 }}
    exit={{ opacity: 0, x: -20 }}
    transition={{
      delay: index * 0.04,
      duration: 0.3,
    }}
    onPointerDown={handlePointerDown}
    onPointerUp={handlePointerUp}
    className="relative overflow-hidden rounded-xl"
  >

    <motion.div
      layout
      whileHover={{ scale: 1.01 }}
      className="flex items-start gap-3 bg-white px-4 py-3 ring-1 ring-border"
    >
      {/* Emoji avatar */}
      <div
        className={`shrink-0 grid h-10 w-10 place-items-center rounded-lg bg-gradient-to-br ${
          item.category === "snacks"
            ? "from-amber-50 to-orange-50"
            : item.category === "beverages"
            ? "from-sky-50 to-blue-50"
            : item.category === "health"
            ? "from-rose-50 to-red-50"
            : item.category === "baby"
            ? "from-pink-50 to-fuchsia-50"
            : item.category === "party"
            ? "from-violet-50 to-purple-50"
            : "from-emerald-50 to-green-50"
        } text-xl`}
      >
        {emoji}
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="truncate font-medium text-sm text-ink">
              {item.name}
            </p>

            <div className="flex items-center gap-1.5 mt-1">
              {item.reason && (
                <span className="inline-block rounded-md bg-canvas px-2 py-0.5 text-[10px] text-ink/50">
                  {item.reason}
                </span>
              )}

              <ProductBadge item={item} />
            </div>

            {/* Fallback Chips */}
            <div className="flex gap-2 mt-2 flex-wrap">
              {alternatives.cheaper && (
                <button
                  onClick={() =>
                    setCandidate({
                      type: "cheaper",
                      product: alternatives.cheaper,
                    })
                  }
                  className="flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-medium bg-fresh/10 text-fresh"
                >
                  <ArrowDown size={10} />
                  Cheaper ₹{alternatives.cheaper.price}
                </button>
              )}

              {alternatives.premium && (
                <button
                  onClick={() =>
                    setCandidate({
                      type: "premium",
                      product: alternatives.premium,
                    })
                  }
                  className="flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-medium bg-smart/10 text-smart"
                >
                  <ArrowUp size={10} />
                  Premium ₹{alternatives.premium.price}
                </button>
              )}
            </div>
          </div>

          <button
            onClick={() => onRemove(item.id)}
            aria-label={`Remove ${item.name}`}
            className="shrink-0 p-1 text-black/20 transition hover:text-red-500"
          >
            <X size={14} />
          </button>
        </div>

        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center rounded-full ring-1 ring-border">
            <button
              onClick={() => onQty(item.id, item.quantity - 1)}
              aria-label="Decrease"
              className="grid h-7 w-7 place-items-center rounded-full hover:bg-canvas transition"
            >
              <Minus size={12} />
            </button>

            <span className="w-6 text-center font-display text-sm font-medium text-ink">
              {item.quantity}
            </span>

            <button
              onClick={() => onQty(item.id, item.quantity + 1)}
              aria-label="Increase"
              className="grid h-7 w-7 place-items-center rounded-full hover:bg-canvas transition"
            >
              <Plus size={12} />
            </button>
          </div>

          <span className="font-display font-bold text-sm text-ink">
            {formatINR(item.price * item.quantity)}
          </span>
        </div>
      </div>
    </motion.div>

    <AnimatePresence>
      {candidate && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 8 }}
          className="mt-2 rounded-xl border border-border bg-white p-3"
        >
          <p className="text-xs text-ink mb-2">
            Replace with{" "}
            <span className="font-semibold">
              {candidate.product.name}
            </span>{" "}
            for ₹{candidate.product.price}?
          </p>

          <div className="flex gap-2">
            <button
              onClick={confirmSwap}
              className="flex-1 rounded-lg bg-smart text-white py-2 text-xs font-medium"
            >
              Confirm
            </button>

            <button
              onClick={() => setCandidate(null)}
              className="flex-1 rounded-lg bg-canvas py-2 text-xs font-medium"
            >
              Cancel
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  </motion.div>
);
}