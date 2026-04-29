/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#09090f",
          secondary: "#0f0f1a",
          card: "#12121f",
          border: "#1e1e30",
        },
        accent: {
          green: "#00e676",
          red: "#ff3d71",
          yellow: "#ffca28",
          blue: "#448aff",
          purple: "#7c4dff",
          neutral: "#546e7a",
        },
        text: {
          primary: "#e8eaf6",
          secondary: "#9fa8da",
          muted: "#546e7a",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "Consolas", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
