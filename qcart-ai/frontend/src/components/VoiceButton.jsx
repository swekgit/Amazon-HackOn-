import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Mic } from "lucide-react";

export default function VoiceButton({ onResult, disabled }) {
  const [supported, setSupported] = useState(false);
  const [listening, setListening] = useState(false);
  const recRef = useRef(null);

  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;
    setSupported(true);
    const rec = new SR();
    rec.lang = "en-IN";
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    rec.onresult = (e) => onResult(e.results[0][0].transcript);
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);
    recRef.current = rec;
  }, [onResult]);

  if (!supported) return null;

  const toggle = () => {
    if (listening) {
      recRef.current.stop();
    } else {
      setListening(true);
      recRef.current.start();
    }
  };

  return (
    <div className="relative">
      {/* Pulse rings when listening */}
      {listening && (
        <>
          <motion.div
            className="absolute inset-0 rounded-xl bg-rose-500/30"
            animate={{ scale: [1, 1.5], opacity: [0.5, 0] }}
            transition={{ repeat: Infinity, duration: 1.2 }}
          />
          <motion.div
            className="absolute inset-0 rounded-xl bg-rose-500/20"
            animate={{ scale: [1, 1.3], opacity: [0.4, 0] }}
            transition={{ repeat: Infinity, duration: 1.2, delay: 0.3 }}
          />
        </>
      )}
      <motion.button
        onClick={toggle}
        disabled={disabled}
        whileTap={{ scale: 0.95 }}
        aria-label="Speak your need"
        className={`relative grid h-11 w-11 shrink-0 place-items-center rounded-xl ring-1 transition disabled:opacity-40 ${
          listening
            ? "bg-rose-600 text-white ring-rose-600"
            : "bg-white text-ink ring-black/10 hover:ring-smart"
        }`}
      >
        <Mic size={18} />
      </motion.button>
    </div>
  );
}
