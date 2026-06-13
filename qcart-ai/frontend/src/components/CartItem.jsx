import { motion } from "framer-motion";
import { Minus, Plus, X } from "lucide-react";
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

export default function CartItem({ item, index, onQty, onRemove }) {
  const emoji = getCategoryEmoji(item.category);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ delay: index * 0.04, duration: 0.3 }}
      whileHover={{ scale: 1.01 }}
      className="flex items-start gap-3 rounded-xl bg-white px-4 py-3 ring-1 ring-border"
    >
      {/* Emoji avatar */}
      <div className={`shrink-0 grid h-10 w-10 place-items-center rounded-lg bg-gradient-to-br ${
        item.category === "snacks" ? "from-amber-50 to-orange-50" :
        item.category === "beverages" ? "from-sky-50 to-blue-50" :
        item.category === "health" ? "from-rose-50 to-red-50" :
        item.category === "baby" ? "from-pink-50 to-fuchsia-50" :
        item.category === "party" ? "from-violet-50 to-purple-50" :
        "from-emerald-50 to-green-50"
      } text-xl`}>
        {emoji}
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="truncate font-medium text-sm text-ink">{item.name}</p>
            <div className="flex items-center gap-1.5 mt-1">
              {item.reason && (
                <span className="inline-block rounded-md bg-canvas px-2 py-0.5 text-[10px] text-ink/50">
                  {item.reason}
                </span>
              )}
              <ProductBadge item={item} />
            </div>
          </div>
          <button onClick={() => onRemove(item.id)} aria-label={`Remove ${item.name}`}
            className="shrink-0 p-1 text-black/20 transition hover:text-red-500">
            <X size={14} />
          </button>
        </div>
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center rounded-full ring-1 ring-border">
            <button onClick={() => onQty(item.id, item.quantity - 1)} aria-label="Decrease"
              className="grid h-7 w-7 place-items-center rounded-full hover:bg-canvas transition">
              <Minus size={12} />
            </button>
            <span className="w-6 text-center font-display text-sm font-medium text-ink">{item.quantity}</span>
            <button onClick={() => onQty(item.id, item.quantity + 1)} aria-label="Increase"
              className="grid h-7 w-7 place-items-center rounded-full hover:bg-canvas transition">
              <Plus size={12} />
            </button>
          </div>
          <span className="font-display font-bold text-sm text-ink">
            {formatINR(item.price * item.quantity)}
          </span>
        </div>
      </div>
    </motion.div>
  );
}
