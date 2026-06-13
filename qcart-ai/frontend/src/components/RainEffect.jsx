import { useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useApp } from "../state/AppContext.jsx";

export default function RainEffect() {
  const { themeName } = useApp();

  const drops = useMemo(() => {
    return Array.from({ length: 50 }, (_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      height: `${10 + Math.random() * 20}px`,
      duration: `${0.5 + Math.random() * 1}s`,
      delay: `${Math.random() * 2}s`,
      opacity: 0.2 + Math.random() * 0.3,
    }));
  }, []);

  if (themeName !== "rainy") return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 pointer-events-none z-0 overflow-hidden"
      >
        {drops.map((drop) => (
          <div
            key={drop.id}
            className="absolute top-0 rain-drop"
            style={{
              left: drop.left,
              height: drop.height,
              opacity: drop.opacity,
              animation: `rain-fall ${drop.duration} ${drop.delay} linear infinite`,
              willChange: "transform",
            }}
          />
        ))}
        <style>{`
          @keyframes rain-fall {
            0% { transform: translateY(-10px); opacity: 0; }
            10% { opacity: 1; }
            90% { opacity: 1; }
            100% { transform: translateY(100vh); opacity: 0; }
          }
        `}</style>
      </motion.div>
    </AnimatePresence>
  );
}
