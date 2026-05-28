/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["'DM Mono'", "monospace"],
        body: ["'IBM Plex Sans'", "sans-serif"],
        mono: ["'DM Mono'", "monospace"],
      },
      colors: {
        bg: {
          base:    "#080C12",
          surface: "#0D1420",
          card:    "#111926",
          hover:   "#161F2E",
          border:  "#1C2A3A",
        },
        accent: {
          green:  "#00E5A0",
          red:    "#FF4D6A",
          amber:  "#FFAB40",
          blue:   "#3D9AFF",
          purple: "#A78BFA",
        },
        text: {
          primary:   "#E8EDF5",
          secondary: "#7A8FA8",
          muted:     "#3D5068",
        },
      },
      backgroundImage: {
        "grid-pattern": "linear-gradient(rgba(0,229,160,.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,229,160,.03) 1px, transparent 1px)",
      },
      backgroundSize: {
        "grid": "48px 48px",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "slide-up":   "slideUp .4s ease forwards",
        "fade-in":    "fadeIn .5s ease forwards",
        "ticker":     "ticker 30s linear infinite",
      },
      keyframes: {
        slideUp:  { from: { opacity: 0, transform: "translateY(16px)" }, to: { opacity: 1, transform: "translateY(0)" } },
        fadeIn:   { from: { opacity: 0 }, to: { opacity: 1 } },
        ticker:   { from: { transform: "translateX(0)" }, to: { transform: "translateX(-50%)" } },
      },
    },
  },
  plugins: [],
};