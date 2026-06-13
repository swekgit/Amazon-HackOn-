import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ShoppingCart, Zap, Plus, CheckCircle2, Sparkles } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import CartItem from "./CartItem.jsx";
import AICartSummary from "./AICartSummary.jsx";
import GapNudge from "./GapNudge.jsx";
import { formatINR } from "../lib/format.js";

export default function CartDrawer() {
  const { cart, subtotal, setCartOpen, meta, addProduct, setQty, removeItem, gapAmount, hasCart } = useApp();
  const [placed, setPlaced] = useState(false);

  return (
    <>
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={() => setCartOpen(false)}
        className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
      />

      {/* Drawer */}
      <motion.div
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", damping: 30, stiffness: 300 }}
        className="fixed top-0 right-0 z-50 h-full w-full max-w-md bg-white shadow-2xl flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <ShoppingCart size={20} className="text-smart" />
            <h2 className="font-display text-lg font-bold text-ink">Your Cart</h2>
            {cart.length > 0 && (
              <span className="rounded-full bg-smart-soft px-2 py-0.5 text-xs font-semibold text-smart-dark">
                {cart.length} items
              </span>
            )}
          </div>
          <button onClick={() => setCartOpen(false)} className="p-2 rounded-lg hover:bg-canvas transition">
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4 bg-canvas">
          <AnimatePresence mode="wait">
            {placed ? (
              <motion.div
                key="placed"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center justify-center py-16 text-center"
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", damping: 15, delay: 0.1 }}
                  className="grid h-20 w-20 place-items-center rounded-full bg-fresh-soft mb-5"
                >
                  <CheckCircle2 className="text-fresh" size={40} />
                </motion.div>
                <h3 className="font-display text-2xl font-bold text-ink">Order Placed! 🎉</h3>
                <p className="mt-2 flex items-center gap-1.5 text-ink/60">
                  <Zap size={16} className="text-fresh" /> Arriving in 10 minutes
                </p>
              </motion.div>
            ) : (
              <motion.div key="cart" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                {/* AI Summary */}
                {hasCart && <AICartSummary />}

                {/* Cart items */}
                <div className="space-y-2.5 mt-4">
                  <AnimatePresence>
                    {cart.map((item, i) => (
                      <CartItem key={item.id} item={item} index={i} onQty={setQty} onRemove={removeItem} />
                    ))}
                  </AnimatePresence>
                </div>

                {/* Suggestions */}
                {meta.suggestions?.length > 0 && (
                  <div className="mt-4">
                    <p className="text-xs font-medium text-ink/40 mb-2">You might also need</p>
                    <div className="flex flex-wrap gap-2">
                      {meta.suggestions.map((s) => (
                        <button key={s.id} onClick={() => addProduct(s)}
                          className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1.5 text-sm text-ink/70 ring-1 ring-border transition hover:ring-smart">
                          <Plus size={13} /> {s.name} · {formatINR(s.price)}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Gap Nudge */}
                <div className="mt-4">
                  <GapNudge gapAmount={gapAmount} fillers={meta.gapFillers} onAdd={addProduct} threshold={meta.threshold} subtotal={subtotal} />
                </div>

                {/* Empty state */}
                {!hasCart && (
                  <div className="flex flex-col items-center justify-center py-16 text-center">
                    <div className="text-5xl mb-4">🛒</div>
                    <p className="font-display text-lg font-semibold text-ink/60">Your cart is empty</p>
                    <p className="text-sm text-ink/40 mt-1">Describe your moment to get started</p>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Checkout footer */}
        {hasCart && !placed && (
          <div className="border-t border-border p-5 bg-white">
            <div className="flex items-end justify-between mb-4">
              <span className="text-sm text-ink/60">Subtotal</span>
              <span className="font-display text-2xl font-bold text-ink">{formatINR(subtotal)}</span>
            </div>
            <button
              onClick={() => setPlaced(true)}
              className="w-full flex items-center justify-center gap-2 rounded-full bg-amazonYellow py-4 font-display font-bold text-ink shadow-md hover:shadow-lg hover:bg-yellow-400 transition-all"
            >
              <Zap size={18} />
              Place Order · 10 min delivery
            </button>
          </div>
        )}
      </motion.div>
    </>
  );
}
