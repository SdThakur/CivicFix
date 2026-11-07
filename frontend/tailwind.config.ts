import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class", '[data-theme="dark"]'],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/styles/**/*.{css,scss}",
  ],
  theme: {
    extend: {
      colors: {
        // Maryland Flag Brand Primitives
        md: {
          white: 'var(--md-white)',
          'white-warm': 'var(--md-white-warm)',
          gold: 'var(--md-gold)',
          'gold-hover': 'var(--md-gold-hover)',
          'gold-subtle': 'var(--md-gold-subtle)',
          'gold-glass': 'var(--md-gold-glass)',
          red: 'var(--md-red)',
          'red-hover': 'var(--md-red-hover)',
          'red-subtle': 'var(--md-red-subtle)',
          'red-glass': 'var(--md-red-glass)',
          black: 'var(--md-black)',
        },
        // Semantic Surface Mappings (~60% White dominant)
        surface: {
          canvas: 'var(--surface-canvas)',
          'canvas-subtle': 'var(--surface-canvas-subtle)',
          card: 'var(--surface-card)',
          'card-subtle': 'var(--surface-card-subtle)',
          'card-hover': 'var(--surface-card-hover)',
          'card-muted': 'var(--surface-card-muted)',
          border: 'var(--surface-border)',
          'border-strong': 'var(--surface-border-strong)',
          glass: 'var(--glass-bg)',
          'glass-chrome': 'var(--glass-chrome-solid)',
          'glass-border': 'var(--glass-border-outer)',
          'glass-specular': 'var(--glass-specular)',
        },
        // Typography Content Tokens
        content: {
          primary: 'var(--text-primary)',
          secondary: 'var(--text-secondary)',
          muted: 'var(--text-muted)',
          inverse: 'var(--text-inverse)',
        },
        // Action Tokens (Red Primary / Gold Accent)
        action: {
          primary: 'var(--action-primary)',
          'primary-hover': 'var(--action-primary-hover)',
          'primary-text': 'var(--action-primary-text)',
          accent: 'var(--action-accent)',
          'accent-hover': 'var(--action-accent-hover)',
          'accent-text': 'var(--action-accent-text)',
        },
        // Status Tokens
        status: {
          urgent: 'var(--status-urgent)',
          'urgent-bg': 'var(--status-urgent-bg)',
          active: 'var(--status-active)',
          'active-bg': 'var(--status-active-bg)',
          neutral: 'var(--status-neutral)',
          'neutral-bg': 'var(--status-neutral-bg)',
          // Backward compatibility mappings for existing status helpers
          success: 'var(--md-gold)',
          'success-subtle': 'var(--md-gold-subtle)',
          'success-border': 'var(--glass-tint-gold-border)',
          warning: 'var(--md-gold)',
          'warning-subtle': 'var(--md-gold-subtle)',
          'warning-border': 'var(--glass-tint-gold-border)',
          danger: 'var(--md-red)',
          'danger-subtle': 'var(--md-red-subtle)',
          'danger-border': 'var(--glass-tint-red-border)',
        },
        // Legacy Brand mapping during transition
        brand: {
          50: '#fffdf7',
          100: '#fffbeb',
          200: '#fef08a',
          300: '#fde047',
          400: '#ffc72c',
          500: '#e03a3e',
          600: '#c93236',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#0b0b0c',
          950: '#000000',
        },
        civic: {
          primary: 'var(--action-primary)',
          'primary-hover': 'var(--action-primary-hover)',
          'primary-subtle': 'var(--md-red-subtle)',
          'primary-border': 'var(--glass-tint-red-border)',
        },
      },
      borderRadius: {
        xs: 'var(--radius-xs)',
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-xl)',
        pill: 'var(--radius-pill)',
      },
      boxShadow: {
        'glass-sm': 'var(--shadow-glass-sm)',
        'glass-md': 'var(--shadow-glass-md)',
        'glass-lg': 'var(--shadow-glass-lg)',
        card: 'var(--shadow-card)',
        floating: 'var(--shadow-floating)',
      },
      transitionTimingFunction: {
        spring: 'var(--ease-spring)',
        liquid: 'var(--ease-liquid)',
        standard: 'var(--ease-standard)',
      },
      transitionDuration: {
        micro: 'var(--duration-micro)',
        fast: 'var(--duration-fast)',
        normal: 'var(--duration-normal)',
        sheet: 'var(--duration-sheet)',
      },
      fontFamily: {
        sans: [
          'Public Sans',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          'sans-serif',
        ],
        display: [
          'Public Sans',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'sans-serif',
        ],
        mono: [
          'ui-monospace',
          'SFMono-Regular',
          'Menlo',
          'Monaco',
          'Consolas',
          'monospace',
        ],
      },
      minHeight: {
        touch: 'var(--touch-target-min)',
      },
      minWidth: {
        touch: 'var(--touch-target-min)',
      },
      animation: {
        'mesh-drift': 'meshDrift var(--mesh-drift-duration) ease-in-out infinite alternate',
      },
      keyframes: {
        meshDrift: {
          '0%': { transform: 'translate(0px, 0px) scale(1)' },
          '50%': { transform: 'translate(-30px, 20px) scale(1.06)' },
          '100%': { transform: 'translate(25px, -25px) scale(0.96)' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
