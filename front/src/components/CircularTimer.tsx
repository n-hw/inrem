import React, { useEffect } from 'react';
import { View, StyleSheet, Text } from 'react-native';
import Svg, { Circle } from 'react-native-svg';
import Animated, {
    useSharedValue,
    useAnimatedProps,
    withTiming,
    Easing,
} from 'react-native-reanimated';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';

const AnimatedCircle = Animated.createAnimatedComponent(Circle);

interface CircularTimerProps {
    percentage: number; // 0 to 1 (1 = full time remaining, 0 = expired)
    remainingText: string;
    subText: string;
    size?: number;
    strokeWidth?: number;
    status: 'safe' | 'warning' | 'critical';
}

export const CircularTimer = ({
    percentage,
    remainingText,
    subText,
    size = 280,
    strokeWidth = 20,
    status,
}: CircularTimerProps) => {
    const radius = (size - strokeWidth) / 2;
    const circumference = radius * 2 * Math.PI;
    const progress = useSharedValue(0);

    useEffect(() => {
        progress.value = withTiming(percentage, {
            duration: 1000,
            easing: Easing.out(Easing.cubic),
        });
    }, [percentage]);

    const animatedProps = useAnimatedProps(() => {
        const strokeDashoffset = circumference * (1 - progress.value);
        return {
            strokeDashoffset,
        };
    });

    // Color interpolation based on percentage or status
    // Simple mapping for now based on status prop
    const getStatusColor = () => {
        switch (status) {
            case 'safe': return colors.primary; // Deep Ocean Blue
            case 'warning': return '#FB8C00'; // Orange
            case 'critical': return colors.danger; // Red
            default: return colors.primary;
        }
    };

    const activeColor = getStatusColor();

    return (
        <View style={[styles.container, { width: size, height: size }]}>
            <View style={styles.textContainer}>
                <Text style={[typography.label, { color: colors.text.caption }]}>{subText}</Text>
                <Text style={[typography.heading1, { color: activeColor, fontSize: 40, marginVertical: 8 }]}>
                    {remainingText}
                </Text>
                <Text style={[typography.caption, { color: colors.text.secondary }]}>
                    {status === 'safe' ? '안전합니다' : status === 'warning' ? '확인이 필요해요' : '긴급'}
                </Text>
            </View>
            <Svg width={size} height={size}>
                {/* Background Track */}
                <Circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    stroke={colors.background === '#F8F9FA' ? '#E0E0E0' : '#333'} // Light gray track
                    strokeWidth={strokeWidth}
                    fill="transparent"
                />
                {/* Progress Circle */}
                <AnimatedCircle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    stroke={activeColor}
                    strokeWidth={strokeWidth}
                    fill="transparent"
                    strokeDasharray={`${circumference} ${circumference}`}
                    strokeLinecap="round"
                    rotation="-90"
                    origin={`${size / 2}, ${size / 2}`}
                    animatedProps={animatedProps}
                />
            </Svg>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        justifyContent: 'center',
        alignItems: 'center',
    },
    textContainer: {
        position: 'absolute',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 1,
    },
});
