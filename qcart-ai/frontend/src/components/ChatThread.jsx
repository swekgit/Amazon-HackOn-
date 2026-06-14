import { useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles } from "lucide-react";

export default function ChatThread({ messages, loading }) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  if (messages.length === 0 && !loading) return null;

  return (
    <div className="space-y-3">
      <AnimatePresence>
        {messages.map((msg, i) =>
          msg.role === "user" ? (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex justify-end"
            >
              <div className="max-w-[80%] rounded-2xl rounded-br-md bg-ink px-4 py-2.5 text-white text-sm">
                {msg.text}
              </div>
            </motion.div>
          ) : (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-start gap-2"
            >
              <Sparkles size={16} className="mt-0.5 shrink-0 text-smart" />
              <p className="max-w-[85%] font-display text-sm text-ink/90">{msg.text}</p>
            </motion.div>
          )
        )}
      </AnimatePresence>
      {loading && (
        <div className="flex items-center gap-2 text-ink/40">
          <Sparkles size={16} className="text-smart" />
          <div className="flex gap-1">
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="h-2 w-2 rounded-full bg-smart/50"
                animate={{ scale: [1, 1.3, 1] }}
                transition={{ repeat: Infinity, duration: 0.7, delay: i * 0.15 }}
              />
            ))}
          </div>
        </div>
      )}
      <div ref={endRef} />
    </div>
  );
}
