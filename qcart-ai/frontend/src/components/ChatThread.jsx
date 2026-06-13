import { Sparkles } from "lucide-react";

export default function ChatThread({ messages, loading }) {
  if (messages.length === 0) return null;

  return (
    <div className="space-y-3">
      {messages.map((msg, i) =>
        msg.role === "user" ? (
          <div key={i} className="flex justify-end">
            <div className="max-w-[80%] rounded-2xl rounded-br-md bg-ink px-4 py-2.5 text-white animate-pop-in">
              {msg.text}
            </div>
          </div>
        ) : (
          <div key={i} className="flex items-start gap-2 animate-fade-up">
            <Sparkles size={16} className="mt-1 shrink-0 text-smart" />
            <p className="max-w-[85%] font-display text-ink/90">{msg.text}</p>
          </div>
        )
      )}
      {loading && (
        <div className="flex items-center gap-2 text-ink/40">
          <Sparkles size={16} className="animate-pulse text-smart" />
          <span className="text-sm">thinking…</span>
        </div>
      )}
    </div>
  );
}
