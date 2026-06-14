import { motion } from "framer-motion";
import { CheckCircle2, Plus } from "lucide-react";
import { formatINR } from "../lib/format.js";

export default function ReadinessPanel({
  readiness,
  onAdd,
}) {
  if (!readiness?.essentials?.length) {
    return null;
  }

  const {
    label,
    score,
    missing,
    complete,
  } = readiness;

  // Success state
  if (complete) {
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

  const barColor =
    score < 50
      ? "bg-red-500"
      : score < 80
      ? "bg-amber-500"
      : "bg-fresh";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl bg-white p-4 ring-1 ring-black/5 shadow-sm"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-ink/80">
          {label}
        </span>

        <span className="text-sm font-semibold text-ink/60">
          {score}%
        </span>
      </div>

      {/* Progress */}
      <div className="mt-2.5 h-3 overflow-hidden rounded-full bg-black/5">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{
            duration: 0.5,
            ease: "easeOut",
          }}
          className={`h-full rounded-full ${barColor}`}
        />
      </div>

      {/* Missing essentials */}
      {missing.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {missing.map((item) => (
            <button
              key={item.id}
              onClick={() => onAdd(item)}
              className="
                inline-flex
                items-center
                gap-1.5
                rounded-xl
                px-3
                py-2
                text-xs
                bg-white
                text-ink/70
                ring-1
                ring-black/10
                hover:ring-smart
                active:scale-[0.98]
                transition
              "
            >
              <Plus size={12} />

              <span className="font-medium">
                {item.name}
              </span>

              <span className="text-ink/40">
                ·
              </span>

              <span>
                {formatINR(item.price)}
              </span>

              {item.reason && (
                <span className="ml-1 text-[10px] text-ink/40">
                  {item.reason}
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </motion.div>
  );
}