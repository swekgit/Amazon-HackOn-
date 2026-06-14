import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ShoppingCart, Zap, Plus, CheckCircle2, Sparkles, Trash2, Truck, Clock, Check } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import CartItem from "./CartItem.jsx";
import GapNudge from "./GapNudge.jsx";
import { formatINR } from "../lib/format.js";
import ReadinessPanel from "./ReadinessPanel.jsx";

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
        className="w-full max-w-xs rounded-2xl bg-white p-6 shadow-2xl ring-1 ring-line text-center"
      >
        <div className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-full bg-rose-soft">
          <Trash2 size={22} className="text-rose" />
        </div>
        <h3 className="font-display text-lg font-bold text-ink">Clear Cart?</h3>
        <p className="mt-2 text-sm text-muted leading-relaxed">
          Remove all items from your cart?
        </p>
        <div className="mt-5 flex gap-3">
          <button onClick={onCancel} className="flex-1 rounded-xl py-2.5 text-sm font-semibold text-muted bg-canvas hover:bg-line transition">
            Cancel
          </button>
          <button onClick={onConfirm} className="flex-1 rounded-xl py-2.5 text-sm font-semibold text-white bg-rose hover:bg-red-600 transition">
            Clear
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

/* ── Compact AI Stats Row ──────────────────────────────────── */
function AIStatsRow({ buildTime, itemCount }) {
  return (
    <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
      <StatPill icon={<Zap size={11} />} label={`${buildTime || "—"}s`} sub="Built" color="text-brand" bg="bg-brand-soft" />
      <StatPill icon={<Clock size={11} />} label={`${Math.max(1, itemCount * 2)} min`} sub="Saved" color="text-cta-deep" bg="bg-amber-50" />
      <StatPill icon={<Truck size={11} />} label="10 min" sub="ETA" color="text-green" bg="bg-green-soft" />
      <StatPill icon={<Sparkles size={11} />} label={`${itemCount}`} sub="Items" color="text-blue" bg="bg-blue-soft" />
    </div>
  );
}

function StatPill({ icon, label, sub, color, bg }) {
  return (
    <div className={`flex items-center gap-1.5 rounded-full ${bg} px-2.5 py-1 shrink-0`}>
      <span className={color}>{icon}</span>
      <span className="text-[11px] font-semibold text-ink">{label}</span>
      <span className="text-[9px] text-muted">{sub}</span>
    </div>
  );
}

/* ── Merged Readiness + Missing Items ──────────────────────── */
function ReadinessBlock({ readiness, onAdd }) {
  const [addedIds, setAddedIds] = useState(new Set());

  if (!readiness) return null;
  const { label, score, missing } = readiness;

  if (score === 100) {
    return (
      <div className="flex items-center gap-2 rounded-card bg-green-soft p-3 ring-1 ring-green/10">
        <CheckCircle2 size={16} className="text-green" />
        <span className="text-sm font-medium text-green">100% ready ✓</span>
      </div>
    );
  }

  if (!missing?.length) return null;

  const barColor = score < 50 ? "bg-rose" : score < 80 ? "bg-cta" : "bg-green";

  const handleAdd = (item) => {
    onAdd(item);
    setAddedIds((prev) => new Set(prev).add(item.id));
  };

  return (
    <div className="rounded-card bg-white p-4 ring-1 ring-line">
      {/* Header + progress */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-ink">{label}</span>
        <span className="text-xs font-bold text-muted">{score}%</span>
      </div>
      <div className="h-2 rounded-full bg-canvas overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className={`h-full rounded-full ${barColor}`}
        />
      </div>

      {/* Missing items */}
      <p className="text-[10px] text-muted mt-3 mb-1.5">Missing items:</p>
      <div className="flex flex-wrap gap-1.5">
        {missing.map((item) => {
          const isAdded = addedIds.has(item.id);
          return (
            <button
              key={item.id}
              onClick={() => handleAdd(item)}
              disabled={isAdded}
              className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-medium transition ring-1 ${isAdded
                ? "bg-green-soft text-green ring-green/15"
                : "bg-white text-ink ring-line hover:ring-brand/30"
                }`}
            >
              {isAdded ? <Check size={10} /> : <Plus size={10} />}
              {item.name} · {formatINR(item.price)}
            </button>
          );
        })}
      </div>
    </div>
  );
}

/* ── Cart Drawer (main) ────────────────────────────────────── */
export default function CartDrawer() {
  const { cart, subtotal, setCartOpen, setChatOpen, meta, readiness, addProduct, setQty, removeItem, gapAmount, hasCart, clearCart } = useApp();
  const [placed, setPlaced] = useState(false);
  const [showClearModal, setShowClearModal] = useState(false);
  const [showClearToast, setShowClearToast] = useState(false);

  const swipeRef = useRef(null);
  const touchStartX = useRef(0);
  const handleTouchStart = (e) => { touchStartX.current = e.touches[0].clientX; };
  const handleTouchEnd = (e) => {
    const diff = touchStartX.current - e.changedTouches[0].clientX;
    if (diff > 60 && cart.length > 0) setShowClearModal(true);
  };

  const handleClearConfirm = () => {
    setShowClearModal(false);
    clearCart();
    setShowClearToast(true);
  };

  useEffect(() => {
    if (!showClearToast) return;
    const id = setTimeout(() => setShowClearToast(false), 2500);
    return () => clearTimeout(id);
  }, [showClearToast]);

  const freeDelivery = subtotal >= (meta.threshold || 399);

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
        className="fixed top-0 right-0 z-50 h-full w-full max-w-md bg-canvas shadow-2xl flex flex-col"
      >
        {/* Header */}
        <div
          ref={swipeRef}
          onTouchStart={handleTouchStart}
          onTouchEnd={handleTouchEnd}
          className="flex items-center justify-between px-5 py-4 bg-white border-b border-line"
        >
          <div className="flex items-center gap-3">
            <ShoppingCart size={24} className="text-brand" />
            <h2 className="font-display text-3xl font-bold text-ink">Your Cart</h2>
            {cart.length > 0 && (
              <span className="rounded-full bg-brand-soft px-3 py-1.5 text-sm font-semibold text-brand-deep">
                {cart.length}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {cart.length > 0 && (
              <button
                onClick={() => setShowClearModal(true)}
                className="flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm font-semibold text-rose bg-rose-soft ring-1 ring-rose/10 hover:ring-rose/30 transition"
              >
                <Trash2 size={16} />
                <span className="hidden sm:inline">Clear</span>
              </button>
            )}
            <button onClick={() => setCartOpen(false)} className="p-2 rounded-lg hover:bg-canvas transition">
              <X size={24} />
            </button>
          </div>
        </div>

        {/* Overlays */}
        <AnimatePresence>
          {showClearModal && <ClearCartModal key="modal" onConfirm={handleClearConfirm} onCancel={() => setShowClearModal(false)} />}
        </AnimatePresence>
        <AnimatePresence>
          {showClearToast && (
            <motion.div key="toast" initial={{ opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -16 }}
              className="absolute left-1/2 top-16 z-[70] -translate-x-1/2 flex items-center gap-2 rounded-full bg-ink px-4 py-2 shadow-lg">
              <CheckCircle2 size={14} className="text-green" />
              <span className="text-xs font-medium text-white">Cart cleared</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
          <AnimatePresence mode="wait">
            {placed ? (
              <motion.div key="placed" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
                className="flex flex-col items-center justify-center py-16 text-center">
                <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", damping: 15, delay: 0.1 }}
                  className="grid h-20 w-20 place-items-center rounded-full bg-green-soft mb-5">
                  <CheckCircle2 className="text-green" size={40} />
                </motion.div>
                <h3 className="font-display text-2xl font-bold text-ink">Order Placed! 🎉</h3>
                <p className="mt-2 flex items-center gap-1.5 text-muted">
                  <Zap size={16} className="text-green" /> Arriving in 10 minutes
                </p>
              </motion.div>
            ) : (
              <motion.div key="cart" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
                {/* Compact AI Stats */}
                {hasCart && <AIStatsRow buildTime={meta.buildTime} itemCount={cart.length} />}

                {/* Readiness Score */}
                {hasCart && (
                  <div className="mt-3">
                    <ReadinessPanel readiness={readiness} onAdd={addProduct} />
                  </div>
                )}

                {/* Cart Items */}
                <div className="space-y-2">
                  <AnimatePresence>
                    {cart.map((item, i) => (
                      <CartItem key={item.id} item={item} index={i} onQty={setQty} onRemove={removeItem} />
                    ))}
                  </AnimatePresence>
                </div>

                {/* Suggestions */}
                {meta.suggestions?.length > 0 && (
                  <div>
                    <p className="text-[10px] font-semibold text-muted mb-1.5 uppercase tracking-wider">You might need</p>
                    <div className="flex flex-wrap gap-1.5">
                      {meta.suggestions.map((s) => (
                        <button key={s.id} onClick={() => addProduct(s)}
                          className="inline-flex items-center gap-1 rounded-full bg-white px-2.5 py-1.5 text-[11px] text-ink ring-1 ring-line hover:ring-brand/30 transition">
                          <Plus size={11} /> {s.name} · {formatINR(s.price)}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Gap Nudge */}
                <GapNudge gapAmount={gapAmount} fillers={meta.gapFillers} onAdd={addProduct} threshold={meta.threshold} subtotal={subtotal} />

                {/* Empty state */}
                {!hasCart && (
                  <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
                    className="flex flex-col items-center justify-center py-16 text-center">
                    <div className="text-5xl mb-4">🛒</div>
                    <p className="font-display text-lg font-semibold text-ink/60">Your cart is empty</p>
                    <p className="text-sm text-muted mt-1 mb-6">Describe a moment and we'll build it</p>
                    <button onClick={() => { setCartOpen(false); setChatOpen(true); }}
                      className="inline-flex items-center gap-2 rounded-full bg-brand px-5 py-2.5 text-sm font-bold text-white shadow-md hover:bg-brand-deep transition">
                      <Sparkles size={15} /> Try a Moment
                    </button>
                  </motion.div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Checkout Footer — sticky at bottom */}
        {hasCart && !placed && (
          <div className="border-t border-line p-4 bg-white">
            {/* Subtotal breakdown */}
            <div className="space-y-1.5 mb-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted">Items ({cart.length})</span>
                <span className="text-ink font-medium">{formatINR(subtotal)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted">Delivery</span>
                <span className={freeDelivery ? "text-green font-medium" : "text-ink font-medium"}>
                  {freeDelivery ? "FREE" : formatINR(29)}
                </span>
              </div>
              <div className="border-t border-line pt-1.5 flex justify-between">
                <span className="text-sm font-semibold text-ink">Total</span>
                <span className="font-display text-xl font-bold text-ink">
                  {formatINR(subtotal + (freeDelivery ? 0 : 29))}
                </span>
              </div>
            </div>

            {/* CTA — Yellow primary */}
            <button
              onClick={() => setPlaced(true)}
              className="w-full flex items-center justify-center gap-2 rounded-full bg-amazonYellow py-3.5 font-display font-bold text-ink shadow-md hover:shadow-lg hover:bg-yellow-400 transition-all"
            >
              <Zap size={16} />
              Place Order · 10 min delivery
            </button>
          </div>
        )}
      </motion.div>
    </>
  );
}
