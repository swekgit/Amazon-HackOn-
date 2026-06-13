import { Zap } from "lucide-react";

export default function Footer() {
  const links = {
    Shop: ["All Categories", "Deals", "Buy Again", "New Arrivals"],
    Help: ["FAQ", "Contact", "Delivery Info", "Returns"],
    Connect: ["About Us", "Careers", "Blog", "Press"],
  };

  return (
    <footer className="mt-12 bg-ink text-white/70">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-2 sm:col-span-1">
            <div className="flex items-center gap-1.5 mb-3">
              <span className="text-xl">⚡</span>
              <span className="font-display text-lg font-bold text-white">QCart AI</span>
            </div>
            <p className="text-sm leading-relaxed text-white/40">
              Moment-aware quick commerce. Describe what you need — AI handles the rest.
            </p>
            <div className="mt-3 flex items-center gap-1.5 text-xs text-smart">
              <Zap size={12} />
              <span>10-min delivery</span>
            </div>
          </div>

          {/* Link columns */}
          {Object.entries(links).map(([title, items]) => (
            <div key={title}>
              <h4 className="font-display font-semibold text-white text-sm mb-3">{title}</h4>
              <ul className="space-y-2">
                {items.map((item) => (
                  <li key={item}>
                    <a href="#" className="text-sm hover:text-white transition-colors">{item}</a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-xs text-white/30">
            © 2026 QCart AI · Powered by Claude · Amazon HackOn 6
          </p>
        </div>
      </div>
    </footer>
  );
}
