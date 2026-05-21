import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { colors } from '../../../theme/colors';
import { typography } from '../../../theme/typography';
import { spacing, radius } from '../../../theme/spacing';
import { SensitivityLevel } from '../../../api/client';
import { useOnboarding } from '../hooks/useOnboarding';

const SENSITIVITY_OPTIONS: { value: SensitivityLevel; label: string; description: string }[] = [
    { value: 'relaxed', label: '느슨함', description: '24시간 무활동 시 안부 확인' },
    { value: 'normal', label: '보통', description: '12시간 무활동 시 안부 확인' },
    { value: 'strict', label: '엄격함', description: '6시간 무활동 시 안부 확인' },
];

interface Props {
    onSkipAll: () => void;
}

export const StepFirstPulse = ({ onSkipAll }: Props) => {
    const [selected, setSelected] = useState<SensitivityLevel>('normal');
    const { finishOnboarding, isCompleting } = useOnboarding();

    return (
        <View style={styles.container}>
            <View style={styles.content}>
                <Text style={styles.icon}>💚</Text>
                <Text style={[typography.heading2, styles.title]}>안부 민감도 설정</Text>
                <Text style={[typography.body2, styles.subtitle]}>
                    얼마나 자주 안부를 확인할까요? 나중에 설정에서 바꿀 수 있어요.
                </Text>
                <View style={styles.optionsList}>
                    {SENSITIVITY_OPTIONS.map(opt => (
                        <TouchableOpacity
                            key={opt.value}
                            style={[styles.option, selected === opt.value && styles.optionSelected]}
                            onPress={() => setSelected(opt.value)}
                        >
                            <View style={[styles.radio, selected === opt.value && styles.radioSelected]} />
                            <View style={styles.optionText}>
                                <Text style={[typography.body1, styles.optionLabel]}>{opt.label}</Text>
                                <Text style={[typography.caption, styles.optionDesc]}>{opt.description}</Text>
                            </View>
                        </TouchableOpacity>
                    ))}
                </View>
            </View>
            <View style={styles.actions}>
                <TouchableOpacity
                    style={[styles.primaryButton, isCompleting && styles.disabled]}
                    onPress={() => finishOnboarding(selected)}
                    disabled={isCompleting}
                >
                    {isCompleting ? (
                        <ActivityIndicator color={colors.text.inverse} />
                    ) : (
                        <Text style={[typography.body1, styles.primaryButtonText]}>시작하기</Text>
                    )}
                </TouchableOpacity>
                <TouchableOpacity style={styles.skipButton} onPress={onSkipAll} disabled={isCompleting}>
                    <Text style={[typography.caption, styles.skipText]}>건너뛰기</Text>
                </TouchableOpacity>
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.background, paddingHorizontal: spacing.lg },
    content: { flex: 1, justifyContent: 'center', gap: spacing.lg },
    icon: { fontSize: 56, textAlign: 'center' },
    title: { color: colors.text.primary, textAlign: 'center' },
    subtitle: { color: colors.text.secondary, textAlign: 'center' },
    optionsList: { gap: spacing.sm },
    option: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: colors.card,
        borderRadius: radius.md,
        padding: spacing.md,
        borderWidth: 1,
        borderColor: colors.border,
        gap: spacing.md,
    },
    optionSelected: { borderColor: colors.primary, backgroundColor: '#F0F4FF' },
    radio: {
        width: 20,
        height: 20,
        borderRadius: 10,
        borderWidth: 2,
        borderColor: colors.border,
    },
    radioSelected: { borderColor: colors.primary, backgroundColor: colors.primary },
    optionText: { flex: 1 },
    optionLabel: { color: colors.text.primary },
    optionDesc: { color: colors.text.caption },
    actions: { paddingBottom: spacing.xxl, gap: spacing.sm },
    primaryButton: {
        backgroundColor: colors.primary,
        borderRadius: radius.md,
        paddingVertical: spacing.md,
        alignItems: 'center',
    },
    disabled: { opacity: 0.6 },
    primaryButtonText: { color: colors.text.inverse },
    skipButton: { alignItems: 'center', paddingVertical: spacing.sm },
    skipText: { color: colors.text.caption },
});
