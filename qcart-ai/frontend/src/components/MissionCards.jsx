import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { MISSIONS } from "../data/missions.js";
import { useApp } from "../state/AppContext.jsx";

const cardVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  visible: (i) => ({
    opacity: 1, y: 0, scale: 1,
    transition: { delay: i * 0.06, duration: 0.5, ease: [0.22, 1, 0.36, 1] },
  }),
};

export default function MissionCards() {
  const { send, loading } = useApp();

  return (
    <div>
      <div className="flex items-center gap-2 mb-6">
        <Sparkles size={20} className="text-smart" />
        <h2 className="font-display text-xl sm:text-2xl font-bold">What's your moment?</h2>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
        {MISSIONS.map((mi, i) => (
          <motion.button
            key={mi.label}
            custom={i}
            variants={cardVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
            whileHover={{ y: -4, scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => send(mi.intent)}
            disabled={loading}
            className={`relative overflow-hidden rounded-2xl p-5 text-left text-white transition-shadow disabled:opacity-50
              bg-gradient-to-br ${mi.gradient}
              hover:shadow-xl hover:shadow-black/15
              ${mi.urgent ? "ring-2 ring-rose-300" : ""}
            `}
          >
            {/* Decorative orb */}
            <div className="absolute -top-6 -right-6 w-24 h-24 rounded-full bg-white/10 blur-xl" />

            <span className="text-3xl sm:text-4xl block mb-2">{mi.emoji}</span>
            <p className="font-display font-semibold text-sm sm:text-base leading-tight">
              {mi.label}
            </p>
            <p className="mt-1 text-xs text-white/70 leading-snug">
              {mi.description}
            </p>

            {mi.urgent && (
              <span className="mt-2 inline-block rounded-full bg-white/20 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider">
                Urgent
              </span>
            )}
          </motion.button>
        ))}
      </div>
    </div>
  );
}
