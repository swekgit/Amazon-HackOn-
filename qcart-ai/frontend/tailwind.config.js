/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#16161A",
        canvas: "#F6F5F2",
        smart: {
          DEFAULT: "#5B41F0",
          dark: "#4530c9",
          soft: "#ECE9FE",
        },
        fresh: {
          DEFAULT: "#0EA46E",
          soft: "#DCFCE7",
        },
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
      },
      fontFamily: {
        display: ['"Space Grotesk"', "system-ui", "sans-serif"],
        sans: ['"Inter"', "system-ui", "sans-serif"],
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
          "0%, 100%": { boxShadow: "0 0 20px rgba(91, 65, 240, 0.3)" },
          "50%": { boxShadow: "0 0 40px rgba(91, 65, 240, 0.6)" },
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
