/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#6366f1', // indigo-500
          dark: '#4338ca',   // indigo-700
          light: '#a5b4fc',  // indigo-300
        },
        accent: {
          DEFAULT: '#10b981', // emerald-500
          dark: '#047857',   // emerald-700
          light: '#6ee7b7',  // emerald-300
        },
        background: '#f9fafb', // gray-50
        surface: '#ffffff',
        text: {
          DEFAULT: '#334155', // slate-700
          light: '#64748b',   // slate-400
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
      },
    },
  },
  plugins: [],
}
