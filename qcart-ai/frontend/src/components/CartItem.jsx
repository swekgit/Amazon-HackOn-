import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Minus, Plus, X, Zap, TrendingDown } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import { formatINR } from "../lib/format.js";

const S3 = "https://qcart-ai-apoorva-images.s3.ap-south-1.amazonaws.com/products/";

function ProductImage({ product }) {
  const [errored, setErrored] = useState(false);
  const src = errored
    ? "/placeholder.jpg"
    : `${S3}${product.id}.jpg`;
  return (
    <img
      src={src}
      alt={product.name}
      onError={() => setErrored(true)}
      className="h-12 w-12 rounded-xl object-cover bg-gray-100 shrink-0"
    />
  );
}

/**
 * Compact left-side Alternatives panel — Task 3.
 * Renders ONLY when item.alternatives exists.
 * Each alt shows: brand, name, price, tag (cheaper/faster), swap button.
 */
function AlternativesPanel({ item, onClose }) {
  const { swapItem } = useApp();

  const alts = item.alternatives;
  if (!alts) return null;

  // Normalise: support array or {cheaper, faster, premium} object shapes
  const altList = Array.isArray(alts)
    ? alts
    : [
        alts.cheaper && { ...alts.cheaper, _tag: "cheaper" },
        alts.faster && { ...alts.faster, _tag: "faster" },
        alts.premium && { ...alts.premium, _tag: "premium" },
      ].filter(Boolean);

  if (!altList.length) return null;

  const tagLabel = (alt) => {
    const t = alt._tag || alt.reason || "";
    if (t === "cheaper" || t.includes("cheap") || t.includes("save")) return "Cheaper";
    if (t === "faster" || t.includes("fast")) return "Faster delivery";
    return null;
  };

  const tagStyle = (alt) => {
    const t = alt._tag || alt.reason || "";
    if (t.includes("cheap") || t.includes("save") || t === "cheaper")
      return "bg-green-soft text-green ring-green/15";
    if (t.includes("fast") || t === "faster")
      return "bg-blue-soft text-blue ring-blue/15";
    return "bg-brand-soft text-brand ring-brand/15";
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -10 }}
      transition={{ duration: 0.2 }}
      className="absolute left-0 top-0 bottom-0 z-10 w-44 bg-white rounded-l-card border-r border-line p-2 flex flex-col gap-1.5 shadow-md overflow-y-auto"
    >
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[11px] font-extrabold text-ink uppercase tracking-wider">Alternatives</span>
        <button onClick={onClose} className="grid h-6 w-6 place-items-center rounded-full bg-ink/5 text-ink/60 hover:bg-ink/10 hover:text-ink transition">
          <X size={14} />
        </button>
      </div>
      {altList.map((alt, i) => {
        const tag = tagLabel(alt);
        return (
          <div key={alt.id || i} className="rounded-lg bg-canvas p-2 flex flex-col gap-1 ring-1 ring-line">
            {alt.brand && (
              <span className="text-[9px] font-semibold text-ink/40 uppercase tracking-wide truncate">
                {alt.brand}
              </span>
            )}
            <p className="text-[11px] font-medium text-ink leading-tight line-clamp-2">{alt.name}</p>
            <p className="font-display text-xs font-bold text-ink">{formatINR(alt.price)}</p>
            {tag && (
              <span className={`self-start inline-flex items-center gap-0.5 rounded-full px-1.5 py-0.5 text-[9px] font-semibold ring-1 ${tagStyle(alt)}`}>
                {tag === "Cheaper" ? <TrendingDown size={8} /> : <Zap size={8} />}
                {tag}
              </span>
            )}
            <button
              onClick={() =>
                swapItem(item.id, {
                  ...alt,
                  category: item.category,
                  reason: tag || "alternative",
                })
              }
              className="mt-0.5 w-full rounded-md bg-brand py-1 text-[10px] font-semibold text-white hover:bg-brand-deep transition"
            >
              Swap
            </button>
          </div>
        );
      })}
    </motion.div>
  );
}

export default function CartItem({ item, index, onQty, onRemove }) {
  const [showAlts, setShowAlts] = useState(false);
  const hasAlts = Array.isArray(item.alternatives)
    ? item.alternatives.length > 0
    : !!item.alternatives && (
        !!(item.alternatives.cheaper || item.alternatives.faster || item.alternatives.premium)
      );

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ delay: index * 0.03, duration: 0.25 }}
      className="relative rounded-card bg-white ring-1 ring-line overflow-hidden"
    >
      {/* Alternatives panel — slides in from left */}
      <AnimatePresence>
        {showAlts && (
          <AlternativesPanel item={item} onClose={() => setShowAlts(false)} />
        )}
      </AnimatePresence>

      <div className={`flex items-start gap-3 p-3 transition-all ${showAlts ? "ml-44" : ""}`}>
        {/* Product image */}
        <ProductImage product={item} />

        {/* Content */}
        <div className="min-w-0 flex-1">
          {/* Name + remove */}
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-ink">{item.name}</p>
              <p className="text-[11px] text-muted capitalize">{item.category}</p>
            </div>
            <button
              onClick={() => onRemove(item.id)}
              aria-label={`Remove ${item.name}`}
              className="shrink-0 p-3 -m-2 rounded-lg text-muted hover:text-rose hover:bg-rose-soft transition"
            >
              <X size={14} />
            </button>
          </div>

          {/* Alternatives toggle — only if item has alternatives */}
          {hasAlts && (
            <button
              onClick={() => setShowAlts((v) => !v)}
              className="mt-1.5 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium bg-brand-soft text-brand ring-1 ring-brand/15 hover:ring-brand/30 transition"
            >
              <TrendingDown size={9} />
              {showAlts ? "Hide" : "See alternatives"}
            </button>
          )}

          {/* Price + Qty stepper */}
          <div className="flex items-center justify-between mt-2.5">
            <div className="flex items-center rounded-full ring-1 ring-line bg-canvas h-11">
              <button
                onClick={() => onQty(item.id, item.quantity - 1)}
                aria-label="Decrease"
                className="grid h-full w-11 place-items-center rounded-full hover:bg-white transition"
              >
                <Minus size={14} />
              </button>
              <span className="w-6 text-center font-display text-sm font-semibold text-ink">
                {item.quantity}
              </span>
              <button
                onClick={() => onQty(item.id, item.quantity + 1)}
                aria-label="Increase"
                className="grid h-full w-11 place-items-center rounded-full hover:bg-white transition"
              >
                <Plus size={14} />
              </button>
            </div>
            <span className="font-display font-bold text-sm text-ink">
              {formatINR(item.price * item.quantity)}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
