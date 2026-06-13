import { MISSIONS } from "../data/missions.js";

export default function MissionTiles({ onPick, disabled }) {
  return (
    <div className="flex flex-wrap gap-2">
      {MISSIONS.map((mi) => (
        <button
          key={mi.label}
          onClick={() => onPick(mi.intent)}
          disabled={disabled}
          className={`rounded-full px-3.5 py-2 text-sm ring-1 transition disabled:opacity-40 ${
            mi.urgent
              ? "bg-rose-50 text-rose-700 ring-rose-200 hover:ring-rose-400"
              : "bg-white text-ink/70 ring-black/10 hover:text-ink hover:ring-smart"
          }`}
        >
          {mi.label}
        </button>
      ))}
    </div>
  );
}
