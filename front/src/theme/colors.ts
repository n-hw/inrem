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

    // 반응형 셸 — viewport 가 모바일 폭(MAX_CONTENT_WIDTH) 보다 클 때 외곽에
    // 깔리는 배경. 모바일 컨테이너가 카드처럼 떠 있는 듯한 효과로 큰 화면
    // (태블릿·웹·데스크톱) 에서도 디자인이 깨지지 않도록.
    shell: '#E3E7EC',
} as const;
