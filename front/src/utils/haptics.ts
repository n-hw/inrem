import * as Haptics from 'expo-haptics';
import { Platform } from 'react-native';

/**
 * Haptic Feedback Utility
 * provides consistent tactile feedback across the app.
 *
 * Design Principle: "Haptic Feedback: 버튼 클릭이나 기록 완료 시 부드러운 진동 피드백을 주어 조작의 확신을 제공."
 */

export const haptic = {
    /**
     * Use for successful actions (e.g., saving a record, completing a task).
     * Result: Light, pleasant vibration.
     */
    success: async () => {
        if (Platform.OS === 'web') return;
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    },

    /**
     * Use for error states or destructive actions deletion warnings.
     * Result: Stronger, distinct vibration.
     */
    error: async () => {
        if (Platform.OS === 'web') return;
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    },

    /**
     * Use for warnings or important alerts.
     * Result: Two short pulses.
     */
    warning: async () => {
        if (Platform.OS === 'web') return;
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
    },

    /**
     * Use for standard button taps or list item selections.
     * Result: Very light, subtle tick.
     */
    selection: async () => {
        if (Platform.OS === 'web') return;
        await Haptics.selectionAsync();
    },

    /**
     * Use for distinct impact (e.g., drawer opening, major UI transition).
     * Styles: Light, Medium, Heavy
     */
    impact: async (style: Haptics.ImpactFeedbackStyle = Haptics.ImpactFeedbackStyle.Medium) => {
        if (Platform.OS === 'web') return;
        await Haptics.impactAsync(style);
    },
};
