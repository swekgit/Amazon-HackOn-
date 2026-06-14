import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { MapPin, Search, ShoppingCart, User, Zap } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";

export default function Header() {
  const { cart, setCartOpen, theme } = useApp();
  const [scrolled, setScrolled] = useState(false);
  const itemCount = cart.reduce((s, i) => s + i.quantity, 0);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

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

          {/* Delivery Location — hidden on mobile */}
          <div className="hidden md:flex items-center gap-1.5 text-sm">
            <MapPin size={14} className="text-smart" />
            <div className="leading-tight">
              <p className="text-[10px] text-ink/50">Deliver to</p>
              <p className="font-medium text-sm text-ink">Bangalore 560001</p>
            </div>
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
