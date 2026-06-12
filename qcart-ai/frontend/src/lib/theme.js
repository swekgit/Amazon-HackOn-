// Maps urgency to an accent palette. Full class strings (not built dynamically)
// so Tailwind's scanner generates them.
export function themeFor(urgency) {
  if (urgency === "high") {
    return {
      urgent: true,
      btn: "bg-rose-600 hover:bg-rose-700",
      ring: "focus-visible:ring-rose-600",
      chip: "bg-rose-50 text-rose-700",
      dot: "bg-rose-600",
      label: "Care mode · essentials first",
    };
  }
  return {
    urgent: false,
    btn: "bg-smart hover:bg-smart-dark",
    ring: "focus-visible:ring-smart",
    chip: "bg-smart-soft text-smart-dark",
    dot: "bg-smart",
    label: "Moment-aware",
  };
}
