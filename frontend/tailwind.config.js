/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"VT323"', "monospace"],
        mono: ['"Press Start 2P"', "monospace"],
        pixel: ['"Press Start 2P"', "monospace"],
      },
      colors: {
        brand: {
          DEFAULT: "#e8c000",
          soft: "#f8d800",
          deep: "#b89000",
        },
        confirmed: "#38a832",
        candidate: "#e8c000",
        reported: "#e8c000",
        signal: "#e84040",
        poke: {
          bg: "#1a1f3d",
          panel: "#f0ece0",
          border: "#2c3060",
          dark: "#0f1428",
          blue: "#3060c8",
        },
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(245,158,11,0.25), 0 8px 40px -8px rgba(245,158,11,0.35)",
        "glow-green": "0 0 0 1px rgba(34,197,94,0.3), 0 8px 30px -8px rgba(34,197,94,0.4)",
        panel: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 24px 60px -30px rgba(0,0,0,0.8)",
        marker: "0 4px 14px -2px rgba(0,0,0,0.6), 0 0 0 4px rgba(2,6,23,0.55)",
      },
      backgroundImage: {
        "grid-faint":
          "linear-gradient(to right, rgba(148,163,184,0.06) 1px, transparent 1px), linear-gradient(to bottom, rgba(148,163,184,0.06) 1px, transparent 1px)",
        "radial-spot":
          "radial-gradient(60% 60% at 50% 0%, rgba(245,158,11,0.10) 0%, transparent 70%)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "marker-in": {
          "0%": { opacity: "0", transform: "translate(-50%, -50%) scale(0.4)" },
          "70%": { transform: "translate(-50%, -50%) scale(1.12)" },
          "100%": { opacity: "1", transform: "translate(-50%, -50%) scale(1)" },
        },
        "ping-ring": {
          "0%": { transform: "translate(-50%, -50%) scale(0.9)", opacity: "0.7" },
          "100%": { transform: "translate(-50%, -50%) scale(2.4)", opacity: "0" },
        },
        blink: { "0%, 100%": { opacity: "1" }, "50%": { opacity: "0.2" } },
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(400%)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.45s cubic-bezier(0.22,1,0.36,1) both",
        "marker-in": "marker-in 0.5s cubic-bezier(0.22,1,0.36,1) both",
        "ping-ring": "ping-ring 2s cubic-bezier(0,0,0.2,1) infinite",
        blink: "blink 1.1s steps(2, start) infinite",
        scan: "scan 3.5s linear infinite",
      },
    },
  },
  plugins: [],
};
