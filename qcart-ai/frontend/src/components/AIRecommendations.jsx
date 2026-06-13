import { useState } from "react";
import { motion } from "framer-motion";
import { Sparkles, Plus, Check } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import { PRODUCTS, getCategoryEmoji } from "../data/products.js";
import { getFrequentlyBought } from "../data/orders.js";
import { formatINR } from "../lib/format.js";

function getBadge(product) {
  const categoryPrices = PRODUCTS.filter((p) => p.category === product.category).map((p) => p.price);
  const min = Math.min(...categoryPrices);
  const max = Math.max(...categoryPrices);
  if (product.price === min && categoryPrices.length > 1) return { type: "value", label: "BEST VALUE", color: "bg-emerald-500" };
  if (product.tags.includes("instant")) return { type: "fast", label: "FASTEST", color: "bg-sky-500" };
  if (product.price === max && categoryPrices.length > 1) return { type: "premium", label: "PREMIUM", color: "bg-purple-500" };
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
        <Sparkles size={20} className="text-smart" />
        <h2 className="font-display text-xl sm:text-2xl font-bold">Recommended for You</h2>
      </div>
      <p className="text-sm text-ink/50 mb-6">Based on your shopping patterns</p>

      <div className="flex gap-3 overflow-x-auto no-scrollbar pb-4 snap-x-mandatory">
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
              className="shrink-0 w-40 sm:w-44 rounded-2xl glass p-4 ring-1 ring-black/5 relative"
            >
              {badge && (
                <span className={`absolute top-2 right-2 ${badge.color} text-white text-[9px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider`}>
                  {badge.label}
                </span>
              )}
              <div className="text-3xl mb-2">{getCategoryEmoji(product.category)}</div>
              <p className="font-medium text-sm leading-snug line-clamp-2">{product.name}</p>
              <p className="mt-1 font-display font-semibold">{formatINR(product.price)}</p>
              <button
                onClick={() => handleAdd(product)}
                disabled={isAdded}
                className={`mt-3 w-full flex items-center justify-center gap-1.5 rounded-lg py-2 text-xs font-semibold transition ${
                  isAdded
                    ? "bg-fresh-soft text-fresh"
                    : "bg-smart-soft text-smart-dark hover:bg-smart/10"
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
