import { Sparkles, Wallet, HeartPulse, Users } from "lucide-react";

const ACTIONS = [
  {
    label: "Cheaper",
    prompt: "make it cheaper",
    icon: Wallet,
  },
  {
    label: "Premium",
    prompt: "make it premium",
    icon: Sparkles,
  },
  {
    label: "Healthier",
    prompt: "make it healthier",
    icon: HeartPulse,
  },
  {
    label: "More people",
    prompt: "add more for more people",
    icon: Users,
  },
];

export default function QuickActions({ onSend, disabled, theme }) {
  return (
    <div className="animate-fade-up">
      <div className="flex flex-wrap gap-2">
        {ACTIONS.map((action) => {
          const Icon = action.icon;

          return (
            <button
              key={action.label}
              type="button"
              disabled={disabled}
              onClick={() => onSend(action.prompt)}
              className={`inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1.5 text-sm font-medium text-ink ring-1 ring-black/10 transition hover:ring-smart disabled:cursor-not-allowed disabled:opacity-50 ${theme.ring}`}
            >
              <Icon className="h-3.5 w-3.5" />
              {action.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}