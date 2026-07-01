import { useState } from "react";
import { motion } from "framer-motion";
import { Plus, Minus } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import { formatINR } from "../lib/format.js";

const S3 = "https://qcart-ai-apoorva-images.s3.ap-south-1.amazonaws.com/products/";

/**
 * Amazon Quick-Commerce style product card with quantity stepper.
 * Task 5: uses real product image from S3, falls back to /placeholder.jpg on error.
 */
export default function ProductCard({
  product,
  badge,
  badgeColor = "bg-green-600",
  subtitle,
  oldPrice,
  index = 0,
}) {
  const { cart, addProduct, setQty, removeItem } = useApp();
  const [imgErrored, setImgErrored] = useState(false);
  const cartItem = cart.find((i) => i.id === product.id);
  const qty = cartItem?.quantity || 0;

  const imgSrc = imgErrored
    ? "/placeholder.jpg"
    : `${S3}${product.id}.jpg`;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.35 }}
      viewport={{ once: true }}
      className="group relative flex flex-col h-full rounded-xl bg-white ring-1 ring-gray-200 hover:shadow-md transition-shadow overflow-hidden"
    >
      {/* Badge */}
      {badge && (
        <span className={`absolute top-2 left-2 z-10 rounded-md ${badgeColor} px-2 py-0.5 text-[10px] font-bold text-white uppercase`}>
          {badge}
        </span>
      )}

      {/* Product image */}
      <div className="flex items-center justify-center bg-gray-50 overflow-hidden" style={{ height: "120px" }}>
        <img
          src={imgSrc}
          alt={product.name}
          onError={() => setImgErrored(true)}
          className="h-full w-full object-contain"
        />
      </div>

      {/* Info area */}
      <div className="flex flex-col flex-1 px-3 pt-2.5 pb-3">
        <p className="font-medium text-[13px] leading-snug text-gray-900 line-clamp-2 min-h-[2.25rem]">
          {product.name}
        </p>
        {subtitle && (
          <p className="text-[11px] text-gray-500 mt-0.5 truncate">{subtitle}</p>
        )}
        <div className="flex-1 min-h-1" />
        <div className="flex items-baseline gap-1.5 mt-1.5">
          <span className="font-display font-bold text-base text-gray-900">
            {formatINR(product.price)}
          </span>
          {oldPrice && oldPrice > product.price && (
            <span className="text-xs text-gray-400 line-through">
              {formatINR(oldPrice)}
            </span>
          )}
        </div>
        <div className="mt-2.5">
          {qty > 0 ? (
            <div className="flex items-center justify-between rounded-lg overflow-hidden ring-1 ring-gray-200 h-[44px]">
              <button
                onClick={() => qty <= 1 ? removeItem(product.id) : setQty(product.id, qty - 1)}
                className="grid h-11 w-11 shrink-0 place-items-center text-gray-700 hover:bg-gray-100 active:bg-gray-200 transition"
                aria-label="Decrease quantity"
              >
                <Minus size={14} />
              </button>
              <span className="font-display font-bold text-sm text-gray-900 min-w-[2rem] text-center">{qty}</span>
              <button
                onClick={() => setQty(product.id, qty + 1)}
                className="grid h-11 w-11 shrink-0 place-items-center text-gray-700 hover:bg-gray-100 active:bg-gray-200 transition"
                aria-label="Increase quantity"
              >
                <Plus size={14} />
              </button>
            </div>
          ) : (
            <button
              onClick={() => addProduct({ ...product, reason: subtitle || "recommended for you" })}
              className="w-full flex items-center justify-center gap-1.5 rounded-lg min-h-[44px] text-sm font-semibold transition active:scale-[0.97]"
              style={{ backgroundColor: "#FFD814", color: "#111827" }}
              onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#F7CA00")}
              onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "#FFD814")}
            >
              <Plus size={14} />
              Add
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
}