import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: { 
    extend: {
      keyframes: {
        wiggle: {
          '0%, 100%': { transform: 'rotate(-1.5deg)' },
          '50%': { transform: 'rotate(1.5deg)' },
        }
      },
      animation: {
        wiggle: 'wiggle 0.25s ease-in-out infinite',
      }
    } 
  },
  plugins: [],
} satisfies Config;
