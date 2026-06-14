import { useRef } from "react";
import { motion } from "framer-motion";
import { Tag, ChevronLeft, ChevronRight, Truck, Zap, Scissors } from "lucide-react";

const OFFERS = [
  {
    title: "Flat ₹50 Off",
    subtitle: "On your first AI-curated cart",
    emoji: "🎁",
    code: "QCART50",
    tagColor: "bg-smart text-white",
    bgColor: "bg-gradient-to-r from-amber-50 to-orange-50",
    accentColor: "border-smart",
  },
  {
    title: "Free Delivery",
    subtitle: "On orders above ₹199",
    emoji: "🚚",
    code: "FREE199",
    tagColor: "bg-fresh text-white",
    bgColor: "bg-gradient-to-r from-emerald-50 to-green-50",
    accentColor: "border-fresh",
  },
  {
    title: "10-Min Delivery",
    subtitle: "Guaranteed or ₹25 cashback",
    emoji: "⚡",
    code: null,
    tagColor: "bg-amazonYellow text-ink",
    bgColor: "bg-gradient-to-r from-yellow-50 to-amber-50",
    accentColor: "border-amazonYellow",
  },
  {
    title: "Party Special",
    subtitle: "20% off on party supplies this weekend",
    emoji: "🎉",
    code: "PARTY20",
    tagColor: "bg-pink-500 text-white",
    bgColor: "bg-gradient-to-r from-pink-50 to-rose-50",
    accentColor: "border-pink-300",
  },
  {
    title: "Baby Essentials",
    subtitle: "Buy 2 Get 1 Free on baby care",
    emoji: "👶",
    code: "BABY3",
    tagColor: "bg-sky-500 text-white",
    bgColor: "bg-gradient-to-r from-sky-50 to-blue-50",
    accentColor: "border-sky-300",
  },
  {
    title: "Coffee Lovers",
    subtitle: "₹30 cashback on coffee orders",
    emoji: "☕",
    code: "COFFEE30",
    tagColor: "bg-amber-700 text-white",
    bgColor: "bg-gradient-to-r from-amber-50 to-yellow-50",
    accentColor: "border-amber-300",
  },
];

export default function OfferBanners() {
  const scrollRef = useRef(null);

  const scroll = (dir) => {
    if (!scrollRef.current) return;
    scrollRef.current.scrollBy({ left: dir * 300, behavior: "smooth" });
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Tag size={18} className="text-smart" />
          <h2 className="font-display text-lg sm:text-xl font-bold text-ink">Deals & Offers</h2>
        </div>
        <div className="hidden sm:flex gap-1">
          <button onClick={() => scroll(-1)} className="p-2 rounded-lg hover:bg-canvas ring-1 ring-border transition">
            <ChevronLeft size={16} />
          </button>
          <button onClick={() => scroll(1)} className="p-2 rounded-lg hover:bg-canvas ring-1 ring-border transition">
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      <div ref={scrollRef} className="flex gap-3 overflow-x-auto no-scrollbar pb-3 snap-x-mandatory">
        {OFFERS.map((offer, i) => (
          <motion.div
            key={offer.title}
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.07, duration: 0.4 }}
            viewport={{ once: true }}
            whileHover={{ scale: 1.02, y: -2 }}
            className={`shrink-0 w-[280px] rounded-xl ${offer.bgColor} p-5 cursor-pointer
              border-l-4 ${offer.accentColor}
              shadow-sm hover:shadow-md transition-all relative overflow-hidden ring-1 ring-border`}
          >
            {/* Offer tag */}
            <span className={`inline-block ${offer.tagColor} text-xs font-bold px-2.5 py-1 rounded-md mb-3`}>
              {offer.emoji} {offer.title}
            </span>

            <p className="text-sm text-ink/70 leading-snug">{offer.subtitle}</p>

            {offer.code && (
              <div className="mt-3 inline-flex items-center gap-1.5 rounded-md border-2 border-dashed border-smart/40 bg-white px-3 py-1.5">
                <Scissors size={12} className="text-smart" />
                <span className="text-xs font-mono font-bold text-smart tracking-wider">{offer.code}</span>
              </div>
            )}

            {!offer.code && (
              <div className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium text-fresh">
                <Zap size={12} />
                <span>Auto-applied</span>
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
}
