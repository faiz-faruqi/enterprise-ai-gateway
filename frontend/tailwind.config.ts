import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        serif: ["DM Serif Display", "Georgia", "serif"],
        mono: ["DM Mono", "Menlo", "monospace"],
        sans: ["Instrument Sans", "Inter", "sans-serif"],
      },
      colors: {
        ink: {
          DEFAULT: "#1a1814",
          2: "#3d3a34",
          3: "#6b6760",
          4: "#9c9890",
        },
        paper: "#faf9f6",
        rule: "#dedad2",
        "rule-light": "#edeae4",
        accent: {
          DEFAULT: "#1d4e89",
          light: "#e8f0f9",
          mid: "#2e6ab4",
        },
        teal: {
          DEFAULT: "#0f6e56",
          light: "#e1f5ee",
        },
        amber: {
          DEFAULT: "#854f0b",
          light: "#faeeda",
        },
        coral: {
          DEFAULT: "#993c1d",
          light: "#faece7",
        },
      },
    },
  },
  plugins: [],
};

export default config;
