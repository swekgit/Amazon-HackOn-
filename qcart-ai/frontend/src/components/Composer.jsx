import { useState } from "react";
import { ArrowRight, Loader2 } from "lucide-react";
import VoiceButton from "./VoiceButton.jsx";

export default function Composer({ onSend, loading, theme, placeholder }) {
  const [text, setText] = useState("");

  const submit = (value) => {
    const v = (value ?? text).trim();
    if (!v || loading) return;
    onSend(v);
    setText("");
  };

  return (
    <div className="flex items-center gap-2 rounded-2xl bg-white p-2 pl-5 ring-1 ring-black/10 shadow-sm focus-within:ring-2 focus-within:ring-smart">
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && submit()}
        placeholder={placeholder}
        className="min-w-0 flex-1 bg-transparent py-2.5 text-ink placeholder:text-ink/35 focus:outline-none"
      />
      <VoiceButton onResult={(t) => submit(t)} theme={theme} disabled={loading} />
      <button
        onClick={() => submit()}
        disabled={loading || !text.trim()}
        aria-label="Send"
        className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl text-white transition disabled:opacity-40 focus:outline-none focus-visible:ring-2 ${theme.btn} ${theme.ring}`}
      >
        {loading ? <Loader2 size={20} className="animate-spin" /> : <ArrowRight size={20} />}
      </button>
    </div>
  );
}
