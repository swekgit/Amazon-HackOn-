import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { MISSIONS } from "../data/missions.js";
import { useApp } from "../state/AppContext.jsx";

const MISSION_VISUALS = {
  "Movie Night": { iconBg: "bg-purple-50", borderAccent: "border-purple-200" },
  "Rainy Day": { iconBg: "bg-cyan-50", borderAccent: "border-cyan-200" },
  "Guests at Home": { iconBg: "bg-amber-50", borderAccent: "border-amber-200" },
  "Study Session": { iconBg: "bg-blue-50", borderAccent: "border-blue-200" },
  "Fever Care": { iconBg: "bg-red-50", borderAccent: "border-red-200" },
  "Summer Essentials": { iconBg: "bg-orange-50", borderAccent: "border-orange-200" },
  "Late Night Cravings": { iconBg: "bg-indigo-50", borderAccent: "border-indigo-200" },
};

const cardVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  visible: (i) => ({
    opacity: 1, y: 0, scale: 1,
    transition: { delay: i * 0.06, duration: 0.5, ease: [0.22, 1, 0.36, 1] },
  }),
};

export default function MissionCards({ onMomentSelect }) {
  const { send, loading } = useApp();

  const handleSelect = (mi) => {
    onMomentSelect?.(mi.label);
    send(mi.intent);
  };

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <Sparkles size={18} className="text-smart" />
        <h2 className="font-display text-lg sm:text-xl font-bold text-ink">What's your moment?</h2>
      </div>

      <div className="grid grid-cols-1 min-[360px]:grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-3">
        {MISSIONS.map((mi, i) => {
          const visual = MISSION_VISUALS[mi.label] || { iconBg: "bg-gray-50", borderAccent: "border-gray-200" };
          return (
            <motion.button
              key={mi.label}
              custom={i}
              variants={cardVariants}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              whileHover={{ y: -4, scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => handleSelect(mi)}
              disabled={loading}
              className={`relative overflow-hidden rounded-xl bg-white p-4 text-left transition-shadow disabled:opacity-50
                border ${visual.borderAccent}
                hover:shadow-lg hover:shadow-black/8
                ${mi.urgent ? "border-l-4 border-l-rose-400" : ""}
              `}
            >
              {/* Emoji icon with tinted background */}
              <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl ${visual.iconBg} mb-2`}>
                <span className="text-2xl">{mi.emoji}</span>
              </div>

              <p className="font-display font-semibold text-sm leading-tight text-ink">
                {mi.label}
              </p>
              <p className="mt-0.5 text-xs text-ink/50 leading-snug">
                {mi.description}
              </p>

              {mi.urgent && (
                <span className="mt-2 inline-block rounded-full bg-rose-50 text-rose-600 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider">
                  Urgent
                </span>
              )}
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}
