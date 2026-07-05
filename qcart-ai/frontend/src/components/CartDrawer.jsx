import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ShoppingCart, Zap, Plus, CheckCircle2, Sparkles, Trash2, Truck, Clock, Check, CreditCard, Tag } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import CartItem from "./CartItem.jsx";
import GapNudge from "./GapNudge.jsx";
import { formatINR } from "../lib/format.js";
import ReadinessPanel from "./ReadinessPanel.jsx";
import RecipeCard from "./RecipeCard.jsx";

/* ── Payment Offers + Saved Payments (Task 4) ──────────────── */
function PaymentExtras({ paymentOffers, savedPayments, onAdd, selectedPayment, onSelectPayment }) {
  if (!paymentOffers?.length && !savedPayments?.length) return null;

  // Find the best eligible offer to identify the recommended payment method
  const bestOffer = paymentOffers?.find((o) => o.eligible && o.savings > 0);
  const recommendedOfferId = bestOffer?.id || "";

  return (
    <div className="space-y-3">
      {paymentOffers?.length > 0 && (
        <div>
          <p className="text-[10px] font-semibold text-muted uppercase tracking-wider mb-1.5 flex items-center gap-1">
            <Tag size={10} /> Offers
          </p>
          <div className="space-y-1.5">
            {paymentOffers.slice(0, 2).map((offer) => (
              <div key={offer.id || offer.title} className="rounded-xl bg-fresh-soft/60 px-3 py-2 ring-1 ring-fresh/10 space-y-1.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-medium text-fresh">{offer.title}</span>
                  {offer.savings > 0 && (
                    <span className="text-[10px] font-bold text-fresh shrink-0">Save {formatINR(offer.savings)}</span>
                  )}
                </div>
                {offer.detail && (
                  <p className="text-[10px] text-muted leading-snug">{offer.detail}</p>
                )}
                {offer.suggested_items?.length > 0 && onAdd && (
                  <div className="flex flex-wrap gap-1.5">
                    {offer.suggested_items.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => onAdd({ ...item, reason: "unlock offer" })}
                        className="inline-flex items-center gap-1 rounded-full bg-white px-2 py-0.5 text-[10px] font-medium text-ink ring-1 ring-line hover:ring-brand/30 transition"
                      >
                        <Plus size={9} />
                        {item.name} · {formatINR(item.price)}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      {savedPayments?.length > 0 && (
        <div>
          <p className="text-[10px] font-semibold text-muted uppercase tracking-wider mb-1.5 flex items-center gap-1">
            <CreditCard size={10} /> Pay with
          </p>
          <div className="flex flex-wrap gap-2">
            {savedPayments.slice(0, 3).map((pm, i) => {
              const selected = selectedPayment?.label === pm.label;
              const isRecommended = recommendedOfferId && pm.offer_id === recommendedOfferId;
              return (
                <button
                  key={pm.id || pm.label || i}
                  type="button"
                  onClick={() => onSelectPayment?.(pm)}
                  className={`relative inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition ${
                    selected
                      ? "bg-brand-soft text-brand-deep ring-2 ring-brand"
                      : "bg-white text-ink ring-1 ring-line hover:ring-brand/30"
                  }`}
                >
                  {isRecommended && (
                    <span className="absolute -top-2 left-1/2 -translate-x-1/2 rounded-full bg-fresh px-1.5 py-0.5 text-[8px] font-bold text-white uppercase leading-none whitespace-nowrap">
                      Recommended
                    </span>
                  )}
                  {selected && <Check size={12} />}
                  <span>{pm.icon || "💳"}</span>
                  {pm.label}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

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

/* ── AI Stats Row — prominent grid ─────────────────────────── */
function AIStatsRow({ buildTime, itemCount }) {
  return (
    <div className="grid grid-cols-4 gap-2">
      <StatPill icon={<Zap size={16} />} label={`${buildTime || "—"}s`} sub="Built" color="text-brand" bg="bg-brand-soft" />
      <StatPill icon={<Clock size={16} />} label={`${Math.max(1, itemCount * 2)} min`} sub="Saved" color="text-cta-deep" bg="bg-amber-50" />
      <StatPill icon={<Truck size={16} />} label="10 min" sub="ETA" color="text-green" bg="bg-green-soft" />
      <StatPill icon={<Sparkles size={16} />} label={`${itemCount}`} sub="Items" color="text-blue" bg="bg-blue-soft" />
    </div>
  );
}

function StatPill({ icon, label, sub, color, bg }) {
  return (
    <div className={`flex flex-col items-center gap-0.5 rounded-xl ${bg} py-3 px-1`}>
      <span className={color}>{icon}</span>
      <span className="text-sm font-bold text-ink leading-tight">{label}</span>
      <span className="text-[9px] font-medium text-muted uppercase tracking-wide">{sub}</span>
    </div>
  );
}

/* ── Merged Readiness + Missing Items ──────────────────────── */
function ReadinessBlock({ readiness, onAdd }) {
  const [addedIds, setAddedIds] = useState(new Set());

  if (!readiness) return null;
  const { label, phrase, score, missing } = readiness;

  if (score === 100) {
    return (
      <div className="flex items-center gap-2 rounded-card bg-green-soft p-3 ring-1 ring-green/10">
        <CheckCircle2 size={16} className="text-green" />
        <span className="text-sm font-medium text-green">100% ready ✓</span>
      </div>
    );
  }

  if (!missing?.length) return null;

  const barColor = score < 40 ? "bg-red-500" : score < 71 ? "bg-amber-400" : "bg-green";
  const bandTextColor = score < 40 ? "text-red-600" : score < 71 ? "text-amber-600" : "text-green-600";
  const bandLabel = score < 40 ? "Just started" : score < 71 ? "Almost there" : "Good to go";

  const handleAdd = (item) => {
    onAdd(item);
    setAddedIds((prev) => new Set(prev).add(item.id));
  };

  const bandBg = score < 40 ? "bg-red-50" : score < 71 ? "bg-amber-50" : "bg-green-50";
  const ringColor = score < 40 ? "ring-red-200" : score < 71 ? "ring-amber-200" : "ring-green-200";

  return (
    <div className={`rounded-2xl ${bandBg} p-4 ring-1 ${ringColor}`}>
      {/* Phrase heading — kept as-is, styled attractively */}
      <p className={`text-sm font-bold capitalize ${bandTextColor} leading-snug`}>
        {phrase || `${bandLabel} — ${label}`}
      </p>

      {/* Score + progress bar */}
      <div className="flex items-center gap-3 mt-2.5">
        <div className="flex-1 h-2.5 rounded-full bg-white/70 overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${score}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className={`h-full rounded-full ${barColor}`}
          />
        </div>
        <span className={`text-sm font-bold ${bandTextColor} tabular-nums`}>{score}%</span>
      </div>

      {/* Missing item chips — no redundant text */}
      <div className="flex flex-wrap gap-1.5 mt-3">
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
  const { cart, subtotal, setCartOpen, setChatOpen, meta, readiness, paymentOffers, addProduct, setQty, removeItem, gapAmount, hasCart, clearCart } = useApp();
  const [placed, setPlaced] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState(null);
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
    setSelectedPayment(null);
    setShowClearToast(true);
  };

  useEffect(() => {
    if (!showClearToast) return;
    const id = setTimeout(() => setShowClearToast(false), 2500);
    return () => clearTimeout(id);
  }, [showClearToast]);

  const freeDelivery = subtotal >= (meta.threshold || 399);

  // Only show suggestions not already in the cart; slice keeps a backfill pool
  // so adding one reveals the next relevant suggestion in its place.
  const visibleSuggestions = (meta.suggestions || [])
    .filter((s) => !cart.some((c) => c.id === s.id))
    .slice(0, 3);

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

                {/* Readiness Score — shown only for intent-generated carts */}
                {hasCart && readiness && (
                  <div className="mt-3">
                    <ReadinessPanel readiness={readiness} onAdd={addProduct} />
                  </div>
                )}

                {/* Suggested for You — shown when readiness is hidden */}
                {hasCart && !readiness && visibleSuggestions.length > 0 && (
                  <div className="mt-3 rounded-xl bg-white p-3 ring-1 ring-black/5 shadow-sm">
                    <p className="text-xs font-semibold text-muted uppercase tracking-wider mb-2 flex items-center gap-1">
                      <Sparkles size={11} /> Suggested for you
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {visibleSuggestions.map((item) => (
                        <button
                          key={item.id}
                          onClick={() => addProduct({ ...item, reason: item.reason || "suggested" })}
                          className="inline-flex items-center gap-1 rounded-full bg-white px-2.5 py-1 text-[10px] font-medium text-ink/70 ring-1 ring-black/10 hover:ring-brand/40 transition"
                        >
                          <Plus size={9} />
                          {item.name} · {formatINR(item.price)}
                        </button>
                      ))}
                    </div>
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



                {/* Gap Nudge */}
                <GapNudge gapAmount={gapAmount} fillers={meta.gapFillers} onAdd={addProduct} threshold={meta.threshold} subtotal={subtotal} />

                {/* Recipe Card */}
                {meta.recipe && (
                  <RecipeCard recipe={meta.recipe} />
                )}

                {/* Payment Offers + Saved Payments */}
                {hasCart && (
                  <PaymentExtras
                    paymentOffers={paymentOffers}
                    savedPayments={meta.savedPayments}
                    onAdd={addProduct}
                    selectedPayment={selectedPayment}
                    onSelectPayment={setSelectedPayment}
                  />
                )}

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
              {(() => {
                const selectedOfferId = selectedPayment?.offer_id;
                const matchedOffer = selectedOfferId
                  ? paymentOffers.find((o) => o.id === selectedOfferId && o.eligible && o.savings > 0)
                  : null;
                const discount = matchedOffer?.savings || 0;
                const total = subtotal + (freeDelivery ? 0 : 29) - discount;
                return (
                  <>
                    {discount > 0 && (
                      <div className="flex justify-between text-sm">
                        <span className="text-fresh font-medium">{matchedOffer.title}</span>
                        <span className="text-fresh font-medium">-{formatINR(discount)}</span>
                      </div>
                    )}
                    <div className="border-t border-line pt-1.5 flex justify-between">
                      <span className="text-sm font-semibold text-ink">Total</span>
                      <div className="text-right">
                        {discount > 0 && (
                          <span className="text-xs text-muted line-through mr-2">
                            {formatINR(subtotal + (freeDelivery ? 0 : 29))}
                          </span>
                        )}
                        <span className="font-display text-xl font-bold text-ink">
                          {formatINR(total)}
                        </span>
                      </div>
                    </div>
                  </>
                );
              })()}
            </div>

            {/* CTA — Yellow primary */}
            <button
              onClick={() => {
                setPlaced(true);
                clearCart();
                setSelectedPayment(null);
              }}
              className="w-full flex items-center justify-center gap-2 rounded-full bg-amazonYellow py-3.5 font-display font-bold text-ink shadow-md hover:shadow-lg hover:bg-yellow-400 transition-all"
            >
              <Zap size={16} />
              {selectedPayment
                ? `Place Order · ${selectedPayment.label}`
                : "Place Order · 10 min delivery"}
            </button>
          </div>
        )}
      </motion.div>
    </>
  );
}
