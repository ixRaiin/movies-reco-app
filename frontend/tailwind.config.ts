// tailwind.config.ts
import type { Config } from 'tailwindcss'
import plugin from 'tailwindcss/plugin'

export default {
  content: [
    './index.html',
    './src/**/*.{vue,ts,tsx,js,jsx}',
  ],
  theme: {
    extend: {
      colors: {
        background: 'var(--bg-0)',
        foreground: 'var(--bg-1)',
        'text-primary': 'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',
        'neon-cyan': 'var(--neon-cyan)',
        'neon-violet': 'var(--neon-violet)',
        'neon-magenta': 'var(--neon-magenta)',
        'neon-orange': 'var(--neon-orange)',
      },
      borderRadius: {
        '2xl': '1rem',
      },
      boxShadow: {
        neon: '0 0 18px rgba(0,229,255,.25)',
      },
      animation: {
        'pulse-soft': 'pulseSoft 2.4s ease-in-out infinite',
      },
      keyframes: {
        pulseSoft: {
          '0%, 100%': { opacity: .7 },
          '50%': { opacity: 1 },
        },
      },
    },
  },
  safelist: [
    'bg-[color:var(--neon-cyan)]/90', // you use this in the Send button
    'bg-aurora',
    'overlay-glass',
    'overlay-glass-strong',
    'text-grad-cyan-violet',
  ],
  plugins: [
    plugin(function({ addUtilities }) {
      addUtilities({
        '.card-glow': {
          boxShadow: '0 10px 25px rgba(0,0,0,.35), 0 0 24px rgba(0,229,255,.06)',
        },
      })
    }),
  ],
} satisfies Config
