import { motion, AnimatePresence } from "framer-motion";
import { TrendingUp, MapPin, Plus, RefreshCw } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import { formatINR } from "../lib/format.js";

/* ── Tag → visual mapping ──────────────────────────────────────────────────── */

const TAG_STYLE = {
  movie:     { bg: "bg-purple-50",  border: "border-purple-200", text: "text-purple-600" },
  snack:     { bg: "bg-amber-50",   border: "border-amber-200",  text: "text-amber-600" },
  party:     { bg: "bg-pink-50",    border: "border-pink-200",   text: "text-pink-600" },
  drink:     { bg: "bg-sky-50",     border: "border-sky-200",    text: "text-sky-600" },
  breakfast: { bg: "bg-orange-50",  border: "border-orange-200", text: "text-orange-600" },
  weekly:    { bg: "bg-emerald-50", border: "border-emerald-200", text: "text-emerald-600" },
  staple:    { bg: "bg-green-50",   border: "border-green-200",  text: "text-green-600" },
  dairy:     { bg: "bg-blue-50",    border: "border-blue-200",   text: "text-blue-600" },
  fruit:     { bg: "bg-lime-50",    border: "border-lime-200",   text: "text-lime-600" },
  fever:     { bg: "bg-red-50",     border: "border-red-200",    text: "text-red-600" },
  medicine:  { bg: "bg-rose-50",    border: "border-rose-200",   text: "text-rose-600" },
  baby:      { bg: "bg-fuchsia-50", border: "border-fuchsia-200", text: "text-fuchsia-600" },
  premium:   { bg: "bg-amber-50",   border: "border-amber-300",  text: "text-amber-700" },
};

const DEFAULT_STYLE = { bg: "bg-gray-50", border: "border-gray-200", text: "text-gray-600" };

function getCardStyle(tags = []) {
  for (const t of tags) {
    if (TAG_STYLE[t]) return TAG_STYLE[t];
  }
  return DEFAULT_STYLE;
}

/* ── Skeleton loader ───────────────────────────────────────────────────────── */

function TrendingSkeleton() {
  return (
    <div className="flex gap-3 overflow-hidden pb-3">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="shrink-0 w-40 h-36 rounded-xl skeleton" />
      ))}
    </div>
  );
}

/* ── Main component ────────────────────────────────────────────────────────── */

export default function TrendingInCity() {
  const { city, trendingProducts, trendingLoading, addProduct } = useApp();

  return (
    <div>
      {/* Section header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <MapPin size={18} className="text-smart" />
          <h2 className="font-display text-lg sm:text-xl font-bold text-ink">
            Trending in {city}
          </h2>
        </div>
        {trendingLoading && (
          <RefreshCw size={14} className="text-ink/30 animate-spin" />
        )}
      </div>

      {/* Loading state */}
      {trendingLoading && trendingProducts.length === 0 && <TrendingSkeleton />}

      {/* Product cards */}
      <div className="flex gap-3 overflow-x-auto no-scrollbar pb-3 snap-x-mandatory">
        <AnimatePresence mode="popLayout">
          {trendingProducts.map((product, i) => {
            const style = getCardStyle(product.tags);
            return (
              <motion.div
                key={product.id}
                layout
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ delay: i * 0.05, duration: 0.35 }}
                className={`shrink-0 rounded-xl ${style.bg} border ${style.border} p-4 w-40 sm:w-44 text-left transition-all hover:shadow-md relative overflow-hidden group`}
              >
                {/* Price tag */}
                <div className="flex items-center justify-between mb-2">
                  <span className="font-display font-bold text-base text-ink">
                    {formatINR(product.price)}
                  </span>
                  {product.tags?.includes("premium") && (
                    <span className="rounded-md bg-amber-200/80 px-1.5 py-0.5 text-[8px] font-bold text-amber-800 uppercase">
                      Premium
                    </span>
                  )}
                </div>

                {/* Product name */}
                <p className="font-medium text-sm leading-snug text-ink line-clamp-2 min-h-[2.5rem]">
                  {product.name}
                </p>

                {/* Tags */}
                <div className="flex flex-wrap gap-1 mt-2">
                  {product.tags?.slice(0, 2).map((tag) => (
                    <span
                      key={tag}
                      className={`rounded-full px-2 py-0.5 text-[9px] font-semibold ${
                        TAG_STYLE[tag]?.text || "text-gray-500"
                      } bg-white/70`}
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                {/* Quick-add button */}
                <motion.button
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={() => addProduct(product)}
                  className="absolute bottom-3 right-3 grid h-7 w-7 place-items-center rounded-full bg-white shadow-sm ring-1 ring-border text-smart opacity-0 group-hover:opacity-100 transition-opacity"
                  title={`Add ${product.name} to cart`}
                >
                  <Plus size={14} />
                </motion.button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Empty state */}
      {!trendingLoading && trendingProducts.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center justify-center py-10 text-center"
        >
          <div className="text-4xl mb-3">📍</div>
          <p className="font-display text-sm font-semibold text-ink/50">
            No trending products for {city} yet
          </p>
          <p className="text-xs text-ink/30 mt-1">
            Try selecting a different city
          </p>
        </motion.div>
      )}
    </div>
  );
}
