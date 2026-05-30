import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/lib/**/*.{js,ts}",
  ],
  theme: {
    extend: {
      colors: {
        indigo: {
          50: "#eef2ff",
          100: "#e0e7ff",
          400: "#818cf8",
          600: "#4f46e5",
          700: "#4338ca",
          800: "#3730a3",
        },
      },
    },
  },
  plugins: [],
};

export default config;
