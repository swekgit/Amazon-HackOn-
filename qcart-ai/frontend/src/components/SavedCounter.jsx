import { motion } from "framer-motion";
import { Zap, Clock } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import { savings } from "../lib/format.js";

export default function SavedCounter() {
  const { cart, meta } = useApp();
  if (!cart || cart.length === 0) return null;
  const { minutes } = savings(cart);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="inline-flex items-center gap-2 rounded-full bg-smart-soft px-4 py-2 text-xs font-medium text-smart-dark"
    >
      {meta.buildTime ? (
        <>
          <Zap size={13} />
          <span>Cart built in <b>{meta.buildTime}s</b></span>
        </>
      ) : (
        <>
          <Clock size={13} />
          <span>Saved ~<b>{minutes} min</b></span>
        </>
      )}
    </motion.div>
  );
}
