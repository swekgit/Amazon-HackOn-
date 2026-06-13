import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MapPin, Search, ShoppingCart, User, Zap, ChevronDown } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";

export default function Header() {
  const { cart, setCartOpen, theme, city, cities, setCity } = useApp();
  const [scrolled, setScrolled] = useState(false);
  const [cityOpen, setCityOpen] = useState(false);
  const cityRef = useRef(null);
  const itemCount = cart.reduce((s, i) => s + i.quantity, 0);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Close dropdown on outside click
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
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 bg-headerBg ${
        scrolled
          ? "shadow-md border-b border-border"
          : "border-b border-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5">
              <span className="text-2xl">⚡</span>
              <span className="font-display text-xl font-bold tracking-tight text-ink">
                QCart
              </span>
              <span className="rounded-md bg-smart px-1.5 py-0.5 text-[10px] font-bold text-white uppercase tracking-wider">
                AI
              </span>
            </div>
          </div>

          {/* Delivery Location — dynamic dropdown, hidden on mobile */}
          <div className="hidden md:block relative" ref={cityRef}>
            <button
              onClick={() => setCityOpen((v) => !v)}
              className="flex items-center gap-1.5 text-sm hover:bg-white/40 rounded-lg px-2 py-1.5 transition-colors"
            >
              <MapPin size={14} className="text-smart shrink-0" />
              <div className="leading-tight text-left">
                <p className="text-[10px] text-ink/50">Deliver to</p>
                <p className="font-medium text-sm text-ink flex items-center gap-1">
                  {city}
                  <ChevronDown size={12} className={`text-ink/40 transition-transform ${cityOpen ? "rotate-180" : ""}`} />
                </p>
              </div>
            </button>

            <AnimatePresence>
              {cityOpen && cities.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: -6, scale: 0.97 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -6, scale: 0.97 }}
                  transition={{ duration: 0.15 }}
                  className="absolute top-full left-0 mt-1 w-48 bg-white rounded-xl shadow-xl ring-1 ring-border overflow-hidden z-50"
                >
                  {cities.map((c) => (
                    <button
                      key={c}
                      onClick={() => { setCity(c); setCityOpen(false); }}
                      className={`w-full text-left px-4 py-2.5 text-sm transition-colors flex items-center gap-2 ${
                        c === city
                          ? "bg-smart-soft text-smart-dark font-semibold"
                          : "text-ink hover:bg-canvas"
                      }`}
                    >
                      <MapPin size={12} className={c === city ? "text-smart" : "text-ink/30"} />
                      {c}
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Mini search — hidden on mobile */}
          <button
            onClick={() => {
              const hero = document.getElementById("hero-search");
              hero?.scrollIntoView({ behavior: "smooth" });
            }}
            className="hidden lg:flex items-center gap-2 px-4 py-2 rounded-full bg-white ring-1 ring-border text-sm text-ink/50 hover:ring-smart/50 transition-all max-w-xs flex-1 mx-8"
          >
            <Search size={14} />
            <span>Search your moment…</span>
          </button>

          {/* Right actions */}
          <div className="flex items-center gap-3">
            {/* Delivery badge */}
            <div className="hidden sm:flex items-center gap-1 rounded-full bg-amazonYellow px-2.5 py-1 text-xs font-bold text-ink">
              <Zap size={12} />
              <span>10 min</span>
            </div>

            {/* Cart */}
            <button
              onClick={() => setCartOpen(true)}
              className="relative p-2.5 rounded-xl hover:bg-white/60 transition-colors"
              aria-label="Open cart"
            >
              <ShoppingCart size={20} className="text-ink" />
              {itemCount > 0 && (
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute -top-0.5 -right-0.5 grid h-5 w-5 place-items-center rounded-full bg-smart text-[10px] font-bold text-white"
                >
                  {itemCount}
                </motion.span>
              )}
            </button>

            {/* Profile */}
            <button className="p-2.5 rounded-xl hover:bg-white/60 transition-colors" aria-label="Profile">
              <User size={20} className="text-ink" />
            </button>
          </div>
        </div>
      </div>
    </motion.header>
  );
}
