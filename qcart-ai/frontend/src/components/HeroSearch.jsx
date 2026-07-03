import { useState, useEffect, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Loader2, MessageCircle, Search } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import { fetchMoments } from "../api/client.js";
import VoiceButton from "./VoiceButton.jsx";

const DEFAULT_PLACEHOLDERS = [
  "Rainy Day comfort food",
  "Guests at Home in 1 hour",
  "Movie Night for 4",
  "Study Session fuel",
  "Late Night Cravings",
  "Morning breakfast",
  "Feeling under the weather",
];

const FALLBACK_CHIPS = [
  { id: "movie-night", emoji: "🍿", label: "Movie Night", intent: "Movie night for 4" },
  { id: "guests-at-home", emoji: "🏠", label: "Guests Coming", intent: "Guests arriving in 1 hour" },
  { id: "rainy-day", emoji: "🌧️", label: "Rainy Day", intent: "Rainy day comfort food" },
  { id: "fever-care", emoji: "🤒", label: "Fever Care", intent: "I have fever and feel weak" },
  { id: "late-night-cravings", emoji: "🌙", label: "Late Night", intent: "Late night snack cravings" },
];

export default function HeroSearch({ onSubmit }) {
  const { send, sendMoment, loading, setChatOpen, customerId, city } = useApp();
  const [text, setText] = useState("");
  const [placeholderIdx, setPlaceholderIdx] = useState(0);
  const [displayedPlaceholder, setDisplayedPlaceholder] = useState("");
  const [isTyping, setIsTyping] = useState(true);
  const [placeholders, setPlaceholders] = useState(DEFAULT_PLACEHOLDERS);
  const [quickPicks, setQuickPicks] = useState(FALLBACK_CHIPS);
  const inputRef = useRef(null);

  useEffect(() => {
    fetchMoments({ customerId, city, pool: "missions" })
      .then((data) => {
        const moments = (data.moments || []).slice(0, 5);
        if (!moments.length) return;
        setQuickPicks(moments);
        setPlaceholders(moments.map((m) => m.intent));
        setPlaceholderIdx(0);
        setIsTyping(true);
      })
      .catch(() => setQuickPicks(FALLBACK_CHIPS));
  }, [customerId, city]);

  useEffect(() => {
    if (!placeholders.length) return;
    const current = placeholders[placeholderIdx];
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
            setPlaceholderIdx((i) => (i + 1) % placeholders.length);
            setIsTyping(true);
            return "";
          }
          return prev.slice(0, -1);
        });
      }, 30);
    }
    return () => clearInterval(timer);
  }, [placeholderIdx, isTyping, placeholders]);

  // Submit logic — UNCHANGED except onSubmit callback
  const submit = useCallback(
    (value) => {
      const v = (value ?? text).trim();
      if (!v || loading) return;
      onSubmit?.(v);
      send(v);
      setText("");
    },
    [text, loading, send, onSubmit]
  );

  const handleChipSelect = useCallback(
    (moment) => {
      onSubmit?.(moment.intent || moment.label);
      if (moment.id) {
        sendMoment(moment);
      } else {
        send(moment.intent);
      }
    },
    [onSubmit, sendMoment, send]
  );

  return (
    <section
      id="hero-search"
      className="relative overflow-hidden"
      style={{
        paddingTop: "5rem",
        paddingBottom: "4.5rem",
      }}
    >
      {/* Warm Amazon-Now grocery-commerce background */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "linear-gradient(180deg, #F7F1E6 0%, #F8F3EA 60%, #FFFFFF 100%)",
        }}
      />

      <div className="relative max-w-4xl mx-auto px-4 sm:px-6 text-center">
        {/* ── Top badge ─────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        >
          <span
            className="inline-block rounded-full px-5 py-2 text-sm font-semibold tracking-wide"
            style={{ backgroundColor: "#F5E3D0", color: "#F97316" }}
          >
            MOMENT-AWARE QUICK COMMERCE
          </span>
        </motion.div>

        {/* ── Headline ──────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.08, ease: [0.22, 1, 0.36, 1] }}
          className="mt-6"
        >
          <h1 className="font-display font-extrabold leading-[1.1] tracking-tight text-4xl sm:text-5xl md:text-6xl">
            <span style={{ color: "#111827" }}>
              Tell us your moment.
            </span>
            <br />
            <span style={{ color: "#F97316" }}>
              AI builds your cart.
            </span>
          </h1>
        </motion.div>

        {/* ── Subheading ────────────────────────────────────── */}
        <motion.p
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.16, ease: [0.22, 1, 0.36, 1] }}
          className="mt-6 text-base sm:text-xl mx-auto"
          style={{ color: "#4B5563", maxWidth: "600px" }}
        >
          A checkout-ready cart in seconds —
          <br className="hidden sm:block" />
          delivered in 10 minutes.
        </motion.p>

        {/* ── Search bar ────────────────────────────────────── */}
        {/* ALL FUNCTIONALITY PRESERVED — only visual styling updated */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.24, ease: [0.22, 1, 0.36, 1] }}
          className="mt-10 mx-auto"
          style={{ maxWidth: "760px" }}
        >
          <div className="relative flex items-center gap-1 sm:gap-2 rounded-[2rem] sm:rounded-full bg-white p-1.5 sm:p-2 pl-4 sm:pl-6 shadow-lg focus-within:ring-2 focus-within:ring-orange-300 transition-all w-full"
            style={{ border: "1px solid #E5E7EB" }}
          >
            <Search size={18} className="shrink-0 sm:w-5 sm:h-5" style={{ color: "#9CA3AF" }} />
            <div className="relative min-w-0 flex-1">
              <input
                ref={inputRef}
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && submit()}
                className="w-full bg-transparent py-2 sm:py-3 text-sm sm:text-base text-ink placeholder:text-transparent focus:outline-none"
                placeholder={displayedPlaceholder}
              />
              {/* Animated placeholder overlay — UNCHANGED */}
              {!text && (
                <div className="absolute inset-0 flex items-center pointer-events-none overflow-hidden">
                  <span className="text-sm sm:text-base whitespace-nowrap text-ellipsis" style={{ color: "#9CA3AF" }}>
                    {displayedPlaceholder}
                    <motion.span
                      animate={{ opacity: [1, 0] }}
                      transition={{ repeat: Infinity, duration: 0.8 }}
                      className="inline-block w-[1.5px] h-4 sm:w-0.5 sm:h-5 ml-0.5 align-middle"
                      style={{ backgroundColor: "#F9731680" }}
                    />
                  </span>
                </div>
              )}
            </div>

            {/* Voice button — shows transcript before sending */}
            <div className="shrink-0 scale-90 sm:scale-100 origin-right">
              <VoiceButton
                onResult={(t) => {
                  setText(t);
                  // Brief delay so user sees the recognized text
                  setTimeout(() => submit(t), 400);
                }}
                disabled={loading}
              />
            </div>

            {/* Chat button — FUNCTIONALITY UNCHANGED */}
            <button
              onClick={() => setChatOpen(true)}
              className="grid h-9 w-9 sm:h-11 sm:w-11 shrink-0 place-items-center rounded-full bg-white transition hover:bg-gray-50"
              style={{ border: "1px solid #E5E7EB" }}
              aria-label="Open chat"
            >
              <MessageCircle size={14} className="sm:w-4 sm:h-4" style={{ color: "#6B7280" }} />
            </button>

            {/* Submit button — FUNCTIONALITY UNCHANGED */}
            <button
              onClick={() => submit()}
              disabled={loading || !text.trim()}
              aria-label="Search"
              className="grid h-9 w-9 sm:h-11 sm:w-11 shrink-0 place-items-center rounded-full bg-amazonYellow hover:bg-yellow-400 text-ink transition disabled:opacity-40 focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-400"
            >
              {loading ? (
                <Loader2 size={16} className="animate-spin sm:w-[18px] sm:h-[18px]" />
              ) : (
                <ArrowRight size={16} className="sm:w-[18px] sm:h-[18px]" />
              )}
            </button>
          </div>
        </motion.div>

        {/* ── Quick pick chips ──────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.35 }}
          className="mt-6 flex flex-wrap justify-center gap-3 sm:gap-4"
        >
          {quickPicks.map((qp) => (
            <motion.button
              key={qp.id || qp.label}
              onClick={() => handleChipSelect(qp)}
              disabled={loading}
              whileHover={{ scale: 1.05, y: -2 }}
              whileTap={{ scale: 0.95 }}
              className="rounded-full bg-white px-5 sm:px-6 py-2.5 sm:py-3 text-sm font-medium text-gray-700 shadow-sm transition-all disabled:opacity-40 hover:shadow-md"
              style={{ border: "1px solid #E5E7EB" }}
            >
              {qp.emoji ? `${qp.emoji} ${qp.label}` : qp.label}
            </motion.button>
          ))}
        </motion.div>

        {/* "Powered by AI" line REMOVED per requirement */}
      </div>
    </section>
  );
}
