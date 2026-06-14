import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MapPin, ShoppingCart, User, Zap, ChevronDown } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";

export default function Header() {
  const { cart, setCartOpen, city, cities, setCity } = useApp();
  const [scrolled, setScrolled] = useState(false);
  const [cityOpen, setCityOpen] = useState(false);
  const cityRef = useRef(null);
  const itemCount = cart.reduce((s, i) => s + i.quantity, 0);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (!cityOpen) return;
    const onClickOutside = (e) => {
      if (cityRef.current && !cityRef.current.contains(e.target)) setCityOpen(false);
    };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [cityOpen]);

  return (
    <motion.header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-white/95 backdrop-blur-md shadow-sm border-b border-line"
          : "bg-white border-b border-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">

          {/* Left: Logo + AI badge */}
          <div className="flex items-center gap-2">
            <span className="text-xl">⚡</span>
            <span className="font-display text-lg font-bold tracking-tight text-ink">
              QCart
            </span>
            <span className="rounded-md bg-brand px-1.5 py-0.5 text-[9px] font-bold text-white uppercase tracking-wider">
              AI
            </span>
          </div>

          {/* Center: Location + Delivery */}
          <div className="hidden sm:flex items-center gap-3">
            {/* Location pill */}
            <div className="relative" ref={cityRef}>
              <button
                onClick={() => setCityOpen((v) => !v)}
                className="flex items-center gap-1.5 rounded-full bg-canvas px-3 py-1.5 text-sm ring-1 ring-line hover:ring-brand/30 transition"
              >
                <MapPin size={13} className="text-brand" />
                <span className="font-medium text-ink text-xs">{city}</span>
                <ChevronDown size={11} className={`text-muted transition-transform ${cityOpen ? "rotate-180" : ""}`} />
              </button>

              <AnimatePresence>
                {cityOpen && cities.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: -4, scale: 0.97 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -4, scale: 0.97 }}
                    transition={{ duration: 0.12 }}
                    className="absolute top-full left-0 mt-1 w-44 bg-white rounded-xl shadow-xl ring-1 ring-line overflow-hidden z-50"
                  >
                    {cities.map((c) => (
                      <button
                        key={c}
                        onClick={() => { setCity(c); setCityOpen(false); }}
                        className={`w-full text-left px-4 py-2.5 text-sm transition-colors flex items-center gap-2 ${
                          c === city
                            ? "bg-brand-soft text-brand-deep font-semibold"
                            : "text-ink hover:bg-canvas"
                        }`}
                      >
                        <MapPin size={11} className={c === city ? "text-brand" : "text-muted"} />
                        {c}
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* 10 min delivery badge */}
            <div className="flex items-center gap-1 rounded-full bg-green-soft px-2.5 py-1 text-[11px] font-semibold text-green">
              <Zap size={11} />
              <span>10 min</span>
            </div>
          </div>

          {/* Right: Cart + Profile */}
          <div className="flex items-center gap-2">
            {/* Cart button */}
            <button
              onClick={() => setCartOpen(true)}
              className="relative p-2 rounded-xl hover:bg-canvas transition"
              aria-label="Open cart"
            >
              <ShoppingCart size={20} className="text-ink" />
              {itemCount > 0 && (
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute -top-0.5 -right-0.5 grid h-[18px] w-[18px] place-items-center rounded-full bg-brand text-[9px] font-bold text-white"
                >
                  {itemCount}
                </motion.span>
              )}
            </button>

            {/* Profile */}
            <button className="p-2 rounded-xl hover:bg-canvas transition" aria-label="Profile">
              <User size={20} className="text-ink" />
            </button>
          </div>
        </div>
      </div>
    </motion.header>
  );
}
