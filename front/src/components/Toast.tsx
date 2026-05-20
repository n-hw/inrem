/**
 * Lightweight Toast — Alert.alert 의 RN Web invisible 문제를 회피하기 위한 inline 대체.
 *
 * - Web/Native 모두 동일하게 보임.
 * - 3초 후 자동 dismiss (`durationMs` 로 조정 가능).
 * - 두 가지 톤: 'info'(기본) / 'success'.
 *
 * 사용처:
 *     const [toast, setToast] = useState<string | null>(null);
 *     ...
 *     {toast && <Toast message={toast} onDone={() => setToast(null)} />}
 */
import React, { useEffect } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { colors } from '../theme/colors';
import { radius, spacing } from '../theme/spacing';
import { typography } from '../theme/typography';

interface Props {
    message: string;
    tone?: 'info' | 'success';
    durationMs?: number;
    onDone?: () => void;
}

export const Toast = ({ message, tone = 'info', durationMs = 3000, onDone }: Props) => {
    useEffect(() => {
        if (!onDone) return;
        const handle = setTimeout(onDone, durationMs);
        return () => clearTimeout(handle);
    }, [message, durationMs, onDone]);

    const bg = tone === 'success' ? colors.success : colors.primary;

    return (
        <View pointerEvents="none" style={styles.wrap}>
            <View style={[styles.bubble, { backgroundColor: bg }]} accessibilityRole="alert">
                <Text style={[typography.body2, { color: colors.text.inverse }]}>{message}</Text>
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    wrap: {
        position: 'absolute',
        left: 0,
        right: 0,
        bottom: spacing.xxl + spacing.xl,
        alignItems: 'center',
        zIndex: 10,
    },
    bubble: {
        maxWidth: '90%',
        paddingHorizontal: spacing.lg,
        paddingVertical: spacing.md,
        borderRadius: radius.full,
        shadowColor: colors.black,
        shadowOpacity: 0.18,
        shadowOffset: { width: 0, height: 4 },
        shadowRadius: 8,
        elevation: 5,
    },
});
