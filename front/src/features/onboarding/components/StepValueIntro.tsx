import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors } from '../../../theme/colors';
import { typography } from '../../../theme/typography';
import { spacing, radius } from '../../../theme/spacing';

interface Props {
    onNext: () => void;
    onSkipAll: () => void;
}

export const StepValueIntro = ({ onNext, onSkipAll }: Props) => (
    <View style={styles.container}>
        <View style={styles.content}>
            <Text style={styles.icon}>🕰</Text>
            <Text style={[typography.heading2, styles.title]}>InRem이 하는 일</Text>
            <View style={styles.card}>
                <Text style={[typography.body1, styles.cardTitle]}>안부 체크 (Pulse)</Text>
                <Text style={[typography.body2, styles.cardBody]}>
                    매일 앱을 열기만 하면 안부 신호가 자동으로 전달돼요.
                </Text>
            </View>
            <View style={styles.card}>
                <Text style={[typography.body1, styles.cardTitle]}>디지털 유산함 (Heritage)</Text>
                <Text style={[typography.body2, styles.cardBody]}>
                    소중한 디지털 자산을 미리 정리해 안전하게 보관하세요.
                </Text>
            </View>
        </View>
        <View style={styles.actions}>
            <TouchableOpacity style={styles.primaryButton} onPress={onNext}>
                <Text style={[typography.body1, styles.primaryButtonText]}>다음</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.skipButton} onPress={onSkipAll}>
                <Text style={[typography.caption, styles.skipText]}>건너뛰기</Text>
            </TouchableOpacity>
        </View>
    </View>
);

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.background, paddingHorizontal: spacing.lg },
    content: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: spacing.lg },
    icon: { fontSize: 56, textAlign: 'center' },
    title: { color: colors.text.primary, textAlign: 'center' },
    card: {
        width: '100%',
        backgroundColor: colors.card,
        borderRadius: radius.md,
        padding: spacing.md,
        borderWidth: 1,
        borderColor: colors.border,
        gap: spacing.xs,
    },
    cardTitle: { color: colors.primary, fontWeight: '600' },
    cardBody: { color: colors.text.secondary },
    actions: { paddingBottom: spacing.xxl, gap: spacing.sm },
    primaryButton: {
        backgroundColor: colors.primary,
        borderRadius: radius.md,
        paddingVertical: spacing.md,
        alignItems: 'center',
    },
    primaryButtonText: { color: colors.text.inverse },
    skipButton: { alignItems: 'center', paddingVertical: spacing.sm },
    skipText: { color: colors.text.caption },
});
