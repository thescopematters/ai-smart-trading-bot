/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'main-bg': '#F5F6F8',
        'sidebar-bg': '#FFFFFF',
        'card-bg': '#FFFFFF',
        'primary-purple': '#6366F1',
        'hover-purple': '#5558E8',
        'light-purple': '#EEF2FF',
        'text-primary': '#111827',
        'text-secondary': '#6B7280',
        'text-muted': '#9CA3AF',
        'border-light': '#E5E7EB',
        'card-border': '#ECEFF3',
        'sidebar-active': '#F3F4F6',
        // Keeping legacy colors for compatibility if needed, but we should phase them out
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
        'slide-in': {
            from: { opacity: '0', transform: 'translateY(8px)' },
            to:   { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'glow': 'glow 2s ease-in-out infinite',
        'float': 'float 3s ease-in-out infinite',
        'blob': "blob 7s infinite",
        'slide-in': 'slide-in 0.2s ease-out',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
