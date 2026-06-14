import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { RotateCcw, ShoppingCart, Check, ArrowRight, Plus, Minus } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import { getFrequentlyBought, getLastPurchaseDate, getPurchaseFrequency } from "../data/orders.js";
import { getCategoryEmoji } from "../data/products.js";
import { formatINR, formatTimeAgo } from "../lib/format.js";

export default function BuyAgainNow() {
  const { addProduct, cart, setQty, removeItem, setCartOpen } = useApp();
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
        <RotateCcw size={18} style={{ color: "#F97316" }} />
        <div>
          <h2 className="font-display text-lg sm:text-xl font-bold text-gray-900">Buy Again</h2>
          <p className="text-xs text-gray-500">Your frequently purchased items</p>
        </div>
      </div>

      {/* Product scroll */}
      <div className="flex gap-3 overflow-x-auto no-scrollbar pb-3 snap-x-mandatory">
        {items.map((product, i) => {
          const lastDate = getLastPurchaseDate(product.id);
          const freq = getPurchaseFrequency(product.id);
          const cartItem = cart.find((c) => c.id === product.id);
          const qty = cartItem?.quantity || 0;
          return (
            <motion.div
              key={product.id}
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.08, duration: 0.4 }}
              viewport={{ once: true }}
              className="shrink-0 w-44 rounded-xl bg-white flex flex-col overflow-hidden hover:shadow-md transition-shadow"
              style={{ border: "1px solid #E5E7EB" }}
            >
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

                <div className="mt-1.5 flex flex-col gap-0.5">
                  {lastDate && (
                    <span className="text-[11px] text-gray-400">{formatTimeAgo(lastDate)}</span>
                  )}
                  <span
                    className="inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold w-fit"
                    style={{ backgroundColor: "#FFF7ED", color: "#EA580C" }}
                  >
                    Ordered {freq}x
                  </span>
                </div>

                {/* Spacer */}
                <div className="flex-1 min-h-1" />

                {/* CTA — Add button or quantity stepper */}
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
                      onClick={() => addProduct({ ...product, reason: "frequently purchased" })}
                      className="w-full flex items-center justify-center gap-1.5 rounded-lg min-h-[44px] text-sm font-semibold transition active:scale-[0.97]"
                      style={{ backgroundColor: "#FFD814", color: "#111827" }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#F7CA00")}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "#FFD814")}
                    >
                      <Plus size={14} />
                      Add
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Build Repeat Cart CTA */}
      <AnimatePresence mode="wait">
        {!built ? (
          <motion.button
            key="build"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            onClick={handleBuildCart}
            className="mt-3 flex items-center gap-2 rounded-full px-6 py-3 font-display font-bold shadow-md hover:shadow-lg transition-all"
            style={{ backgroundColor: "#FFD814", color: "#111827" }}
            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#F7CA00")}
            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "#FFD814")}
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
            className="mt-3 flex items-center gap-2 rounded-full bg-green-600 px-6 py-3 font-display font-bold text-white shadow-md hover:shadow-lg transition-all"
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
