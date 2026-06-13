import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Mic } from "lucide-react";

export default function VoiceButton({ onResult, disabled }) {
  const [supported, setSupported] = useState(false);
  const [status, setStatus] = useState("idle"); // idle | listening | error
  const recRef = useRef(null);
  const resetTimerRef = useRef(null);

  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;

    setSupported(true);

    const rec = new SR();
    rec.lang = "en-IN";
    rec.interimResults = false;
    rec.maxAlternatives = 1;

    rec.onstart = () => {
      setStatus("listening");
    };

    rec.onresult = (e) => {
      const text = e.results?.[0]?.[0]?.transcript?.trim();
      if (text) onResult(text);
    };

    rec.onend = () => {
      setStatus((s) => (s === "error" ? s : "idle"));
    };

    rec.onerror = (e) => {
      if (
        e.error === "not-allowed" ||
        e.error === "service-not-allowed" ||
        e.error === "audio-capture"
      ) {
        setStatus("error");

        clearTimeout(resetTimerRef.current);
        resetTimerRef.current = setTimeout(() => {
          setStatus("idle");
        }, 1800);
      } else {
        setStatus("idle");
      }
    };

    recRef.current = rec;

    return () => {
      clearTimeout(resetTimerRef.current);
      rec.stop?.();
    };
  }, [onResult]);

  if (!supported) return null;

  const toggle = () => {
    if (!recRef.current || disabled) return;

    if (status === "listening") {
      recRef.current.stop();
      return;
    }

    try {
      setStatus("listening");
      recRef.current.start();
    } catch {
      setStatus("idle");
    }
  };

  const listening = status === "listening";
  const error = status === "error";

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
