import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import * as SecureStore from 'expo-secure-store';
import { authApi } from '../api/client';

interface User {
    id: string;
    email: string;
    is_active: boolean;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Check for existing token on app startup
    useEffect(() => {
        const loadToken = async () => {
            try {
                const storedToken = await SecureStore.getItemAsync('access_token');
                if (storedToken) {
                    setToken(storedToken);
                    // Fetch user data
                    const userData = await authApi.getMe();
                    setUser(userData);
                }
            } catch (_error) {
                // Token invalid or expired
                await SecureStore.deleteItemAsync('access_token');
            } finally {
                setIsLoading(false);
            }
        };

        loadToken();
    }, []);

    const login = async (email: string, password: string) => {
        const response = await authApi.login(email, password);
        await SecureStore.setItemAsync('access_token', response.access_token);
        setToken(response.access_token);

        // Fetch user data
        const userData = await authApi.getMe();
        setUser(userData);
    };

    const register = async (email: string, password: string) => {
        const response = await authApi.register(email, password);
        await SecureStore.setItemAsync('access_token', response.access_token);
        setToken(response.access_token);

        // Fetch user data
        const userData = await authApi.getMe();
        setUser(userData);
    };

    const logout = async () => {
        await SecureStore.deleteItemAsync('access_token');
        setToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                token,
                isLoading,
                isAuthenticated: !!token && !!user,
                login,
                register,
                logout,
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
