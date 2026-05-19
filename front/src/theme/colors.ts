/**
 * InRem color tokens.
 * Concept: "Warm Serenity" (따뜻한 평온)
 * See: document/design_system.md §2
 */
export const colors = {
    // Primary: Deep Ocean Blue (신뢰, 안정, 전문성 + 고대비)
    primary: '#003366',

    // Secondary: Soft Sage (생명력, 평온, 위로)
    secondary: '#B2AC88',

    // Accent: Warm Sand (인간적인 따뜻함)
    accent: '#D4C4B5',

    // Background: Off-white (눈의 피로도 감소)
    background: '#F8F9FA',

    // Semantic
    danger: '#D32F2F',
    success: '#2E7D32',
    warning: '#F57C00',

    // Text
    text: {
        primary: '#111111',
        secondary: '#424242',
        caption: '#757575',
        inverse: '#FFFFFF',
    },

    // Common
    white: '#FFFFFF',
    black: '#000000',
    transparent: 'transparent',

    // UI
    border: '#E0E0E0',
    card: '#FFFFFF',
    overlay: 'rgba(0, 0, 0, 0.4)',
} as const;
