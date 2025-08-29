import type { Config } from 'tailwindcss'
import tailwindcss from '@tailwindcss/vite' // optional if you use it in Vite
import plugin from 'tailwindcss/plugin'

export default {
  content: [
    './index.html',
    './src/**/*.{vue,ts,tsx,js,jsx}',
    './components/**/*.{vue,ts,tsx,js,jsx}',
  ],
  theme: {
    extend: {} // tokens come from CSS (@theme) in src/styles/tailwind.css
  },
  plugins: [
    // (Optional) add a class alias here if you want, but most utilities should be in CSS.
    plugin(() => {}),
  ],
} satisfies Config
