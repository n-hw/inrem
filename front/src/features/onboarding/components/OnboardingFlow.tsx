import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { colors } from '../../../theme/colors';
import { spacing } from '../../../theme/spacing';
import { StepValueIntro } from './StepValueIntro';
import { StepGuardianIntro } from './StepGuardianIntro';
import { StepFirstPulse } from './StepFirstPulse';
import { useOnboarding } from '../hooks/useOnboarding';

type Step = 1 | 2 | 3;

const TOTAL_STEPS = 3;

const ProgressDots = ({ current }: { current: Step }) => (
    <View style={dotStyles.row}>
        {([1, 2, 3] as Step[]).map(n => (
            <View key={n} style={[dotStyles.dot, current === n && dotStyles.active]} />
        ))}
    </View>
);

const dotStyles = StyleSheet.create({
    row: { flexDirection: 'row', justifyContent: 'center', gap: 8, paddingTop: spacing.lg },
    dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.border },
    active: { backgroundColor: colors.primary },
});

export const OnboardingFlow = () => {
    const [step, setStep] = useState<Step>(1);
    const { finishOnboarding, isCompleting } = useOnboarding();

    const goNext = () => {
        if (step < TOTAL_STEPS) {
            const nextStep = (step + 1) as Step;
            setStep(nextStep);
        }
    };

    return (
        <View style={styles.container}>
            <ProgressDots current={step} />
            <View style={styles.stepContainer}>
                {step === 1 && (
                    <StepValueIntro
                        onNext={goNext}
                        onSkipAll={() => finishOnboarding()}
                        isSkipping={isCompleting}
                    />
                )}
                {step === 2 && (
                    <StepGuardianIntro
                        onNext={goNext}
                        onSkipAll={() => finishOnboarding()}
                        isSkipping={isCompleting}
                    />
                )}
                {step === 3 && (
                    <StepFirstPulse
                        onFinish={finishOnboarding}
                        onSkipAll={() => finishOnboarding()}
                        isCompleting={isCompleting}
                    />
                )}
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.background },
    stepContainer: { flex: 1 },
});
