import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authApi, tokenStorage, apiClient } from '../api/client';

interface User {
    id: string;
    email: string;
    is_active: boolean;
    onboarding_completed_at: string | null;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    isOnboardingCompleted: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
    completeOnboarding: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const loadToken = async () => {
            try {
                const storedToken = await tokenStorage.getAccess();
                if (storedToken) {
                    setToken(storedToken);
                    const userData = await authApi.getMe();
                    setUser(userData);
                }
            } catch (_error) {
                await tokenStorage.clear();
            } finally {
                setIsLoading(false);
            }
        };
        loadToken();
    }, []);

    const login = async (email: string, password: string) => {
        const response = await authApi.login(email, password);
        await tokenStorage.setBoth(response.access_token, response.refresh_token);
        setToken(response.access_token);
        const userData = await authApi.getMe();
        setUser(userData);
    };

    const register = async (email: string, password: string) => {
        const response = await authApi.register(email, password);
        await tokenStorage.setBoth(response.access_token, response.refresh_token);
        setToken(response.access_token);
        const userData = await authApi.getMe();
        setUser(userData);
    };

    const logout = async () => {
        await tokenStorage.clear();
        setToken(null);
        setUser(null);
    };

    const completeOnboarding = async () => {
        const resp = await apiClient.patch('/auth/me/onboarding');
        setUser(prev =>
            prev ? { ...prev, onboarding_completed_at: resp.data.onboarding_completed_at } : null
        );
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                token,
                isLoading,
                isAuthenticated: !!token && !!user,
                isOnboardingCompleted: !!user?.onboarding_completed_at,
                login,
                register,
                logout,
                completeOnboarding,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
