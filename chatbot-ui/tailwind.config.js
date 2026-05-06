/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'neon-blue': '#00f3ff',
        'neon-purple': '#bc13fe',
        'deep-black': '#050510',
        'glass-panel': 'rgba(255, 255, 255, 0.05)',
        'start-up': '#00ff9d',
        'loss-red': '#ff0055',
      },
      keyframes: {
        glow: {
          '0%, 100%': { filter: 'drop-shadow(0 0 5px rgba(0, 243, 255, 0.5))' },
          '50%': { filter: 'drop-shadow(0 0 20px rgba(0, 243, 255, 0.8))' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        blob: {
          "0%": {
            transform: "translate(0px, 0px) scale(1)",
          },
          "33%": {
            transform: "translate(30px, -50px) scale(1.1)",
          },
          "66%": {
            transform: "translate(-20px, 20px) scale(0.9)",
          },
          "100%": {
            transform: "translate(0px, 0px) scale(1)",
          },
        },
      },
      animation: {
        'glow': 'glow 2s ease-in-out infinite',
        'float': 'float 3s ease-in-out infinite',
        'blob': "blob 7s infinite",
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
