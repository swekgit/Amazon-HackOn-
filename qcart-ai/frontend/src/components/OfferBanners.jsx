import { useRef } from "react";
import { motion } from "framer-motion";
import { Tag, ChevronLeft, ChevronRight } from "lucide-react";

const OFFERS = [
  { title: "Flat ₹50 Off", subtitle: "On your first AI-curated cart", emoji: "🎁", gradient: "from-violet-500 to-purple-700", code: "QCART50" },
  { title: "Free Delivery", subtitle: "On orders above ₹199", emoji: "🚚", gradient: "from-emerald-500 to-green-700", code: "FREE199" },
  { title: "10-Min Delivery", subtitle: "Guaranteed or ₹25 cashback", emoji: "⚡", gradient: "from-amber-500 to-orange-600", code: null },
  { title: "Party Special", subtitle: "20% off on party supplies this weekend", emoji: "🎉", gradient: "from-pink-500 to-rose-600", code: "PARTY20" },
  { title: "Baby Essentials", subtitle: "Buy 2 Get 1 Free on baby care", emoji: "👶", gradient: "from-sky-400 to-blue-600", code: "BABY3" },
  { title: "Coffee Lovers", subtitle: "₹30 cashback on coffee orders", emoji: "☕", gradient: "from-amber-700 to-yellow-900", code: "COFFEE30" },
];

export default function OfferBanners() {
  const scrollRef = useRef(null);

  const scroll = (dir) => {
    if (!scrollRef.current) return;
    scrollRef.current.scrollBy({ left: dir * 300, behavior: "smooth" });
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Tag size={20} className="text-smart" />
          <h2 className="font-display text-xl sm:text-2xl font-bold">Deals & Offers</h2>
        </div>
        <div className="hidden sm:flex gap-1">
          <button onClick={() => scroll(-1)} className="p-2 rounded-lg hover:bg-white/60 ring-1 ring-black/5 transition">
            <ChevronLeft size={16} />
          </button>
          <button onClick={() => scroll(1)} className="p-2 rounded-lg hover:bg-white/60 ring-1 ring-black/5 transition">
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      <div ref={scrollRef} className="flex gap-4 overflow-x-auto no-scrollbar pb-4 snap-x-mandatory">
        {OFFERS.map((offer, i) => (
          <motion.div
            key={offer.title}
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.07, duration: 0.4 }}
            viewport={{ once: true }}
            whileHover={{ scale: 1.03, y: -2 }}
            className={`shrink-0 w-[280px] rounded-2xl bg-gradient-to-br ${offer.gradient} p-6 text-white cursor-pointer
              shadow-lg hover:shadow-xl transition-shadow relative overflow-hidden`}
          >
            <div className="absolute -bottom-4 -right-4 w-24 h-24 rounded-full bg-white/10 blur-lg" />
            <span className="text-3xl">{offer.emoji}</span>
            <h3 className="mt-3 font-display text-lg font-bold">{offer.title}</h3>
            <p className="mt-1 text-sm text-white/80">{offer.subtitle}</p>
            {offer.code && (
              <div className="mt-3 inline-block rounded-lg bg-white/20 px-3 py-1 text-xs font-mono font-bold tracking-wider">
                {offer.code}
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
}
