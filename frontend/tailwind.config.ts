import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        aic: {
          green: "#006B3C",
          "green-light": "#0D9457",
          "green-dark": "#004D2A",
          gold: "#FFC20E",
          red: "#CE1126",
          dark: "#0B1220",
          slate: "#111827",
          muted: "#64748B",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      backgroundImage: {
        "aic-hero": "radial-gradient(circle at 20% 20%, rgba(0,107,60,0.16), transparent 40%), radial-gradient(circle at 85% 0%, rgba(255,194,14,0.14), transparent 35%), radial-gradient(circle at 90% 80%, rgba(206,17,38,0.10), transparent 40%)",
        "aic-gradient": "linear-gradient(135deg, #006B3C 0%, #0D9457 50%, #0B1220 100%)",
        "aic-card-glow": "linear-gradient(180deg, rgba(255,255,255,0.6), rgba(255,255,255,0))",
      },
      boxShadow: {
        card: "0 1px 2px rgba(15,23,42,0.04), 0 8px 24px -8px rgba(15,23,42,0.10)",
        "card-hover": "0 4px 12px rgba(15,23,42,0.06), 0 16px 40px -12px rgba(15,23,42,0.18)",
        glow: "0 0 0 1px rgba(0,107,60,0.08), 0 8px 30px -8px rgba(0,107,60,0.35)",
      },
      keyframes: {
        "fade-in": { "0%": { opacity: "0", transform: "translateY(8px)" }, "100%": { opacity: "1", transform: "translateY(0)" } },
        "fade-in-up": { "0%": { opacity: "0", transform: "translateY(16px)" }, "100%": { opacity: "1", transform: "translateY(0)" } },
        shimmer: { "0%": { backgroundPosition: "-200% 0" }, "100%": { backgroundPosition: "200% 0" } },
        float: { "0%, 100%": { transform: "translateY(0)" }, "50%": { transform: "translateY(-6px)" } },
      },
      animation: {
        "fade-in": "fade-in 0.5s ease-out both",
        "fade-in-up": "fade-in-up 0.6s cubic-bezier(0.16,1,0.3,1) both",
        shimmer: "shimmer 2s linear infinite",
        float: "float 6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
