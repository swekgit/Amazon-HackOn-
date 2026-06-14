import { motion } from "framer-motion";
import { Truck, Plus, Check } from "lucide-react";
import { formatINR } from "../lib/format.js";
import { useState } from "react";

export default function GapNudge({ gapAmount, fillers, onAdd, threshold, subtotal }) {
  const [addedIds, setAddedIds] = useState(new Set());

  if (!gapAmount || gapAmount <= 0) return null;

  const progress = Math.min((subtotal / (threshold || 199)) * 100, 100);

  const handleAdd = (f) => {
    onAdd(f);
    setAddedIds((prev) => new Set(prev).add(f.id));
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl bg-fresh-soft/80 p-4 ring-1 ring-fresh/15"
    >
      <p className="flex items-center gap-2 font-medium text-fresh text-sm">
        <Truck size={16} /> {formatINR(gapAmount)} away from free delivery!
      </p>

      {/* Progress bar */}
      <div className="mt-3 relative">
        <div className="h-2 rounded-full bg-white">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="h-full rounded-full bg-gradient-to-r from-fresh to-emerald-400"
          />
        </div>
        <div className="flex justify-between mt-1 text-[10px] text-ink/40">
          <span>{formatINR(subtotal)}</span>
          <span>{formatINR(threshold || 199)}</span>
        </div>
      </div>

      {/* Fillers */}
      {fillers?.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {fillers.map((f) => {
            const isAdded = addedIds.has(f.id);
            return (
              <button
                key={f.id}
                onClick={() => handleAdd(f)}
                disabled={isAdded}
                className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition ring-1 ${isAdded
                  ? "bg-fresh-soft text-fresh ring-fresh/20"
                  : "bg-white text-ink/70 ring-black/10 hover:ring-fresh"
                  }`}
              >
                {isAdded ? <Check size={12} /> : <Plus size={12} />}
                {f.name} · {formatINR(f.price)}
              </button>
            );
          })}
        </div>
      )}
    </motion.div>
  );
}
