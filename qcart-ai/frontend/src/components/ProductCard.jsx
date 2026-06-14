import { motion } from "framer-motion";
import { Plus, Minus } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import { getCategoryEmoji } from "../data/products.js";
import { formatINR } from "../lib/format.js";

/**
 * Amazon Quick-Commerce style product card with quantity stepper.
 *
 * Features:
 *  - Fixed height, flex-col, CTA pinned to bottom
 *  - Not-in-cart: yellow [+ Add] button
 *  - In-cart: [-] qty [+] stepper
 *  - Uniform across all grids
 *
 * Props:
 *  product   : { id, name, price, category, tags?, reason? }
 *  badge     : string | null (e.g. "20% OFF")
 *  badgeColor: string (tailwind bg class, default "bg-green-600")
 *  subtitle  : string (e.g. "Ordered 3x" or reason)
 *  oldPrice  : number | null (strike-through price)
 *  index     : number (stagger delay)
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
  const cartItem = cart.find((i) => i.id === product.id);
  const qty = cartItem?.quantity || 0;
  const emoji = getCategoryEmoji(product.category);

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

      {/* Product visual area */}
      <div className="flex items-center justify-center bg-gray-50 py-5">
        <span className="text-4xl select-none">{emoji}</span>
      </div>

      {/* Info area — flex-1 pushes CTA to bottom */}
      <div className="flex flex-col flex-1 px-3 pt-2.5 pb-3">
        {/* Product name — 2 lines max */}
        <p className="font-medium text-[13px] leading-snug text-gray-900 line-clamp-2 min-h-[2.25rem]">
          {product.name}
        </p>

        {/* Subtitle / reason */}
        {subtitle && (
          <p className="text-[11px] text-gray-500 mt-0.5 truncate">{subtitle}</p>
        )}

        {/* Spacer */}
        <div className="flex-1 min-h-1" />

        {/* Price row */}
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

        {/* CTA — always at bottom (mt-auto) */}
        <div className="mt-2.5">
          {qty > 0 ? (
            /* Quantity stepper */
            <div className="flex items-center justify-between rounded-lg overflow-hidden ring-1 ring-gray-200">
              <button
                onClick={() =>
                  qty <= 1
                    ? removeItem(product.id)
                    : setQty(product.id, qty - 1)
                }
                className="grid h-9 w-9 place-items-center text-gray-700 hover:bg-gray-100 active:bg-gray-200 transition"
                aria-label="Decrease quantity"
              >
                <Minus size={14} />
              </button>
              <span className="font-display font-bold text-sm text-gray-900 min-w-[2rem] text-center">
                {qty}
              </span>
              <button
                onClick={() => setQty(product.id, qty + 1)}
                className="grid h-9 w-9 place-items-center text-gray-700 hover:bg-gray-100 active:bg-gray-200 transition"
                aria-label="Increase quantity"
              >
                <Plus size={14} />
              </button>
            </div>
          ) : (
            /* Add button — Amazon yellow */
            <button
              onClick={() =>
                addProduct({ ...product, reason: subtitle || "recommended for you" })
              }
              className="w-full flex items-center justify-center gap-1.5 rounded-lg py-2 text-sm font-semibold transition active:scale-[0.97]"
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
