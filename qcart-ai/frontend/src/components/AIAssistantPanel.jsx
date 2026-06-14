import { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles, ShoppingCart, MessageCircle, Zap, X,
  ChevronRight, Clock, Truck, CheckCircle2, Plus,
} from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import { formatINR } from "../lib/format.js";
import { MOMENT_CONTEXTS } from "../data/momentContexts.js";

/**
 * State-driven AI Assistant Panel — slides in below hero when AI is active.
 * NOT a tab. Appears dynamically when the user types a prompt or clicks a chip.
 */
export default function AIAssistantPanel({ detectedMoment }) {
  const {
    loading, messages, cart, subtotal, hasCart,
    meta, addProduct, setCartOpen, setChatOpen, error, gapAmount,
  } = useApp();

  const [dismissed, setDismissed] = useState(false);
  const [loadingStepIdx, setLoadingStepIdx] = useState(0);

  // Reset on new prompt
  useEffect(() => {
    if (loading) { setDismissed(false); setLoadingStepIdx(0); }
  }, [loading]);

  // Cycle loading steps
  useEffect(() => {
    if (!loading) return;
    const steps = detectedMoment ? MOMENT_CONTEXTS[detectedMoment]?.loadingSteps : null;
    const count = steps?.length || 4;
    const t = setInterval(() => setLoadingStepIdx((p) => (p + 1) % count), 1200);
    return () => clearInterval(t);
  }, [loading, detectedMoment]);

  // Filter suggestions — remove items already in cart
  const cartIds = useMemo(() => new Set(cart.map((i) => i.id)), [cart]);
  const dynamicSuggestions = useMemo(() => {
    const pool = (meta.suggestions || []).filter((s) => {
      const id = typeof s === "object" ? s.id : null;
      return !id || !cartIds.has(id);
    });
    return pool.slice(0, 4);
  }, [meta.suggestions, cartIds]);

  if (dismissed) return null;
  if (!loading && !hasCart && messages.length === 0 && !error) return null;

  const momentCtx = detectedMoment ? MOMENT_CONTEXTS[detectedMoment] : null;
  const loadingSteps = momentCtx?.loadingSteps || [
    { emoji: "✨", text: "Analyzing your request" },
    { emoji: "🔍", text: "Finding best products" },
    { emoji: "🛒", text: "Building your cart" },
    { emoji: "⚡", text: "Optimizing delivery" },
  ];
  const insights = momentCtx?.resultInsights || [];
  const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
  const lastUser = [...messages].reverse().find((m) => m.role === "user");

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ type: "spring", damping: 28, stiffness: 280 }}
      className="overflow-hidden relative z-20"
    >
      <div className="max-w-3xl mx-auto px-4 sm:px-6 pt-4 pb-2">
        <div className="rounded-2xl bg-white shadow-lg overflow-hidden" style={{ border: "1px solid #E5E7EB" }}>

          {/* Header */}
          <div className="flex items-center justify-between px-5 py-3" style={{ borderBottom: "1px solid #F3F4F6" }}>
            <div className="flex items-center gap-2.5">
              <div className="grid h-7 w-7 place-items-center rounded-full shadow-sm" style={{ backgroundColor: "#FFD814" }}>
                <Zap size={12} className="text-gray-900" />
              </div>
              <span className="font-display text-sm font-bold text-gray-900">Cart Assistant</span>
              {loading && (
                <motion.span
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="rounded-full px-2 py-0.5 text-[10px] font-semibold"
                  style={{ backgroundColor: "#FFF7ED", color: "#EA580C" }}
                >
                  Building...
                </motion.span>
              )}
            </div>
            {!loading && (
              <button onClick={() => setDismissed(true)} className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors">
                <X size={14} />
              </button>
            )}
          </div>

          {/* Body */}
          <div className="px-5 py-5">
            {loading ? (
              /* Loading state */
              <div className="flex flex-col items-center py-3 gap-4">
                <motion.div animate={{ rotate: [0, 360] }} transition={{ repeat: Infinity, duration: 3, ease: "linear" }} className="relative">
                  <Sparkles size={32} style={{ color: "#F97316" }} />
                  <motion.div className="absolute inset-0 rounded-full" style={{ backgroundColor: "rgba(249,115,22,0.1)" }} animate={{ scale: [1, 1.6, 1], opacity: [0.5, 0, 0.5] }} transition={{ repeat: Infinity, duration: 2 }} />
                </motion.div>
                <div className="text-center min-h-[3.5rem]">
                  <AnimatePresence mode="wait">
                    <motion.div key={loadingStepIdx} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.3 }} className="flex flex-col items-center gap-1">
                      <p className="font-display font-semibold text-gray-900 text-base">
                        <span className="mr-1.5">{loadingSteps[loadingStepIdx]?.emoji}</span>
                        {loadingSteps[loadingStepIdx]?.text}
                      </p>
                      {lastUser && <p className="text-xs text-gray-500">"{lastUser.text}"</p>}
                    </motion.div>
                  </AnimatePresence>
                </div>
                <div className="flex gap-1.5">
                  {loadingSteps.map((_, i) => (
                    <motion.div key={i} className={`w-2 h-2 rounded-full transition-colors duration-300 ${i <= loadingStepIdx ? "bg-orange-500" : "bg-gray-200"}`} animate={i === loadingStepIdx ? { scale: [1, 1.4, 1] } : {}} transition={{ repeat: Infinity, duration: 0.8 }} />
                  ))}
                </div>
              </div>
            ) : error ? (
              <div className="text-center py-4">
                <p className="text-sm text-red-500 font-medium">{error}</p>
                <p className="text-xs text-gray-400 mt-1">Try a different prompt</p>
              </div>
            ) : (
              /* Result state */
              <div className="space-y-4">
                {/* Moment context — inline, no floating ribbon */}
                {momentCtx && (
                  <div>
                    <p className="font-display font-semibold text-gray-900 text-base">{momentCtx.icon} {detectedMoment} detected</p>
                    <p className="text-sm text-gray-500 mt-0.5">Cart optimized for {detectedMoment.toLowerCase()}</p>
                  </div>
                )}

                {/* AI reply */}
                {lastAssistant && (
                  <div className="flex items-start gap-3">
                    <div className="shrink-0 grid h-8 w-8 place-items-center rounded-full mt-0.5" style={{ backgroundColor: "#FFF7ED" }}>
                      <Sparkles size={14} style={{ color: "#F97316" }} />
                    </div>
                    <p className="text-sm text-gray-900 leading-relaxed">{lastAssistant.text}</p>
                  </div>
                )}

                {/* Status chips */}
                {insights.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {insights.map((text, i) => (
                      <motion.span key={i} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.15 + i * 0.1 }} className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium text-green-700 ring-1 ring-green-200" style={{ backgroundColor: "#F0FDF4" }}>
                        <CheckCircle2 size={12} />{text}
                      </motion.span>
                    ))}
                  </div>
                )}

                {/* Summary row */}
                {hasCart && (
                  <div className="flex items-center gap-3 flex-wrap rounded-xl bg-gray-50 p-3 text-sm">
                    <span className="flex items-center gap-1.5 font-display font-bold text-gray-900"><ShoppingCart size={14} />{cart.length} Items</span>
                    <span className="text-gray-300">|</span>
                    <span className="font-display font-bold text-gray-900">{formatINR(subtotal)}</span>
                    {meta.buildTime && (<><span className="text-gray-300">|</span><span className="flex items-center gap-1 text-xs text-gray-500"><Clock size={10} />Built in {meta.buildTime}s</span></>)}
                    <span className="text-gray-300">|</span>
                    <span className="flex items-center gap-1 text-xs text-green-600"><Truck size={10} />10 min delivery</span>
                  </div>
                )}

                {/* Free delivery */}
                {hasCart && gapAmount > 0 && (
                  <div className="rounded-xl p-3" style={{ backgroundColor: "#FFF7ED", border: "1px solid #FDBA7420" }}>
                    <div className="flex flex-wrap items-center justify-between gap-1 text-xs">
                      <span className="text-gray-800 font-medium">🚚 <span className="font-bold" style={{ color: "#EA580C" }}>{formatINR(gapAmount)}</span> away from free delivery</span>
                      <span className="text-gray-400">{formatINR(subtotal)} / {formatINR(meta.threshold || 199)}</span>
                    </div>
                    <div className="mt-2 h-1.5 rounded-full bg-gray-200 overflow-hidden">
                      <motion.div initial={{ width: 0 }} animate={{ width: `${Math.min(100, (subtotal / (meta.threshold || 199)) * 100)}%` }} transition={{ duration: 0.8 }} className="h-full rounded-full" style={{ backgroundColor: "#F97316" }} />
                    </div>
                  </div>
                )}
                {hasCart && gapAmount <= 0 && (
                  <div className="flex items-center gap-2 rounded-xl p-3 text-xs font-medium text-green-700" style={{ backgroundColor: "#F0FDF4" }}>
                    <CheckCircle2 size={14} />🎉 Free delivery unlocked!
                  </div>
                )}

                {/* Suggestions */}
                {dynamicSuggestions.length > 0 && (
                  <div className="space-y-2.5">
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">You Might Also Need</p>
                    <div className="flex flex-wrap gap-2">
                      {dynamicSuggestions.map((s, i) => {
                        const name = typeof s === "string" ? s : s.name || s.label;
                        const price = typeof s === "object" ? s.price : null;
                        return (
                          <motion.button key={name || i} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}
                            onClick={() => typeof s === "object" && s.id && addProduct({ ...s, reason: "suggested add-on" })}
                            className="flex items-center gap-2 rounded-xl bg-gray-50 px-3 py-2 text-xs text-gray-900 hover:bg-orange-50 transition-all group" style={{ border: "1px solid #E5E7EB" }}>
                            <span className="font-medium">{name}</span>
                            {price && <span className="text-gray-400">{formatINR(price)}</span>}
                            <Plus size={12} className="text-gray-400 group-hover:text-orange-500 transition-colors" />
                          </motion.button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* CTAs */}
                <div className="flex items-center gap-2 pt-1">
                  {hasCart && (
                    <button onClick={() => setCartOpen(true)} className="flex items-center gap-2 rounded-full px-5 py-2.5 text-sm font-bold shadow-sm hover:shadow transition-all active:scale-[0.97]" style={{ backgroundColor: "#FFD814", color: "#111827" }}>
                      <ShoppingCart size={14} />View Cart<ChevronRight size={14} />
                    </button>
                  )}
                  <button onClick={() => setChatOpen(true)} className="flex items-center gap-2 rounded-full bg-white px-4 py-2.5 text-sm font-medium text-gray-500 hover:text-gray-900 transition-all" style={{ border: "1px solid #E5E7EB" }}>
                    <MessageCircle size={14} />Refine
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
