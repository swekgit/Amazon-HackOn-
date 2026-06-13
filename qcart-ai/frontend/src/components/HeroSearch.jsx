import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, Loader2, MessageCircle, Mic, Sparkles } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import VoiceButton from "./VoiceButton.jsx";

const PLACEHOLDERS = [
  "Movie night for 4",
  "Rainy day snacks",
  "Guests arriving in 1 hour",
  "Morning breakfast",
  "Party for 6",
  "Study session fuel",
  "Feeling under the weather",
  "Late night cravings",
];

export default function HeroSearch() {
  const { send, loading, setChatOpen, theme } = useApp();
  const [text, setText] = useState("");
  const [placeholderIdx, setPlaceholderIdx] = useState(0);
  const [displayedPlaceholder, setDisplayedPlaceholder] = useState("");
  const [isTyping, setIsTyping] = useState(true);
  const inputRef = useRef(null);

  // Typing animation effect
  useEffect(() => {
    const current = PLACEHOLDERS[placeholderIdx];
    let charIdx = 0;
    let timer;

    if (isTyping) {
      timer = setInterval(() => {
        charIdx++;
        setDisplayedPlaceholder(current.slice(0, charIdx));
        if (charIdx >= current.length) {
          clearInterval(timer);
          setTimeout(() => setIsTyping(false), 1800);
        }
      }, 55);
    } else {
      timer = setInterval(() => {
        setDisplayedPlaceholder((prev) => {
          if (prev.length <= 0) {
            clearInterval(timer);
            setPlaceholderIdx((i) => (i + 1) % PLACEHOLDERS.length);
            setIsTyping(true);
            return "";
          }
          return prev.slice(0, -1);
        });
      }, 30);
    }
    return () => clearInterval(timer);
  }, [placeholderIdx, isTyping]);

  const submit = useCallback(
    (value) => {
      const v = (value ?? text).trim();
      if (!v || loading) return;
      send(v);
      setText("");
    },
    [text, loading, send]
  );

  const quickPicks = [
    { label: "🎬 Movie Night", intent: "Movie night for 4" },
    { label: "🎉 Party for 6", intent: "Party for 6 people" },
    { label: "🌧️ Rainy Day", intent: "Rainy day comfort food" },
    { label: "🤒 Fever Care", intent: "I have fever and feel weak" },
  ];

  return (
    <section id="hero-search" className="relative pt-24 pb-12 sm:pt-32 sm:pb-16 overflow-hidden">
      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full opacity-20 blur-3xl"
          style={{ background: `radial-gradient(circle, ${theme.accent}40, transparent 70%)` }}
        />
      </div>

      <div className="relative max-w-3xl mx-auto px-4 sm:px-6 text-center">
        {/* Headline */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        >
          <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold leading-[1.1] tracking-tight">
            Don't search.{" "}
            <span
              className="text-gradient bg-gradient-to-r"
              style={{
                backgroundImage: `linear-gradient(135deg, ${theme.accent}, ${theme.accent}CC)`,
              }}
            >
              Just say your moment.
            </span>
          </h1>
          <p className="mt-4 text-base sm:text-lg text-ink/50 max-w-xl mx-auto">
            AI builds your checkout-ready cart in seconds. Describe what you need — we handle the rest.
          </p>
        </motion.div>

        {/* Search bar */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
          className="mt-8 sm:mt-10"
        >
          <div className="relative flex items-center gap-2 rounded-2xl bg-white/90 backdrop-blur-sm p-2 pl-5 ring-1 ring-black/10 shadow-xl shadow-black/5 focus-within:ring-2 focus-within:ring-smart transition-all">
            <div className="relative min-w-0 flex-1">
              <input
                ref={inputRef}
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && submit()}
                className="w-full bg-transparent py-3 text-lg text-ink placeholder:text-transparent focus:outline-none"
                placeholder={displayedPlaceholder}
              />
              {/* Animated placeholder overlay */}
              {!text && (
                <div className="absolute inset-0 flex items-center pointer-events-none">
                  <span className="text-lg text-ink/30">
                    {displayedPlaceholder}
                    <motion.span
                      animate={{ opacity: [1, 0] }}
                      transition={{ repeat: Infinity, duration: 0.8 }}
                      className="inline-block w-0.5 h-5 bg-smart/60 ml-0.5 align-middle"
                    />
                  </span>
                </div>
              )}
            </div>

            <VoiceButton onResult={(t) => submit(t)} disabled={loading} />

            <button
              onClick={() => setChatOpen(true)}
              className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-white text-ink ring-1 ring-black/10 hover:ring-smart transition"
              aria-label="Open chat"
            >
              <MessageCircle size={18} />
            </button>

            <button
              onClick={() => submit()}
              disabled={loading || !text.trim()}
              aria-label="Search"
              className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-smart hover:bg-smart-dark text-white transition disabled:opacity-40 focus:outline-none focus-visible:ring-2 focus-visible:ring-smart"
            >
              {loading ? (
                <Loader2 size={20} className="animate-spin" />
              ) : (
                <ArrowRight size={20} />
              )}
            </button>
          </div>
        </motion.div>

        {/* Quick picks */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="mt-5 flex flex-wrap justify-center gap-2"
        >
          <span className="text-xs text-ink/40 self-center mr-1">Try:</span>
          {quickPicks.map((qp) => (
            <button
              key={qp.label}
              onClick={() => submit(qp.intent)}
              disabled={loading}
              className="rounded-full px-3.5 py-1.5 text-sm bg-white/70 text-ink/60 ring-1 ring-black/5 hover:ring-smart/40 hover:text-ink transition disabled:opacity-40"
            >
              {qp.label}
            </button>
          ))}
        </motion.div>

        {/* AI badge */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-6 inline-flex items-center gap-1.5 text-xs text-ink/35"
        >
          <Sparkles size={12} />
          <span>Powered by AI · 10-min delivery</span>
        </motion.div>
      </div>
    </section>
  );
}
