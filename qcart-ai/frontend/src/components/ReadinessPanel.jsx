import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, Plus } from "lucide-react";
import { formatINR } from "../lib/format.js";

/**
 * Minimal Readiness Panel — Task 1
 * Shows: animated progress bar, moment-aware phrase, missing-items line.
 * Bands: 0-40 | 41-70 | 71-99 | 100 — same score buckets as before.
 */
export default function ReadinessPanel({ readiness, onAdd }) {
  const [addedIds, setAddedIds] = useState(new Set());

  if (!readiness?.essentials?.length) return null;

  const { phrase, score, missing, complete } = readiness;

  // Color bands: <40 red, 41-70 amber, 71-99 green, 100 green
  const barColor = complete
    ? "bg-green-500"
    : score >= 71
    ? "bg-green-400"
    : score >= 41
    ? "bg-amber-400"
    : "bg-red-500";

  const bandTextColor = complete
    ? "text-green-600"
    : score >= 71
    ? "text-green-600"
    : score >= 41
    ? "text-amber-600"
    : "text-red-600";

  const handleAdd = (item) => {
    onAdd(item);
    setAddedIds((prev) => new Set(prev).add(item.id));
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl bg-white p-3 ring-1 ring-black/5 shadow-sm"
    >
      {/* Band label + score */}
      <div className="flex items-center justify-between mb-2">
        <span className={`text-xs font-semibold ${bandTextColor}`}>
          {complete && <CheckCircle2 size={12} className="inline mr-1 mb-0.5" />}
          {phrase}
        </span>
        <span className={`text-xs font-semibold ${bandTextColor}`}>{score}%</span>
      </div>

      {/* Animated progress bar — amber → green */}
      <div className="h-1.5 overflow-hidden rounded-full bg-black/5">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          className={`h-full rounded-full transition-colors duration-700 ${barColor}`}
        />
      </div>

      {/* "You're missing" text — only when incomplete */}
      <AnimatePresence>
        {!complete && missing?.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-2.5 overflow-hidden"
          >
            <p className={`text-[11px] font-medium mb-1.5 ${bandTextColor}`}>
              You're missing:{" "}
              <span className="text-ink/70">
                {missing.map((m) => m.name).join(", ")}
              </span>
            </p>
            <div className="flex flex-wrap gap-1.5">
              {missing.slice(0, 4).map((item) => {
                const added = addedIds.has(item.id);
                return (
                  <button
                    key={item.id}
                    onClick={() => handleAdd(item)}
                    disabled={added}
                    className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-medium ring-1 transition ${
                      added
                        ? "bg-green-soft text-green ring-green/15"
                        : "bg-white text-ink/70 ring-black/10 hover:ring-brand/40"
                    }`}
                  >
                    {added ? <CheckCircle2 size={9} /> : <Plus size={9} />}
                    {item.name} · {formatINR(item.price)}
                  </button>
                );
              })}
              {missing.length > 4 && (
                <span className="inline-flex items-center text-[10px] text-ink/40 px-1">
                  +{missing.length - 4} more
                </span>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 100% celebration */}
      <AnimatePresence>
        {complete && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            className="mt-2 text-center text-xs text-green-600 font-medium"
          >
            🎉 {phrase}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
