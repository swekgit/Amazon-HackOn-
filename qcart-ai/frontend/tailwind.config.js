/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // ─── QCart Design System Tokens ────────────────────────────
        brand: {
          DEFAULT: "#FF7A1A",
          deep: "#E85D04",
          soft: "#FFE7D3",
        },
        cta: {
          DEFAULT: "#FFB703",
          deep: "#F59E0B",
        },
        ink: "#17161B",
        muted: "#6E6B76",
        line: "#ECEAE6",
        canvas: "#FAFAF7",
        card: "#FFFFFF",
        green: {
          DEFAULT: "#0E9F6E",
          soft: "#E3F7EE",
        },
        blue: {
          DEFAULT: "#2D7FF9",
          soft: "#E7F0FE",
        },
        rose: {
          DEFAULT: "#E5484D",
          soft: "#FDE8E8",
        },

        // ─── Backwards Compatibility Aliases ──────────────────────
        // smart → brand (existing components use smart extensively)
        smart: {
          DEFAULT: "#FF7A1A",
          dark: "#E85D04",
          soft: "#FFE7D3",
        },
        // fresh → green (existing components use fresh)
        fresh: {
          DEFAULT: "#0E9F6E",
          soft: "#E3F7EE",
        },

        // ─── Legacy tokens (still used by some components) ────────
        amazon: {
          DEFAULT: "#FF9900",
          dark: "#131921",
          light: "#FEBD69",
          blue: "#232F3E",
        },
        prime: {
          DEFAULT: "#00A8E1",
          dark: "#007EB5",
        },
        amazonYellow: "#FFD814",
        headerBg: "#DFF4FF",
        border: "#E5E7EB",
      },
      fontFamily: {
        display: ['"Space Grotesk"', "system-ui", "sans-serif"],
        body: ['"Inter"', "system-ui", "sans-serif"],
        sans: ['"Inter"', "system-ui", "sans-serif"],
      },
      borderRadius: {
        card: "18px",
        panel: "24px",
        pill: "999px",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pop-in": {
          "0%": { opacity: "0", transform: "scale(0.96)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "pulse-ring": {
          "0%": { transform: "scale(1)", opacity: "0.6" },
          "100%": { transform: "scale(1.8)", opacity: "0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-6px)" },
        },
        glow: {
          "0%, 100%": { boxShadow: "0 0 20px rgba(255, 122, 26, 0.3)" },
          "50%": { boxShadow: "0 0 40px rgba(255, 122, 26, 0.5)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.45s cubic-bezier(0.22,1,0.36,1) both",
        "pop-in": "pop-in 0.3s ease-out both",
        shimmer: "shimmer 2s ease-in-out infinite",
        "pulse-ring": "pulse-ring 1.5s ease-out infinite",
        float: "float 3s ease-in-out infinite",
        glow: "glow 2s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
