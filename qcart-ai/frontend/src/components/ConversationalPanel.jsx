import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Sparkles, ArrowRight, Loader2 } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";

const QUICK_ACTIONS = [
  "Make it premium",
  "Keep under ₹500",
  "Remove sugary drinks",
  "Add snacks for kids",
];

export default function ConversationalPanel() {
  const { messages, sendPreview, loading, setChatOpen, hasPreview, previewCart, previewSubtotal, confirmPreview, discardPreview } = useApp();
  const [text, setText] = useState("");
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const submit = (value) => {
    const v = (value ?? text).trim();
    if (!v || loading) return;
    sendPreview(v);
    setText("");
  };

  return (
    <>
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={() => setChatOpen(false)}
        className="fixed inset-0 z-40 bg-black/20"
      />

      {/* Panel */}
      <motion.div
        initial={{ opacity: 0, y: 30, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 30, scale: 0.95 }}
        transition={{ type: "spring", damping: 25, stiffness: 300 }}
        className="fixed bottom-20 right-4 sm:right-6 z-40 w-[calc(100%-2rem)] max-w-sm rounded-2xl glass shadow-2xl ring-1 ring-black/10 flex flex-col"
        style={{ maxHeight: "65vh" }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-black/5">
          <div className="flex items-center gap-2">
            <Sparkles size={16} className="text-smart" />
            <span className="font-display font-semibold text-sm">AI Shopping Assistant</span>
          </div>
          <button onClick={() => setChatOpen(false)} className="p-1.5 rounded-lg hover:bg-black/5 transition">
            <X size={16} />
          </button>
        </div>

        {/* Messages */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3 min-h-[200px]">
          {messages.length === 0 && (
            <div className="text-center py-8">
              <Sparkles size={24} className="mx-auto text-smart/40 mb-2" />
              <p className="text-sm text-ink/40">Tell me what you need!</p>
              <p className="text-xs text-ink/30 mt-1">e.g. "Movie night for 4" or "Make it cheaper"</p>
            </div>
          )}
          <AnimatePresence>
            {messages.map((msg, i) =>
              msg.role === "user" ? (
                <motion.div key={i} initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} className="flex justify-end">
                  <div className="max-w-[80%] rounded-2xl rounded-br-md bg-ink px-3 py-2 text-sm text-white">
                    {msg.text}
                  </div>
                </motion.div>
              ) : (
                <motion.div key={i} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className="flex items-start gap-2">
                  <Sparkles size={14} className="mt-0.5 shrink-0 text-smart" />
                  <p className="text-sm text-ink/80">{msg.text}</p>
                </motion.div>
              )
            )}
          </AnimatePresence>
          {loading && (
            <div className="flex items-center gap-2 text-ink/40">
              <Sparkles size={14} className="text-smart" />
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <motion.div key={i} className="h-1.5 w-1.5 rounded-full bg-smart/60"
                    animate={{ scale: [1, 1.4, 1] }}
                    transition={{ repeat: Infinity, duration: 0.8, delay: i * 0.15 }} />
                ))}
              </div>
            </div>
          )}
        </div>

        {hasPreview && (
          <div className="mx-3 mb-2 rounded-xl border border-smart/20 bg-white/80 p-3">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-xs font-semibold text-smart-dark">
                Proposed cart · {previewCart.length} item{previewCart.length > 1 ? "s" : ""}
              </span>
              <span className="text-xs font-semibold text-ink">₹{previewSubtotal}</span>
            </div>
            <div className="max-h-28 space-y-1 overflow-y-auto">
              {previewCart.map((it) => (
                <div key={it.id} className="flex items-center justify-between text-xs text-ink/70">
                  <span className="truncate pr-2">{it.quantity}× {it.name}</span>
                  <span className="shrink-0">₹{it.price * it.quantity}</span>
                </div>
              ))}
            </div>
            <div className="mt-3 flex gap-2">
              <button
                onClick={confirmPreview}
                disabled={loading}
                className="flex-1 rounded-lg bg-smart py-2 text-sm font-medium text-white transition disabled:opacity-40"
              >
                Add to cart
              </button>
              <button
                onClick={discardPreview}
                disabled={loading}
                className="rounded-lg px-3 text-sm text-ink/60 transition hover:bg-black/5 disabled:opacity-40"
              >
                Discard
              </button>
            </div>
          </div>
        )}

        {/* Quick actions */}
        <div className="px-4 pb-2 flex flex-wrap gap-1.5">
          {QUICK_ACTIONS.map((action) => (
            <button key={action} onClick={() => submit(action)} disabled={loading}
              className="rounded-full px-2.5 py-1 text-[11px] bg-smart-soft text-smart-dark hover:bg-smart/10 transition disabled:opacity-40">
              {action}
            </button>
          ))}
        </div>

        {/* Input */}
        <div className="px-3 pb-3">
          <div className="flex items-center gap-2 rounded-xl bg-white/80 p-1.5 pl-3 ring-1 ring-black/10">
            <input
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()}
              placeholder="Refine your cart..."
              className="min-w-0 flex-1 bg-transparent py-1.5 text-sm text-ink placeholder:text-ink/30 focus:outline-none"
            />
            <button
              onClick={() => submit()}
              disabled={loading || !text.trim()}
              className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-smart text-white transition disabled:opacity-40"
            >
              {loading ? <Loader2 size={14} className="animate-spin" /> : <ArrowRight size={14} />}
            </button>
          </div>
        </div>
      </motion.div>
    </>
  );
}
