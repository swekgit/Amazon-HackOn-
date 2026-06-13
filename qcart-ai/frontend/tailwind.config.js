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
      },
      animation: {
        "fade-up": "fade-up 0.45s cubic-bezier(0.22,1,0.36,1) both",
        "pop-in": "pop-in 0.3s ease-out both",
      },
    },
  },
  plugins: [],
};
