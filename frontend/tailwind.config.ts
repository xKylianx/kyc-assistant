import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "orange-primary": "#FF7900",
        orange: {
          DEFAULT: "#FF7900",
          50: "#FFF3E8",
          100: "#FFE1C2",
          500: "#FF7900",
          600: "#E56C00",
        },
        brand: {
          blue: "#4BB4E6",
          purple: "#9164CD",
          green: "#50BE87",
          pink: "#FFB4E6",
          yellow: "#FFDC00",
          gray: {
            dark: "#595959",
            DEFAULT: "#8F8F8F",
            light: "#D6D6D6",
          },
          black: "#000000",
        },
      },
      fontFamily: {
        sans: ["Helvetica Neue", "Helvetica", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;