/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cyber: {
          dark: '#12161f',        // Rich dark slate canvas background
          panel: '#1e2430',       // Rich dark slate obsidian panel surface
          subtle: '#161b26',      // Inner container dark fill
          border: '#2d3748',      // Metallic slate border
          grey: '#94a3b8',        // Neutral slate grey for secondary text
          text: '#f8fafc',        // Soft off-white main text
          white: '#ffffff',       // Pure white highlight
          red: '#cc0000',         // #cc0000 - Tesla Crimson Red
          accent: '#cc0000',      // Crimson Red primary CTA accent
          teal: '#38bdf8',        // Electric Sky Blue accent
          success: '#00e676',     // Autopilot Emerald Green
          warning: '#fbbf24',     // Warm Amber Caution
          danger: '#cc0000',      // Tesla Crimson Emergency
        }
      },
      fontFamily: {
        sans: ['Gotham', 'Helvetica Neue', 'Helvetica', 'Arial', 'Inter', 'sans-serif'],
        mono: ['Fira Code', 'Roboto Mono', 'monospace']
      }
    },
  },
  plugins: [],
}
