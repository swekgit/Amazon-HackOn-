import { motion } from "framer-motion";
import { Sparkles, Plus, Minus, Truck } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import { PRODUCTS, getCategoryEmoji } from "../data/products.js";
import { getFrequentlyBought } from "../data/orders.js";
import { formatINR } from "../lib/format.js";

function getBadge(product) {
  const categoryPrices = PRODUCTS.filter((p) => p.category === product.category).map((p) => p.price);
  const min = Math.min(...categoryPrices);
  const max = Math.max(...categoryPrices);
  if (product.price === min && categoryPrices.length > 1) return { label: "BEST VALUE", color: "bg-green-600" };
  if (product.tags.includes("instant")) return { label: "FASTEST", color: "bg-blue-600" };
  if (product.price === max && categoryPrices.length > 1) return { label: "PREMIUM", color: "bg-amber-600" };
  return null;
}

export default function AIRecommendations() {
  const { addProduct, cart, setQty, removeItem } = useApp();

  // Build recommendations: items related to frequent purchases + some variety
  const frequent = getFrequentlyBought();
  const frequentCategories = new Set(frequent.map((p) => p.category));
  const frequentIds = new Set(frequent.map((p) => p.id));

  const recommendations = PRODUCTS
    .filter((p) => !frequentIds.has(p.id))
    .filter((p) => frequentCategories.has(p.category) || p.tags.includes("breakfast") || p.tags.includes("snack"))
    .slice(0, 8);

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <Sparkles size={18} style={{ color: "#F97316" }} />
        <h2 className="font-display text-lg sm:text-xl font-bold text-gray-900">Recommended for You</h2>
      </div>
      <p className="text-xs text-gray-500 mb-4">Based on your shopping patterns</p>

      <div className="grid grid-cols-1 min-[360px]:grid-cols-2 md:grid-cols-3 lg:flex gap-3 lg:overflow-x-auto no-scrollbar pb-3 snap-x-mandatory">
        {recommendations.map((product, i) => {
          const badge = getBadge(product);
          const cartItem = cart.find((c) => c.id === product.id);
          const qty = cartItem?.quantity || 0;
          return (
            <motion.div
              key={product.id}
              initial={{ opacity: 0, y: 15 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06, duration: 0.4 }}
              viewport={{ once: true }}
              className="shrink-0 w-full lg:w-44 rounded-xl bg-white flex flex-col overflow-hidden relative hover:shadow-md transition-shadow"
              style={{ border: "1px solid #E5E7EB" }}
            >
              {/* Badge */}
              {badge && (
                <span className={`absolute top-2 left-2 z-10 ${badge.color} text-[9px] font-bold px-2 py-0.5 rounded-md text-white uppercase tracking-wider`}>
                  {badge.label}
                </span>
              )}

              {/* Product visual */}
              <div className="flex items-center justify-center bg-gray-50 py-4">
                <span className="text-3xl">{getCategoryEmoji(product.category)}</span>
              </div>

              {/* Info */}
              <div className="flex flex-col flex-1 px-3 pt-2 pb-3">
                <p className="font-medium text-[13px] leading-snug line-clamp-2 text-gray-900 min-h-[2.25rem]">
                  {product.name}
                </p>
                <p className="mt-1 font-display font-bold text-gray-900">{formatINR(product.price)}</p>

                {/* Delivery estimate */}
                <div className="mt-1 flex items-center gap-1 text-[11px] text-green-600">
                  <Truck size={10} />
                  <span>10 min</span>
                </div>

                {/* Spacer */}
                <div className="flex-1 min-h-1" />

                {/* CTA — quantity stepper or Add */}
                <div className="mt-2.5">
                  {qty > 0 ? (
                    <div
                      className="flex items-center justify-between rounded-lg overflow-hidden h-[44px]"
                      style={{ border: "1px solid #E5E7EB" }}
                    >
                      <button
                        onClick={() =>
                          qty <= 1
                            ? removeItem(product.id)
                            : setQty(product.id, qty - 1)
                        }
                        className="grid h-11 w-11 shrink-0 place-items-center text-gray-700 hover:bg-gray-100 active:bg-gray-200 transition"
                      >
                        <Minus size={14} />
                      </button>
                      <span className="font-display font-bold text-sm text-gray-900 min-w-[2rem] text-center">
                        {qty}
                      </span>
                      <button
                        onClick={() => setQty(product.id, qty + 1)}
                        className="grid h-11 w-11 shrink-0 place-items-center text-gray-700 hover:bg-gray-100 active:bg-gray-200 transition"
                      >
                        <Plus size={14} />
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => addProduct({ ...product, reason: "recommended for you" })}
                      className="w-full flex items-center justify-center gap-1.5 rounded-lg min-h-[44px] text-xs font-semibold transition active:scale-[0.97]"
                      style={{ backgroundColor: "#FFD814", color: "#111827" }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#F7CA00")}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "#FFD814")}
                    >
                      <Plus size={12} />
                      Add
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
