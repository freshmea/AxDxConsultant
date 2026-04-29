import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#080b13",
        panel: "#101827",
        cyanline: "#5eead4",
        violetline: "#a78bfa",
      },
      boxShadow: {
        glow: "0 0 60px rgba(94, 234, 212, 0.18)",
      },
    },
  },
  plugins: [],
};

export default config;
