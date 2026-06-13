import { useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, Plus, Check } from "lucide-react";
import { formatINR } from "../lib/format.js";

/**
 * ReadinessPanel — shows how prepared the cart is for the user's moment.
 *
 * Props:
 *   readiness: { label: string, score: number, missing: [{id, name, price, reason}] }
 *   onAdd: (item) => void
 */
export default function ReadinessPanel({ readiness, onAdd }) {
  const [addedIds, setAddedIds] = useState(new Set());

  if (!readiness) return null;

  const { label, score, missing } = readiness;

  // Success state: 100% ready
  if (score === 100) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl bg-white p-4 ring-1 ring-black/5 shadow-sm"
      >
        <div className="flex items-center gap-2 text-fresh font-medium text-sm">
          <CheckCircle2 size={18} />
          <span>100% ready ✓</span>
        </div>
      </motion.div>
    );
  }

  // Don't render if no missing items
  if (!missing?.length) return null;

  // Progress bar color based on score
  const barColor =
    score < 50
      ? "bg-red-500"
      : score < 80
      ? "bg-amber-500"
      : "bg-fresh";

  const handleAdd = (item) => {
    onAdd(item);
    setAddedIds((prev) => new Set(prev).add(item.id));
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl bg-white p-4 ring-1 ring-black/5 shadow-sm"
    >
      {/* Header: label + percentage */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-ink/80">{label}</span>
        <span className="text-sm font-semibold text-ink/60">{score}%</span>
      </div>

      {/* Progress bar */}
      <div className="mt-2.5 h-3 rounded-full bg-black/5 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className={`h-full rounded-full ${barColor}`}
        />
      </div>

      {/* Missing items */}
      <div className="mt-3 flex flex-wrap gap-2">
        {missing.map((item) => {
          const isAdded = addedIds.has(item.id);
          return (
            <button
              key={item.id}
              onClick={() => handleAdd(item)}
              disabled={isAdded}
              className={`inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs transition ring-1 ${
                isAdded
                  ? "bg-fresh-soft text-fresh ring-fresh/20"
                  : "bg-white text-ink/70 ring-black/10 hover:ring-smart active:scale-[0.98]"
              }`}
            >
              <span className="flex items-center gap-1">
                {isAdded ? <Check size={12} /> : <Plus size={12} />}
                <span className="font-medium">{item.name}</span>
                <span className="text-ink/40">·</span>
                <span>{formatINR(item.price)}</span>
              </span>
              {item.reason && !isAdded && (
                <span className="ml-1 text-[10px] text-ink/40">{item.reason}</span>
              )}
            </button>
          );
        })}
      </div>
    </motion.div>
  );
}
