import { useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { settingsApi, SensitivityLevel } from '../../../api/client';

export const useOnboarding = () => {
    const { completeOnboarding } = useAuth();
    const [isCompleting, setIsCompleting] = useState(false);

    const finishOnboarding = async (sensitivity?: SensitivityLevel) => {
        setIsCompleting(true);
        try {
            if (sensitivity) {
                await settingsApi.updatePolicy({ sensitivity });
            }
            await completeOnboarding();
        } finally {
            setIsCompleting(false);
        }
    };

    return { finishOnboarding, isCompleting };
};
