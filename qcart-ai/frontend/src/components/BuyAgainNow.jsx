import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { RotateCcw, ShoppingCart, Check, ArrowRight } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import { getFrequentlyBought, getLastPurchaseDate, getPurchaseFrequency } from "../data/orders.js";
import { getCategoryEmoji } from "../data/products.js";
import { formatINR, formatTimeAgo } from "../lib/format.js";

export default function BuyAgainNow() {
  const { addProduct, setCartOpen } = useApp();
  const [built, setBuilt] = useState(false);
  const items = getFrequentlyBought();

  const handleBuildCart = () => {
    items.forEach((p) => addProduct({ ...p, reason: "frequently purchased" }));
    setBuilt(true);
    setTimeout(() => setCartOpen(true), 600);
  };

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <RotateCcw size={18} className="text-smart" />
        <div>
          <h2 className="font-display text-lg sm:text-xl font-bold text-ink">Buy Again</h2>
          <p className="text-xs text-ink/50">Your frequently purchased items</p>
        </div>
      </div>

      {/* Product scroll */}
      <div className="flex gap-3 overflow-x-auto no-scrollbar pb-3 snap-x-mandatory">
        {items.map((product, i) => {
          const lastDate = getLastPurchaseDate(product.id);
          const freq = getPurchaseFrequency(product.id);
          return (
            <motion.div
              key={product.id}
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.08, duration: 0.4 }}
              viewport={{ once: true }}
              whileHover={{ y: -3 }}
              className="shrink-0 w-44 rounded-xl bg-white p-4 ring-1 ring-border cursor-default hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-canvas mb-2">
                <span className="text-2xl">{getCategoryEmoji(product.category)}</span>
              </div>
              <p className="font-medium text-sm leading-snug line-clamp-2 text-ink">{product.name}</p>
              <p className="mt-1 font-display font-bold text-ink">{formatINR(product.price)}</p>
              <div className="mt-2 flex flex-col gap-1">
                {lastDate && (
                  <span className="text-[11px] text-ink/40">{formatTimeAgo(lastDate)}</span>
                )}
                <span className="inline-block rounded-full bg-smart-soft px-2 py-0.5 text-[10px] font-semibold text-smart-dark w-fit">
                  Ordered {freq}x
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* CTA Button */}
      <AnimatePresence mode="wait">
        {!built ? (
          <motion.button
            key="build"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            onClick={handleBuildCart}
            className="mt-3 flex items-center gap-2 rounded-full bg-amazonYellow px-6 py-3 font-display font-bold text-ink shadow-md hover:shadow-lg hover:bg-yellow-400 transition-all"
          >
            <ShoppingCart size={18} />
            Build My Repeat Cart
          </motion.button>
        ) : (
          <motion.button
            key="ready"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            onClick={() => setCartOpen(true)}
            className="mt-3 flex items-center gap-2 rounded-full bg-fresh px-6 py-3 font-display font-bold text-white shadow-md hover:shadow-lg transition-all"
          >
            <Check size={18} />
            Cart Ready — Checkout Now
            <ArrowRight size={16} />
          </motion.button>
        )}
      </AnimatePresence>
    </div>
  );
}
