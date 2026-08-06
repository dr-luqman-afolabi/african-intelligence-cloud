import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // Sampled from the AIC logo rather than chosen by eye. The mark is built
      // from navy (~#002050, its dominant colour) and green (~#0A8A48); it
      // contains no gold or red, so those are kept only for the flag accent
      // strip and are no longer used to theme the interface.
      colors: {
        aic: {
          // Navy — the primary brand colour. `dark` was #0B1220, effectively
          // black, which read as a generic dark UI and clashed with the logo's
          // navy. It is now the brand navy itself.
          navy: "#0A2A5E",
          "navy-deep": "#061B3D",
          "navy-light": "#14417F",
          dark: "#0A2A5E",

          green: "#0A7C46",
          "green-light": "#12A15C",
          "green-dark": "#055C33",

          // The teal-blue of the logo's orbit arc — used sparingly for
          // secondary accents so the palette isn't only navy and green.
          blue: "#1C6FA8",
          "blue-light": "#2E8CC9",

          // Retained for the pan-African accent strip only.
          gold: "#FFC20E",
          red: "#CE1126",

          slate: "#132A4A",
          muted: "#5A6B85",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      backgroundImage: {
        // Navy, green and the arc's blue — the logo's own three colours —
        // replacing the green/gold/red wash, which shared nothing with the mark.
        "aic-hero":
          "radial-gradient(circle at 18% 15%, rgba(10,42,94,0.14), transparent 42%), radial-gradient(circle at 82% 5%, rgba(18,161,92,0.13), transparent 38%), radial-gradient(circle at 88% 82%, rgba(28,111,168,0.11), transparent 42%)",
        "aic-gradient": "linear-gradient(135deg, #061B3D 0%, #0A2A5E 45%, #0A7C46 100%)",
        "aic-gradient-soft": "linear-gradient(135deg, #0A2A5E 0%, #14417F 60%, #1C6FA8 100%)",
        "aic-card-glow": "linear-gradient(180deg, rgba(255,255,255,0.6), rgba(255,255,255,0))",
      },
      boxShadow: {
        // Shadows tinted navy rather than neutral grey, so depth reads as part
        // of the palette instead of a grey haze over it.
        card: "0 1px 2px rgba(10,42,94,0.05), 0 8px 24px -8px rgba(10,42,94,0.12)",
        "card-hover": "0 4px 12px rgba(10,42,94,0.08), 0 16px 40px -12px rgba(10,42,94,0.20)",
        glow: "0 0 0 1px rgba(10,124,70,0.10), 0 8px 30px -8px rgba(10,124,70,0.35)",
        "glow-navy": "0 0 0 1px rgba(10,42,94,0.10), 0 8px 30px -8px rgba(10,42,94,0.40)",
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
