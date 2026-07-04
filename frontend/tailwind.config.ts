import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        background: '#FFFFFF',
        surface: '#F8FAFC',
        surfaceElevated: '#FFFFFF',
        primary: '#00B8D9',
        primaryDark: '#0086A8',
        primarySoft: '#E6FAFE',
        text: '#0B0F14',
        textMuted: '#4B5563',
        border: '#E5E7EB',
        danger: '#EF4444',
        success: '#10B981',
        warning: '#F59E0B',
      },
      maxWidth: {
        client: '480px',
        dashboard: '1200px',
      },
      minHeight: {
        touch: '44px',
      },
    },
  },
} satisfies Config
