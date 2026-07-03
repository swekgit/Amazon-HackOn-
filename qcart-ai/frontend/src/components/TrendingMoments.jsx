import { useMemo } from "react";
import { motion } from "framer-motion";
import { TrendingUp } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import { getTrendingForCustomer } from "../data/missions.js";

export default function TrendingMoments() {
  const { send, loading, customerProfile, city } = useApp();

  const trending = useMemo(
    () => getTrendingForCustomer(customerProfile, city),
    [customerProfile, city]
  );

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp size={18} className="text-smart" />
        <h2 className="font-display text-lg sm:text-xl font-bold text-ink">Trending Now</h2>
      </div>

      <div className="flex gap-3 overflow-x-auto no-scrollbar pb-3 snap-x-mandatory">
        {trending.map((moment, i) => (
          <motion.button
            key={moment.label}
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.06, duration: 0.4 }}
            viewport={{ once: true }}
            whileHover={{ scale: 1.05, y: -2 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => send(moment.intent)}
            disabled={loading}
            className={`shrink-0 rounded-xl ${moment.bgColor} border ${moment.borderColor} p-4 w-36 sm:w-40 text-left transition-all hover:shadow-md disabled:opacity-50 relative overflow-hidden`}
          >
            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-white/70 mb-2">
              <span className="text-2xl">{moment.emoji}</span>
            </div>
            <p className="font-display font-semibold text-sm leading-tight text-ink">{moment.label}</p>
            <span className="mt-1.5 inline-block rounded-full bg-white px-2 py-0.5 text-[10px] font-bold text-ink/50">
              {moment.count} carts
            </span>
          </motion.button>
        ))}
      </div>
    </div>
  );
}
