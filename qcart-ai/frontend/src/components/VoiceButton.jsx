import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Mic } from "lucide-react";

export default function VoiceButton({ onResult, onInterim, disabled }) {
  const [supported, setSupported] = useState(false);
  const [status, setStatus] = useState("idle"); // idle | listening | error
  const recRef = useRef(null);
  const resetTimerRef = useRef(null);

  // User intent: true between click-to-start and click-to-stop (or unmount).
  // Distinct from the actual "running" state so we can auto-restart on
  // spurious onend (silence timeouts) without stopping the session.
  const isListeningRef = useRef(false);
  // Actual running state, set between onstart/onend. Guards double start().
  const runningRef = useRef(false);
  // Accumulates final transcript segments across the session.
  const finalTranscriptRef = useRef("");

  // Keep latest callbacks in refs so the recognition object is created
  // only once (instead of every parent render).
  const onResultRef = useRef(onResult);
  const onInterimRef = useRef(onInterim);
  useEffect(() => {
    onResultRef.current = onResult;
    onInterimRef.current = onInterim;
  }, [onResult, onInterim]);

  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;

    setSupported(true);

    const rec = new SR();
    rec.lang = "en-IN";
    rec.continuous = true;
    rec.interimResults = true;
    rec.maxAlternatives = 1;

    rec.onstart = () => {
      runningRef.current = true;
      setStatus("listening");
    };

    rec.onresult = (e) => {
      let interim = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const res = e.results[i];
        const chunk = res[0]?.transcript ?? "";
        if (res.isFinal) {
          finalTranscriptRef.current =
            (finalTranscriptRef.current + " " + chunk).replace(/\s+/g, " ").trim();
        } else {
          interim += chunk;
        }
      }
      const live = (finalTranscriptRef.current + " " + interim)
        .replace(/\s+/g, " ")
        .trim();
      if (live) onInterimRef.current?.(live);
    };

    rec.onerror = (e) => {
      // Hard errors — actually give up and surface UI.
      if (
        e.error === "not-allowed" ||
        e.error === "service-not-allowed" ||
        e.error === "audio-capture"
      ) {
        isListeningRef.current = false;
        setStatus("error");
        clearTimeout(resetTimerRef.current);
        resetTimerRef.current = setTimeout(() => setStatus("idle"), 1800);
        return;
      }
      // Soft errors like "no-speech", "aborted", "network": don't die.
      // Let onend decide whether to restart (based on user intent).
    };

    rec.onend = () => {
      runningRef.current = false;

      // If the user still wants to be listening, this was a spurious end
      // (silence timeout, browser hiccup). Restart the same instance.
      if (isListeningRef.current) {
        try {
          rec.start();
        } catch {
          // InvalidStateError if it's already restarting — safe to ignore.
        }
        return;
      }

      // User stopped (or unmount). Submit whatever we collected.
      setStatus((s) => (s === "error" ? s : "idle"));
      const finalText = finalTranscriptRef.current.trim();
      finalTranscriptRef.current = "";
      if (finalText) onResultRef.current?.(finalText);
    };

    recRef.current = rec;

    return () => {
      clearTimeout(resetTimerRef.current);
      isListeningRef.current = false;
      try {
        rec.stop();
      } catch {
        // ignore
      }
    };
  }, []);

  if (!supported) return null;

  const toggle = () => {
    const rec = recRef.current;
    if (!rec || disabled) return;

    // Second click — stop and let onend submit the final transcript.
    if (isListeningRef.current) {
      isListeningRef.current = false;
      try {
        rec.stop();
      } catch {
        // ignore
      }
      return;
    }

    // First click — start a fresh session.
    isListeningRef.current = true;
    finalTranscriptRef.current = "";
    setStatus("listening");

    // Guard against double start(): calling start() while already running
    // throws InvalidStateError and kills the session.
    if (runningRef.current) return;

    try {
      rec.start();
    } catch {
      // Already starting/started — swallow and stay in listening state.
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
        aria-label={listening ? "Stop listening and search" : "Speak your need"}
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
