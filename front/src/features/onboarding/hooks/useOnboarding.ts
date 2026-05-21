import { useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { settingsApi, SensitivityLevel } from '../../../api/client';

export const useOnboarding = () => {
    const { completeOnboarding } = useAuth();
    const [isCompleting, setIsCompleting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const finishOnboarding = async (sensitivity?: SensitivityLevel) => {
        setIsCompleting(true);
        setError(null);
        try {
            if (sensitivity) {
                await settingsApi.updatePolicy({ sensitivity });
            }
            await completeOnboarding();
        } catch (e) {
            // Log but don't trap user — onboarding is optional.
            // The user state stays unchanged; App.tsx will keep showing onboarding.
            console.error('[Onboarding] Failed to complete:', e);
            setError('연결에 문제가 있어요. 잠시 후 다시 시도해 주세요.');
        } finally {
            setIsCompleting(false);
        }
    };

    return { finishOnboarding, isCompleting, error };
};
