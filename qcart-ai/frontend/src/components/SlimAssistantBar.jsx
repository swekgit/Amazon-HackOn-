import { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, ShoppingCart, Zap, ChevronRight, Loader2 } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import { formatINR } from "../lib/format.js";

/**
 * SlimAssistantBar — compact inline status below the search bar.
 * Shows: loading animation while AI builds the cart, then a one-line summary.
 * Designed to be minimal (single row, no full panel).
 */

const LOADING_STEPS = [
  { emoji: "✨", text: "Analyzing your moment" },
  { emoji: "🔍", text: "Finding best products" },
  { emoji: "🛒", text: "Building your cart" },
  { emoji: "⚡", text: "Optimizing delivery" },
];

export default function SlimAssistantBar() {
  const { loading, hasCart, cart, subtotal, meta, setCartOpen, messages, error } = useApp();
  const [stepIdx, setStepIdx] = useState(0);
  const [visible, setVisible] = useState(false);

  // Show bar when loading starts or cart exists
  useEffect(() => {
    if (loading || hasCart) setVisible(true);
  }, [loading, hasCart]);

  // Cycle loading steps
  useEffect(() => {
    if (!loading) return;
    setStepIdx(0);
    const t = setInterval(() => setStepIdx((p) => (p + 1) % LOADING_STEPS.length), 1400);
    return () => clearInterval(t);
  }, [loading]);

  // Get last AI message for summary
  const lastReply = useMemo(
    () => [...messages].reverse().find((m) => m.role === "assistant"),
    [messages]
  );

  if (!visible) return null;
  if (!loading && !hasCart && !error) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, height: 0 }}
        animate={{ opacity: 1, height: "auto" }}
        exit={{ opacity: 0, height: 0 }}
        transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
        className="overflow-hidden"
      >
        <div className="max-w-4xl mx-auto px-4 sm:px-6 pt-3 pb-1">
          <motion.div
            layout
            className="rounded-2xl shadow-sm overflow-hidden"
            style={{ border: "1px solid #E5E7EB", backgroundColor: "#FFFBF5" }}
          >
            {loading ? (
              /* ── Loading state ─────────────────────────────── */
              <div className="flex items-center gap-3 px-4 py-3">
                <motion.div
                  animate={{ rotate: [0, 360] }}
                  transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                  className="shrink-0"
                >
                  <Loader2 size={18} style={{ color: "#F97316" }} />
                </motion.div>
                <div className="min-w-0 flex-1">
                  <AnimatePresence mode="wait">
                    <motion.p
                      key={stepIdx}
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -6 }}
                      transition={{ duration: 0.25 }}
                      className="text-sm font-semibold text-gray-800 truncate"
                    >
                      <span className="mr-1.5">{LOADING_STEPS[stepIdx].emoji}</span>
                      {LOADING_STEPS[stepIdx].text}
                    </motion.p>
                  </AnimatePresence>
                </div>
                {/* Step dots */}
                <div className="flex gap-1 shrink-0">
                  {LOADING_STEPS.map((_, i) => (
                    <div
                      key={i}
                      className={`w-1.5 h-1.5 rounded-full transition-colors duration-300 ${
                        i <= stepIdx ? "bg-orange-400" : "bg-gray-200"
                      }`}
                    />
                  ))}
                </div>
              </div>
            ) : error ? (
              /* ── Error state ──────────────────────────────── */
              <div className="flex items-center gap-2 px-4 py-3">
                <span className="text-sm text-red-500 font-medium">{error}</span>
              </div>
            ) : hasCart ? (
              /* ── Result state — compact summary ───────────── */
              <div className="flex items-center gap-3 px-4 py-2.5">
                <div
                  className="shrink-0 grid h-7 w-7 place-items-center rounded-full"
                  style={{ backgroundColor: "#FFD814" }}
                >
                  <Zap size={12} className="text-gray-900" />
                </div>

                {/* Summary text */}
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-gray-800 truncate">
                    <span className="font-bold">{cart.length} items</span>
                    <span className="text-gray-400 mx-1.5">·</span>
                    <span className="font-bold">{formatINR(subtotal)}</span>
                    {meta.buildTime && (
                      <>
                        <span className="text-gray-400 mx-1.5">·</span>
                        <span className="text-gray-500 text-xs">Built in {meta.buildTime}s</span>
                      </>
                    )}
                  </p>
                </div>

                {/* View Cart CTA */}
                <button
                  onClick={() => setCartOpen(true)}
                  className="shrink-0 inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 text-xs font-bold shadow-sm hover:shadow transition-all active:scale-[0.97]"
                  style={{ backgroundColor: "#FFD814", color: "#111827" }}
                >
                  <ShoppingCart size={12} />
                  View Cart
                  <ChevronRight size={12} />
                </button>
              </div>
            ) : null}
          </motion.div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
