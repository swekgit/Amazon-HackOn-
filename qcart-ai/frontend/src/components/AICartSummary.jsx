import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Sparkles, Zap, Clock, MousePointer, Truck } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import { savings, formatDeliveryTime } from "../lib/format.js";

function AnimatedNumber({ value, suffix = "" }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    if (!value && value !== 0) return;
    const end = typeof value === "string" ? parseFloat(value) : value;
    if (isNaN(end)) return;
    const duration = 1000;
    const startTime = performance.now();
    let raf;
    function step(now) {
      const progress = Math.min((now - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(suffix === "s" ? (eased * end).toFixed(1) : Math.round(eased * end));
      if (progress < 1) raf = requestAnimationFrame(step);
    }
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [value, suffix]);
  return <span className="font-display font-bold text-ink">{display}{suffix}</span>;
}

export default function AICartSummary() {
  const { cart, meta, messages } = useApp();
  const { minutes, taps } = savings(cart);
  const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl bg-gradient-to-r from-smart-soft/80 to-amber-50/60 p-4 ring-1 ring-smart/15"
    >
      {/* AI label */}
      <div className="flex items-center gap-1.5 mb-2">
        <Sparkles size={14} className="text-smart" />
        <span className="text-xs font-semibold text-smart-dark uppercase tracking-wider">AI-Curated Cart</span>
      </div>

      {/* Reply */}
      {lastAssistant && (
        <p className="text-sm text-ink/70 mb-3 leading-relaxed">{lastAssistant.text}</p>
      )}

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-2">
        <div className="rounded-lg bg-white p-2.5 text-center ring-1 ring-border">
          <Zap size={14} className="mx-auto text-smart mb-1" />
          <AnimatedNumber value={meta.buildTime} suffix="s" />
          <p className="text-[10px] text-ink/40 mt-0.5">Built in</p>
        </div>
        <div className="rounded-lg bg-white p-2.5 text-center ring-1 ring-border">
          <Clock size={14} className="mx-auto text-amber-500 mb-1" />
          <AnimatedNumber value={minutes} suffix=" min" />
          <p className="text-[10px] text-ink/40 mt-0.5">Saved</p>
        </div>
        <div className="rounded-lg bg-white p-2.5 text-center ring-1 ring-border">
          <MousePointer size={14} className="mx-auto text-fresh mb-1" />
          <AnimatedNumber value={taps} />
          <p className="text-[10px] text-ink/40 mt-0.5">Taps saved</p>
        </div>
      </div>

      {/* Delivery estimate */}
      <div className="mt-3 flex items-center gap-1.5 text-xs text-ink/50">
        <Truck size={12} />
        <span>Delivering by {formatDeliveryTime()}</span>
      </div>
    </motion.div>
  );
}
