import { motion } from "framer-motion";
import { Sparkles, X } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";

export default function CopilotFAB() {
  const { chatOpen, setChatOpen, cartOpen } = useApp();

  // Don't show when cart drawer is open
  if (cartOpen) return null;

  return (
    <div className="fixed bottom-6 right-6 z-30">
      {/* Hover label */}
      <motion.div
        initial={{ opacity: 0, x: 10 }}
        whileHover={{ opacity: 1, x: 0 }}
        className="absolute right-16 top-1/2 -translate-y-1/2 whitespace-nowrap rounded-lg bg-ink px-3 py-1.5 text-xs font-medium text-white shadow-lg pointer-events-none opacity-0"
      >
        QCart Copilot
      </motion.div>

      {/* Pulse rings */}
      {!chatOpen && (
        <>
          <motion.div
            className="absolute inset-0 rounded-full bg-smart/20"
            animate={{ scale: [1, 1.6], opacity: [0.4, 0] }}
            transition={{ repeat: Infinity, duration: 2, ease: "easeOut" }}
          />
          <motion.div
            className="absolute inset-0 rounded-full bg-smart/15"
            animate={{ scale: [1, 1.4], opacity: [0.3, 0] }}
            transition={{ repeat: Infinity, duration: 2, delay: 0.5, ease: "easeOut" }}
          />
        </>
      )}

      {/* Button */}
      <motion.button
        onClick={() => setChatOpen(!chatOpen)}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        animate={chatOpen ? {} : { boxShadow: ["0 0 20px rgba(91,65,240,0.3)", "0 0 40px rgba(91,65,240,0.5)", "0 0 20px rgba(91,65,240,0.3)"] }}
        transition={chatOpen ? {} : { repeat: Infinity, duration: 2 }}
        className={`relative grid h-14 w-14 place-items-center rounded-full shadow-xl transition-colors ${
          chatOpen
            ? "bg-ink text-white"
            : "bg-gradient-to-br from-smart to-smart-dark text-white"
        }`}
        aria-label={chatOpen ? "Close copilot" : "Open QCart Copilot"}
      >
        {chatOpen ? <X size={22} /> : <Sparkles size={22} />}
      </motion.button>
    </div>
  );
}
