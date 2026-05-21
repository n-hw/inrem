import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors } from '../../../theme/colors';
import { typography } from '../../../theme/typography';
import { spacing, radius } from '../../../theme/spacing';

interface Props {
    onNext: () => void;
    onSkipAll: () => void;
}

export const StepGuardianIntro = ({ onNext, onSkipAll }: Props) => (
    <View style={styles.container}>
        <View style={styles.content}>
            <Text style={styles.icon}>🛡️</Text>
            <Text style={[typography.heading2, styles.title]}>보호자 초대</Text>
            <Text style={[typography.body1, styles.description]}>
                가족이나 신뢰하는 사람에게 보호자 코드를 공유하면, 활동이 감지되지 않을 때 자동으로 알림이 가요.
            </Text>
            <View style={styles.infoBox}>
                <Text style={[typography.caption, styles.infoText]}>
                    💡 지금 바로 하지 않아도 괜찮아요.{'\n'}
                    설정 → 보호자 관리에서 언제든지 추가할 수 있어요.
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
    description: { color: colors.text.secondary, textAlign: 'center', lineHeight: 28 },
    infoBox: {
        backgroundColor: colors.accent,
        borderRadius: radius.md,
        padding: spacing.md,
        width: '100%',
    },
    infoText: { color: colors.text.secondary, lineHeight: 20 },
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
