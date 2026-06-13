import { motion } from "framer-motion";
import { TrendingUp } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";

const TRENDING = [
  { label: "Movie Night", emoji: "🎬", intent: "Movie night for 4 people", count: "2.4k", gradient: "from-violet-500 to-purple-700" },
  { label: "Morning Essentials", emoji: "☀️", intent: "Morning breakfast for family", count: "1.8k", gradient: "from-amber-400 to-orange-500" },
  { label: "Party Time", emoji: "🎉", intent: "Party for 6 people", count: "1.2k", gradient: "from-pink-500 to-rose-600" },
  { label: "Fever Care", emoji: "🤒", intent: "I have fever and feel weak", count: "890", gradient: "from-red-400 to-rose-600" },
  { label: "Study Session", emoji: "📚", intent: "Study session fuel", count: "756", gradient: "from-blue-500 to-indigo-600" },
  { label: "Rainy Day Comfort", emoji: "🌧️", intent: "Rainy day comfort food", count: "1.5k", gradient: "from-slate-400 to-cyan-600" },
  { label: "Weekly Groceries", emoji: "🛒", intent: "Weekly grocery run for family", count: "3.1k", gradient: "from-emerald-500 to-green-700" },
  { label: "Baby Needs", emoji: "👶", intent: "Baby essentials", count: "670", gradient: "from-pink-300 to-fuchsia-400" },
];

export default function TrendingMoments() {
  const { send, loading } = useApp();

  return (
    <div>
      <div className="flex items-center gap-2 mb-6">
        <TrendingUp size={20} className="text-smart" />
        <h2 className="font-display text-xl sm:text-2xl font-bold">Trending Now</h2>
      </div>

      <div className="flex gap-3 overflow-x-auto no-scrollbar pb-4 snap-x-mandatory">
        {TRENDING.map((moment, i) => (
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
            className={`shrink-0 rounded-2xl bg-gradient-to-br ${moment.gradient} p-4 w-36 sm:w-40 text-white text-left transition-shadow hover:shadow-lg disabled:opacity-50 relative overflow-hidden`}
          >
            <div className="absolute -top-3 -right-3 w-16 h-16 rounded-full bg-white/10 blur-lg" />
            <span className="text-2xl">{moment.emoji}</span>
            <p className="mt-2 font-display font-semibold text-sm leading-tight">{moment.label}</p>
            <span className="mt-1.5 inline-block rounded-full bg-white/20 px-2 py-0.5 text-[10px] font-bold">
              {moment.count} carts
            </span>
          </motion.button>
        ))}
      </div>
    </div>
  );
}
