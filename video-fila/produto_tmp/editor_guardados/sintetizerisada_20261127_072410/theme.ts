import {loadFont} from '@remotion/google-fonts/Montserrat';

const montserrat = loadFont('normal', {
  weights: ['600', '700', '800', '900'],
  subsets: ['latin'],
});

export const FONT_FAMILY = montserrat.fontFamily;

export const THEME = {
  colors: {
    primary: '#FFA94D', // Laranja marca
    primaryDark: '#D97706',
    primaryGlow: 'rgba(255, 169, 77, 0.45)',
    darkBg: '#0B0F19',
    cardBg: '#111827EE',
    cardBorder: 'rgba(255, 255, 255, 0.12)',
    textPrimary: '#FFFFFF',
    textSecondary: '#E2E8F0',
    textMuted: '#94A3B8',
    textOnPrimary: '#1F2937',
    success: '#10B981',
    successBg: '#064E3BCC',
    danger: '#EF4444',
    dangerBg: '#7F1D1DCC',
    whatsappGreen: '#25D366',
    whatsappBubbleUser: '#FFFFFF',
    whatsappBubbleAi: '#DCF8C6',
  },
  safeZone: {
    top: 150,
    bottom: 1580,
    left: 60,
    right: 1020,
    width: 960,
  },
};
