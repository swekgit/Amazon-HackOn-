import { motion } from "framer-motion";
import { Minus, Plus, X } from "lucide-react";
import { formatINR } from "../lib/format.js";
import { getCategoryEmoji } from "../data/products.js";

function ProductBadge({ item }) {
  if (item.price < 60)
    return <span className="rounded-full bg-emerald-500 text-white text-[8px] font-bold px-1.5 py-0.5 uppercase">Best Value</span>;
  if (item.tags?.includes("instant"))
    return <span className="rounded-full bg-sky-500 text-white text-[8px] font-bold px-1.5 py-0.5 uppercase">Fastest</span>;
  if (item.price > 200)
    return <span className="rounded-full bg-purple-500 text-white text-[8px] font-bold px-1.5 py-0.5 uppercase">Premium</span>;
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
      className="flex items-start gap-3 rounded-2xl bg-white/80 px-4 py-3 ring-1 ring-black/5"
    >
      {/* Emoji avatar */}
      <div className={`shrink-0 grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br ${
        item.category === "snacks" ? "from-amber-100 to-orange-100" :
        item.category === "beverages" ? "from-sky-100 to-blue-100" :
        item.category === "health" ? "from-rose-100 to-red-100" :
        item.category === "baby" ? "from-pink-100 to-fuchsia-100" :
        item.category === "party" ? "from-violet-100 to-purple-100" :
        "from-emerald-100 to-green-100"
      } text-xl`}>
        {emoji}
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="truncate font-medium text-sm text-ink">{item.name}</p>
            <div className="flex items-center gap-1.5 mt-1">
              {item.reason && (
                <span className="inline-block rounded-full bg-canvas px-2 py-0.5 text-[10px] text-ink/50">
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
          <div className="flex items-center rounded-full ring-1 ring-black/10">
            <button onClick={() => onQty(item.id, item.quantity - 1)} aria-label="Decrease"
              className="grid h-7 w-7 place-items-center rounded-full hover:bg-canvas transition">
              <Minus size={12} />
            </button>
            <span className="w-6 text-center font-display text-sm font-medium">{item.quantity}</span>
            <button onClick={() => onQty(item.id, item.quantity + 1)} aria-label="Increase"
              className="grid h-7 w-7 place-items-center rounded-full hover:bg-canvas transition">
              <Plus size={12} />
            </button>
          </div>
          <span className="font-display font-semibold text-sm">
            {formatINR(item.price * item.quantity)}
          </span>
        </div>
      </div>
    </motion.div>
  );
}
