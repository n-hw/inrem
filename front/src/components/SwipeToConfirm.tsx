import React, { useState } from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import { GestureDetector, Gesture } from 'react-native-gesture-handler';
import Animated, {
    useAnimatedStyle,
    useSharedValue,
    withSpring,
    runOnJS,
    interpolate,
    Extrapolate,
} from 'react-native-reanimated';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { haptic } from '../utils/haptics';

const BUTTON_HEIGHT = 60;
const BUTTON_WIDTH = Dimensions.get('window').width - 48; // padding horizontal 24 * 2
const SWIPEABLE_DIMENSIONS = BUTTON_HEIGHT - 8;
const H_SWIPE_RANGE = BUTTON_WIDTH - BUTTON_HEIGHT;

interface SwipeToConfirmProps {
    onConfirm: () => Promise<void>;
    isLoading?: boolean;
}

export const SwipeToConfirm = ({ onConfirm, isLoading = false }: SwipeToConfirmProps) => {
    const X = useSharedValue(0);
    const startX = useSharedValue(0);
    const [isCompleted, setIsCompleted] = useState(false);

    const handleComplete = async () => {
        setIsCompleted(true);
        await haptic.success();
        await onConfirm();
        // Reset after delay
        setTimeout(() => {
            setIsCompleted(false);
            X.value = withSpring(0);
        }, 2000);
    };

    const pan = Gesture.Pan()
        .onStart(() => {
            startX.value = X.value;
        })
        .onUpdate((event) => {
            if (isCompleted || isLoading) return;
            let newValue = startX.value + event.translationX;
            if (newValue < 0) newValue = 0;
            if (newValue > H_SWIPE_RANGE) newValue = H_SWIPE_RANGE;
            X.value = newValue;
        })
        .onEnd(() => {
            if (isCompleted || isLoading) return;
            if (X.value > H_SWIPE_RANGE * 0.7) {
                X.value = withSpring(H_SWIPE_RANGE);
                runOnJS(handleComplete)();
            } else {
                X.value = withSpring(0);
            }
        });

    const AnimatedStyles = {
        swipeable: useAnimatedStyle(() => {
            return {
                transform: [{ translateX: X.value }],
                backgroundColor: isCompleted ? colors.secondary : colors.primary,
            };
        }),
        text: useAnimatedStyle(() => {
            return {
                opacity: interpolate(
                    X.value,
                    [0, H_SWIPE_RANGE / 2],
                    [1, 0],
                    Extrapolate.CLAMP
                ),
            };
        }),
    };

    return (
        <View style={styles.container}>
            <View style={styles.track}>
                <Animated.View style={[styles.textContainer, AnimatedStyles.text]}>
                    <Text style={[typography.body2, { color: colors.text.caption }]}>
                        밀어서 안부 확인하기 {'>>>'}
                    </Text>
                </Animated.View>
                <GestureDetector gesture={pan}>
                    <Animated.View style={[styles.swipeable, AnimatedStyles.swipeable]}>
                        <Text style={{ color: colors.white, fontWeight: 'bold' }}>
                            {isLoading ? '...' : isCompleted ? '✓' : '>'}
                        </Text>
                    </Animated.View>
                </GestureDetector>
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        width: BUTTON_WIDTH,
        height: BUTTON_HEIGHT,
        alignItems: 'center',
        justifyContent: 'center',
        marginVertical: 20,
    },
    track: {
        width: BUTTON_WIDTH,
        height: BUTTON_HEIGHT,
        borderRadius: BUTTON_HEIGHT / 2,
        backgroundColor: colors.white,
        borderWidth: 1,
        borderColor: colors.border,
        justifyContent: 'center',
        padding: 4,
    },
    swipeable: {
        width: SWIPEABLE_DIMENSIONS,
        height: SWIPEABLE_DIMENSIONS,
        borderRadius: SWIPEABLE_DIMENSIONS / 2,
        backgroundColor: colors.primary,
        justifyContent: 'center',
        alignItems: 'center',
        position: 'absolute',
        left: 4,
        zIndex: 2,
    },
    textContainer: {
        width: '100%',
        alignItems: 'center',
        justifyContent: 'center',
    },
});
