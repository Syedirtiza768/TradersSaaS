/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    screens: {
      'xs': '480px',
      'sm': '640px',
      'md': '768px',
      'lg': '1024px',
      'xl': '1280px',
      '2xl': '1536px',
    },
    extend: {
      colors: {
        brand: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          950: '#172554',
        },
        trader: {
          primary: '#1e40af',
          secondary: '#059669',
          accent: '#d97706',
          danger: '#dc2626',
          success: '#16a34a',
          warning: '#f59e0b',
          info: '#2563eb',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      fontSize: {
        'fluid-xs': 'clamp(0.694rem, 0.66rem + 0.17vw, 0.8rem)',
        'fluid-sm': 'clamp(0.8rem, 0.75rem + 0.25vw, 0.938rem)',
        'fluid-base': 'clamp(0.875rem, 0.825rem + 0.25vw, 1rem)',
        'fluid-lg': 'clamp(1rem, 0.925rem + 0.38vw, 1.2rem)',
        'fluid-xl': 'clamp(1.25rem, 1.1rem + 0.75vw, 1.563rem)',
        'fluid-2xl': 'clamp(1.5rem, 1.25rem + 1.25vw, 2rem)',
      },
      spacing: {
        'safe-bottom': 'env(safe-area-inset-bottom, 0px)',
        'safe-top': 'env(safe-area-inset-top, 0px)',
        'safe-left': 'env(safe-area-inset-left, 0px)',
        'safe-right': 'env(safe-area-inset-right, 0px)',
      },
    },
  },
  plugins: [],
};
