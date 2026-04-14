import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./data/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      boxShadow: {
        panel:
          "0 0 0 1px rgba(255,255,255,0.05), 0 24px 80px rgba(0,0,0,0.45), 0 10px 35px rgba(24,94,255,0.10)"
      },
      colors: {
        ink: "#050816",
        panel: "#0b1120",
        "panel-soft": "#111827",
        accent: "#89b4ff",
        "accent-strong": "#4f8cff"
      },
      backgroundImage: {
        "hero-grid":
          "linear-gradient(rgba(137,180,255,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(137,180,255,0.08) 1px, transparent 1px)"
      }
    }
  },
  plugins: []
};

export default config;
