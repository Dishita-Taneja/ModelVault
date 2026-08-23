/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        void: '#070A12',
        charcoal: '#0B0F19',
        panel: '#111827',
        surface: '#151D2F',
        surfaceHover: '#1C273E',
        socBorder: '#1F2B3F',
        socBorderLight: '#2D3D58',
        electricRed: '#EF4444',
        electricRedGlow: 'rgba(239, 68, 68, 0.2)',
        amberGlow: 'rgba(245, 158, 11, 0.2)',
        emeraldGlow: 'rgba(16, 185, 129, 0.2)',
        cyberCyan: '#06B6D4',
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"Fira Code"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        'glow-red': '0 0 20px -3px rgba(239, 68, 68, 0.35)',
        'glow-amber': '0 0 20px -3px rgba(245, 158, 11, 0.35)',
        'glow-cyan': '0 0 20px -3px rgba(6, 182, 212, 0.35)',
        'card-subtle': '0 4px 20px -2px rgba(0, 0, 0, 0.6)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'shimmer': 'shimmer 2s infinite linear',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
      },
    },
  },
  plugins: [],
};
