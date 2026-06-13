import { useState } from "react";
import { motion } from "framer-motion";
import { Sparkles, Plus, Check, Truck } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import { PRODUCTS, getCategoryEmoji } from "../data/products.js";
import { getFrequentlyBought } from "../data/orders.js";
import { formatINR } from "../lib/format.js";

function getBadge(product) {
  const categoryPrices = PRODUCTS.filter((p) => p.category === product.category).map((p) => p.price);
  const min = Math.min(...categoryPrices);
  const max = Math.max(...categoryPrices);
  if (product.price === min && categoryPrices.length > 1) return { type: "value", label: "BEST VALUE", color: "bg-fresh text-white" };
  if (product.tags.includes("instant")) return { type: "fast", label: "FASTEST", color: "bg-prime text-white" };
  if (product.price === max && categoryPrices.length > 1) return { type: "premium", label: "PREMIUM PICK", color: "bg-smart text-white" };
  return null;
}

export default function AIRecommendations() {
  const { addProduct } = useApp();
  const [added, setAdded] = useState(new Set());

  // Build recommendations: items related to frequent purchases + some variety
  const frequent = getFrequentlyBought();
  const frequentCategories = new Set(frequent.map((p) => p.category));
  const frequentIds = new Set(frequent.map((p) => p.id));

  const recommendations = PRODUCTS
    .filter((p) => !frequentIds.has(p.id))
    .filter((p) => frequentCategories.has(p.category) || p.tags.includes("breakfast") || p.tags.includes("snack"))
    .slice(0, 8);

  const handleAdd = (product) => {
    addProduct({ ...product, reason: "recommended for you" });
    setAdded((prev) => new Set(prev).add(product.id));
  };

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <Sparkles size={18} className="text-smart" />
        <h2 className="font-display text-lg sm:text-xl font-bold text-ink">Recommended for You</h2>
      </div>
      <p className="text-xs text-ink/50 mb-4">Based on your shopping patterns</p>

      <div className="flex gap-3 overflow-x-auto no-scrollbar pb-3 snap-x-mandatory">
        {recommendations.map((product, i) => {
          const badge = getBadge(product);
          const isAdded = added.has(product.id);
          return (
            <motion.div
              key={product.id}
              initial={{ opacity: 0, y: 15 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06, duration: 0.4 }}
              viewport={{ once: true }}
              whileHover={{ y: -3 }}
              className="shrink-0 w-40 sm:w-44 rounded-xl bg-white p-4 ring-1 ring-border relative hover:shadow-md transition-shadow"
            >
              {badge && (
                <span className={`absolute top-2 right-2 ${badge.color} text-[9px] font-bold px-2 py-0.5 rounded-md uppercase tracking-wider`}>
                  {badge.label}
                </span>
              )}
              <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-canvas mb-2">
                <span className="text-2xl">{getCategoryEmoji(product.category)}</span>
              </div>
              <p className="font-medium text-sm leading-snug line-clamp-2 text-ink">{product.name}</p>
              <p className="mt-1 font-display font-bold text-ink">{formatINR(product.price)}</p>

              {/* Delivery estimate */}
              <div className="mt-1 flex items-center gap-1 text-[11px] text-fresh">
                <Truck size={10} />
                <span>10 min</span>
              </div>

              <button
                onClick={() => handleAdd(product)}
                disabled={isAdded}
                className={`mt-2 w-full flex items-center justify-center gap-1.5 rounded-lg py-2 text-xs font-semibold transition ${
                  isAdded
                    ? "bg-fresh-soft text-fresh"
                    : "bg-amazonYellow text-ink hover:bg-yellow-400"
                }`}
              >
                {isAdded ? <><Check size={12} /> Added</> : <><Plus size={12} /> Add</>}
              </button>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
