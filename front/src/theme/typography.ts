import { TextStyle } from 'react-native';

export const fontFamily = {
    thin: 'Pretendard-Regular', // Fallback
    light: 'Pretendard-Regular', // Fallback
    regular: 'Pretendard-Regular',
    medium: 'Pretendard-Medium',
    bold: 'Pretendard-Bold',
    black: 'Pretendard-Bold', // Fallback
};

export const typography = {
    // Heading: 24pt~28pt (Bold)
    heading1: {
        fontFamily: fontFamily.bold,
        fontSize: 28,
        lineHeight: 36,
    } as TextStyle,
    heading2: {
        fontFamily: fontFamily.bold,
        fontSize: 24,
        lineHeight: 32,
    } as TextStyle,

    // Body: 18pt (Medium/Regular)
    body1: {
        fontFamily: fontFamily.medium,
        fontSize: 18,
        lineHeight: 26,
    } as TextStyle,
    body2: {
        fontFamily: fontFamily.regular,
        fontSize: 18,
        lineHeight: 26,
    } as TextStyle,

    // Caption: 14pt (Regular)
    caption: {
        fontFamily: fontFamily.regular,
        fontSize: 14,
        lineHeight: 20,
    } as TextStyle,
};
