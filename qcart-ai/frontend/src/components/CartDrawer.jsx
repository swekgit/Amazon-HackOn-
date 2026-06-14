import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ShoppingCart, Zap, Plus, CheckCircle2, Sparkles, Trash2 } from "lucide-react";



import { useApp } from "../state/AppContext.jsx";
import CartItem from "./CartItem.jsx";
import AICartSummary from "./AICartSummary.jsx";
import GapNudge from "./GapNudge.jsx";
import ReadinessPanel from "./ReadinessPanel.jsx";
import { formatINR } from "../lib/format.js";

/* ── Clear-Cart Confirmation Modal ─────────────────────────── */
function ClearCartModal({ onConfirm, onCancel }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute inset-0 z-[60] flex items-center justify-center bg-black/30 backdrop-blur-[6px] px-6"
      onClick={onCancel}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.92, y: 12 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.92, y: 12 }}
        transition={{ type: "spring", damping: 26, stiffness: 340 }}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-xs rounded-2xl bg-white p-6 shadow-2xl ring-1 ring-border text-center"
      >
        {/* Icon */}
        <div className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-full bg-red-50">
          <Trash2 size={22} className="text-red-500" />
        </div>

        <h3 className="font-display text-lg font-bold text-ink">Clear Cart?</h3>
        <p className="mt-2 text-sm text-ink/60 leading-relaxed">
          Are you sure you want to remove all items from your cart?
        </p>

        {/* Buttons */}
        <div className="mt-6 flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 rounded-xl py-2.5 text-sm font-semibold text-ink/70 bg-canvas hover:bg-gray-200 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 rounded-xl py-2.5 text-sm font-semibold text-white bg-red-500 hover:bg-red-600 shadow-sm hover:shadow transition-all"
          >
            Clear Cart
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

/* ── Success Toast ─────────────────────────────────────────── */
function ClearSuccessToast() {
  return (
    <motion.div
      initial={{ opacity: 0, y: -16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -16 }}
      transition={{ type: "spring", damping: 22, stiffness: 300 }}
      className="absolute left-1/2 top-16 z-[70] -translate-x-1/2 flex items-center gap-2 rounded-full bg-ink px-4 py-2 shadow-lg"
    >
      <CheckCircle2 size={16} className="text-fresh" />
      <span className="text-sm font-medium text-white whitespace-nowrap">Cart Cleared ✓</span>
    </motion.div>
  );
}

/* ── Cart Drawer (main) ────────────────────────────────────── */
export default function CartDrawer() {
  const { cart, subtotal, setCartOpen, setChatOpen, meta,readiness, addProduct, setQty, removeItem, gapAmount, hasCart, clearCart } = useApp();
  const [placed, setPlaced] = useState(false);
  const [showClearModal, setShowClearModal] = useState(false);
  const [showClearToast, setShowClearToast] = useState(false);

  /* Swipe-left detection on the header for mobile */
  const swipeRef = useRef(null);
  const touchStartX = useRef(0);

  const handleTouchStart = (e) => {
    touchStartX.current = e.touches[0].clientX;
  };
  const handleTouchEnd = (e) => {
    const diff = touchStartX.current - e.changedTouches[0].clientX;
    if (diff > 60 && cart.length > 0) {
      setShowClearModal(true);
    }
  };

  /* Handle confirmed clear */
  const handleClearConfirm = () => {
    setShowClearModal(false);
    clearCart();
    setShowClearToast(true);
  };

  /* Auto-dismiss the success toast */
  useEffect(() => {
    if (!showClearToast) return;
    const id = setTimeout(() => setShowClearToast(false), 2500);
    return () => clearTimeout(id);
  }, [showClearToast]);

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
        {/* Header — swipeable area */}
        <div
          ref={swipeRef}
          onTouchStart={handleTouchStart}
          onTouchEnd={handleTouchEnd}
          className="flex items-center justify-between px-5 py-4 border-b border-border"
        >
          <div className="flex items-center gap-2">
            <ShoppingCart size={20} className="text-smart" />
            <h2 className="font-display text-lg font-bold text-ink">Your Cart</h2>
            {cart.length > 0 && (
              <span className="rounded-full bg-smart-soft px-2 py-0.5 text-xs font-semibold text-smart-dark">
                {cart.length} items
              </span>
            )}
          </div>
          <div className="flex items-center gap-1">
            {/* Clear Cart action — only when items exist */}
            {cart.length > 0 && (
              <button
                onClick={() => setShowClearModal(true)}
                className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-red-500 bg-red-50 ring-1 ring-red-100 hover:bg-red-100 hover:ring-red-200 transition-all"
                title="Clear Cart"
              >
                <Trash2 size={16} />
                <span className="hidden sm:inline">Clear</span>
              </button>
            )}
            <button onClick={() => setCartOpen(false)} className="p-2 rounded-lg hover:bg-canvas transition">
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Overlays (inside drawer so they are scoped) */}
        <AnimatePresence>
          {showClearModal && (
            <ClearCartModal
              key="clear-modal"
              onConfirm={handleClearConfirm}
              onCancel={() => setShowClearModal(false)}
            />
          )}
        </AnimatePresence>

        <AnimatePresence>
          {showClearToast && <ClearSuccessToast key="clear-toast" />}
        </AnimatePresence>

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

                {/* Readiness Score */}
                {hasCart && (
                  <div className="mt-3">
                    <ReadinessPanel readiness={readiness} onAdd={addProduct} />
                  </div>
                )}

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

                {/* Empty state — premium version */}
                {!hasCart && (
                  <motion.div
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="flex flex-col items-center justify-center py-16 text-center"
                  >
                    <div className="text-5xl mb-4">🛒</div>
                    <p className="font-display text-lg font-semibold text-ink/60">Your cart is empty</p>
                    <p className="text-sm text-ink/40 mt-1 mb-6">Describe a moment and we'll build it for you</p>
                    <button
                      onClick={() => { setCartOpen(false); setChatOpen(true); }}
                      className="inline-flex items-center gap-2 rounded-full bg-smart px-5 py-2.5 text-sm font-bold text-white shadow-md hover:shadow-lg hover:bg-smart-dark transition-all"
                    >
                      <Sparkles size={15} />
                      Try a Moment
                    </button>
                  </motion.div>
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
