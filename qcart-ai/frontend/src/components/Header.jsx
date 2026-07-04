import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MapPin, ShoppingCart, User, Zap, ChevronDown } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import { CUSTOMERS } from "../lib/constants.js";

export default function Header() {
  const { cart, setCartOpen, city, cities, setCity, customerId, setCustomerId } = useApp();
  const [scrolled, setScrolled] = useState(false);
  const [cityOpen, setCityOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const cityRef = useRef(null);
  const profileRef = useRef(null);
  const activeCustomer = CUSTOMERS.find((c) => c.value === customerId);
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

  useEffect(() => {
    if (!profileOpen) return;
    const onClickOutside = (e) => {
      if (profileRef.current && !profileRef.current.contains(e.target)) setProfileOpen(false);
    };
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [profileOpen]);

  return (
    <motion.header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-white/95 backdrop-blur-md shadow-sm border-b border-line"
          : "bg-white border-b border-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center justify-between gap-y-2 py-2 sm:h-14 sm:py-0">

          {/* Left: Logo + AI badge */}
          <div className="flex items-center gap-1 sm:gap-2">
            <span className="text-lg sm:text-xl">⚡</span>
            <span className="font-display text-base sm:text-lg font-bold tracking-tight text-ink">
              QCart
            </span>
            <span className="rounded-md bg-brand px-1 sm:px-1.5 py-0.5 text-[8px] sm:text-[9px] font-bold text-white uppercase tracking-wider">
              AI
            </span>
          </div>

          {/* Center: Location + Delivery */}
          <div className="flex items-center gap-1.5 sm:gap-3">
            {/* Location pill */}
            <div className="relative" ref={cityRef}>
              <button
                onClick={() => setCityOpen((v) => !v)}
                className="flex items-center gap-1 sm:gap-1.5 rounded-full bg-canvas px-2 sm:px-3 py-1 sm:py-1.5 text-xs sm:text-sm ring-1 ring-line hover:ring-brand/30 transition"
              >
                <MapPin size={11} className="text-brand sm:w-[13px] sm:h-[13px]" />
                <span className="font-medium text-ink text-[10px] sm:text-xs">{city}</span>
                <ChevronDown size={10} className={`text-muted transition-transform sm:w-[11px] sm:h-[11px] ${cityOpen ? "rotate-180" : ""}`} />
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
            <div className="flex items-center gap-1 rounded-full bg-green-soft px-2 sm:px-2.5 py-1 text-[9px] sm:text-[11px] font-semibold text-green">
              <Zap size={10} className="sm:w-[11px] sm:h-[11px]" />
              <span>10 min</span>
            </div>
          </div>

          {/* Right: Cart + Profile */}
          <div className="flex items-center gap-1 sm:gap-2">
            {/* Cart button */}
            <button
              onClick={() => setCartOpen(true)}
              className="relative p-1.5 sm:p-2 rounded-xl hover:bg-canvas transition"
              aria-label="Open cart"
            >
              <ShoppingCart size={18} className="text-ink sm:w-[20px] sm:h-[20px]" />
              {itemCount > 0 && (
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute -top-0.5 -right-0.5 grid h-[16px] w-[16px] sm:h-[18px] sm:w-[18px] place-items-center rounded-full bg-brand text-[8px] sm:text-[9px] font-bold text-white"
                >
                  {itemCount}
                </motion.span>
              )}
            </button>

            {/* Profile / customer switcher */}
            <div className="relative" ref={profileRef}>
              <button
                onClick={() => setProfileOpen((v) => !v)}
                className="flex items-center gap-1 sm:gap-1.5 rounded-full bg-canvas px-2 sm:px-3 py-1 sm:py-1.5 text-xs sm:text-sm ring-1 ring-line hover:ring-brand/30 transition"
                aria-label={`Profile: ${activeCustomer?.label || "Customer"}`}
                aria-expanded={profileOpen}
              >
                <User size={11} className="text-brand sm:w-[13px] sm:h-[13px]" />
                <span className="font-medium text-ink text-[10px] sm:text-xs">
                  {activeCustomer?.label || "Customer"}
                </span>
                <ChevronDown size={10} className={`text-muted transition-transform sm:w-[11px] sm:h-[11px] ${profileOpen ? "rotate-180" : ""}`} />
              </button>

              <AnimatePresence>
                {profileOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -4, scale: 0.97 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -4, scale: 0.97 }}
                    transition={{ duration: 0.12 }}
                    className="absolute top-full right-0 mt-1 w-44 bg-white rounded-xl shadow-xl ring-1 ring-line overflow-hidden z-50"
                  >
                    <div className="px-4 py-2.5 text-[10px] font-semibold uppercase tracking-wider text-muted border-b border-line">
                      Switch customer
                    </div>
                    {CUSTOMERS.map((c) => (
                      <button
                        key={c.value}
                        onClick={() => {
                          setCustomerId(c.value);
                          setProfileOpen(false);
                        }}
                        className={`w-full text-left px-4 py-2.5 text-sm transition-colors flex items-center gap-2 ${
                          c.value === customerId
                            ? "bg-brand-soft text-brand-deep font-semibold"
                            : "text-ink hover:bg-canvas"
                        }`}
                      >
                        <User size={11} className={c.value === customerId ? "text-brand" : "text-muted"} />
                        {c.label}
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>
    </motion.header>
  );
}
