import { useEffect, useRef, useState } from "react";
import { Mic } from "lucide-react";

// Browser speech-to-text. Hides itself if the browser doesn't support it.
export default function VoiceButton({ onResult, theme, disabled }) {
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
    <button
      onClick={toggle}
      disabled={disabled}
      aria-label="Speak your need"
      className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl ring-1 transition disabled:opacity-40 ${
        listening ? "bg-rose-600 text-white ring-rose-600 animate-pulse" : "bg-white text-ink ring-black/10 hover:ring-smart"
      }`}
    >
      <Mic size={18} />
    </button>
  );
}
