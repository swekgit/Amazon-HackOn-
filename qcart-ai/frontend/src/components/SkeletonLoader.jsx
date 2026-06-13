export default function SkeletonLoader({ variant = "card", count = 1 }) {
  const items = Array.from({ length: count }, (_, i) => i);

  if (variant === "text") {
    return (
      <div className="space-y-2">
        {items.map((i) => (
          <div key={i} className="skeleton rounded h-4" style={{ width: `${60 + Math.random() * 30}%`, animationDelay: `${i * 150}ms` }} />
        ))}
      </div>
    );
  }

  if (variant === "image") {
    return (
      <div className="flex gap-3">
        {items.map((i) => (
          <div key={i} className="skeleton rounded-xl h-24 w-24 shrink-0" style={{ animationDelay: `${i * 150}ms` }} />
        ))}
      </div>
    );
  }

  if (variant === "product") {
    return (
      <div className="flex gap-3">
        {items.map((i) => (
          <div key={i} className="shrink-0 w-40 rounded-2xl bg-white/60 p-4 ring-1 ring-black/5 space-y-3" style={{ animationDelay: `${i * 150}ms` }}>
            <div className="skeleton rounded-xl h-16 w-full" />
            <div className="skeleton rounded h-3 w-3/4" />
            <div className="skeleton rounded h-3 w-1/2" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((i) => (
        <div key={i} className="skeleton rounded-2xl h-32 w-full" style={{ animationDelay: `${i * 150}ms` }} />
      ))}
    </div>
  );
}
