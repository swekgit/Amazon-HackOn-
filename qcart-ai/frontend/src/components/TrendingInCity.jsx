import { motion, AnimatePresence } from "framer-motion";
import { MapPin, RefreshCw } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import ProductCard from "./ProductCard.jsx";

/* ── Skeleton loader ───────────────────────────────────────────────────────── */

function TrendingSkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="h-48 rounded-xl bg-gray-100 animate-pulse" />
      ))}
    </div>
  );
}

/* ── Main component ────────────────────────────────────────────────────────── */

export default function TrendingInCity() {
  const { city, trendingProducts, trendingLoading } = useApp();

  return (
    <div>
      {/* Section header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <MapPin size={18} style={{ color: "#F97316" }} />
          <h2 className="font-display text-lg sm:text-xl font-bold text-gray-900">
            Trending in {city}
          </h2>
        </div>
        {trendingLoading && (
          <RefreshCw size={14} className="text-gray-400 animate-spin" />
        )}
      </div>

      {/* Loading state */}
      {trendingLoading && trendingProducts.length === 0 && <TrendingSkeleton />}

      {/* Product cards — 5-column grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3">
        <AnimatePresence mode="popLayout">
          {trendingProducts.map((product, i) => (
            <ProductCard
              key={product.id}
              product={product}
              subtitle={product.tags?.slice(0, 2).join(", ")}
              badge={product.tags?.includes("premium") ? "Premium" : null}
              badgeColor="bg-amber-600"
              index={i}
            />
          ))}
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
          <p className="font-display text-sm font-semibold text-gray-400">
            No trending products for {city} yet
          </p>
          <p className="text-xs text-gray-300 mt-1">
            Try selecting a different city
          </p>
        </motion.div>
      )}
    </div>
  );
}
