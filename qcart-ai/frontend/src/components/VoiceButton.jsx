import { useEffect, useRef, useState } from "react";
import { Mic, AlertCircle } from "lucide-react";

// Browser speech-to-text. Hides itself if the browser doesn't support it.
export default function VoiceButton({ onResult, theme, disabled }) {
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
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={toggle}
        disabled={disabled}
        aria-label="Speak your need"
        className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl ring-1 transition disabled:opacity-40 ${
          listening
            ? "animate-pulse bg-rose-600 text-white ring-rose-600"
            : error
            ? "bg-rose-50 text-rose-600 ring-rose-200"
            : "bg-white text-ink ring-black/10 hover:ring-smart"
        }`}
      >
        {error ? <AlertCircle size={18} /> : <Mic size={18} />}
      </button>

      {listening && (
        <span className="animate-fade-up text-xs font-medium text-ink/60">
          Listening…
        </span>
      )}

      {error && (
        <span className="animate-fade-up text-xs font-medium text-rose-600">
          Mic unavailable
        </span>
      )}
    </div>
  );
}