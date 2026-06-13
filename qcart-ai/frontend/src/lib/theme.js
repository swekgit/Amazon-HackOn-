// Maps urgency to an accent palette. Full class strings (not built dynamically)
// so Tailwind's scanner generates them.
export function themeFor(urgency) {
  if (urgency === "high") {
    return {
      urgent: true,

      // Smooth transitions when switching modes
      btn: "bg-rose-600 hover:bg-rose-700 transition-colors duration-500",
      ring: "focus-visible:ring-rose-600 transition-colors duration-500",

      chip: "bg-rose-50 text-rose-700 transition-colors duration-500",
      dot: "bg-rose-600 transition-colors duration-500",

      label: "Care mode · essentials first",
    };
  }

  return {
    urgent: false,

    // Smooth transitions when returning to normal mode
    btn: "bg-smart hover:bg-smart-dark transition-colors duration-500",
    ring: "focus-visible:ring-smart transition-colors duration-500",

    chip: "bg-smart-soft text-smart-dark transition-colors duration-500",
    dot: "bg-smart transition-colors duration-500",

    label: "Moment-aware",
  };
}
