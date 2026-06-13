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
      <div className="flex items-center gap-2 mb-6">
        <RotateCcw size={20} className="text-smart" />
        <div>
          <h2 className="font-display text-xl sm:text-2xl font-bold">Buy Again</h2>
          <p className="text-sm text-ink/50">Your frequently purchased items</p>
        </div>
      </div>

      {/* Product scroll */}
      <div className="flex gap-3 overflow-x-auto no-scrollbar pb-4 snap-x-mandatory">
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
              className="shrink-0 w-44 rounded-2xl glass p-4 ring-1 ring-black/5 cursor-default"
            >
              <div className="text-3xl mb-2">{getCategoryEmoji(product.category)}</div>
              <p className="font-medium text-sm leading-snug line-clamp-2">{product.name}</p>
              <p className="mt-1 font-display font-semibold text-smart">{formatINR(product.price)}</p>
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
            className="mt-4 flex items-center gap-2 rounded-xl bg-gradient-to-r from-smart to-smart-dark px-6 py-3.5 font-display font-semibold text-white shadow-lg shadow-smart/20 hover:shadow-xl hover:shadow-smart/30 transition-all"
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
            className="mt-4 flex items-center gap-2 rounded-xl bg-gradient-to-r from-fresh to-emerald-600 px-6 py-3.5 font-display font-semibold text-white shadow-lg shadow-fresh/20 hover:shadow-xl transition-all"
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
