/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: "#F6F7FB",
        panel: "#FFFFFF",
        muted: "#EEF2F6",
        border: "#E2E8F0",
        accent: "#2F6FED",
        "accent-soft": "#E8F0FF",
        text: "#0F172A",
        "text-muted": "#5B6475",
      },
      boxShadow: {
        soft: "0 10px 30px -18px rgba(15, 23, 42, 0.35)",
        card: "0 6px 18px -10px rgba(15, 23, 42, 0.25)",
      },
      borderRadius: {
        xl: "0.9rem",
        "2xl": "1.2rem",
      },
    },
  },
  plugins: [],
}
