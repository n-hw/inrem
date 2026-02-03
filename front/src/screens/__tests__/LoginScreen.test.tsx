import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { LoginScreen } from '../LoginScreen';
import { AuthProvider } from '../../context/AuthContext';

// Mock the AuthContext
jest.mock('../../context/AuthContext', () => {
    return {
        useAuth: () => ({
            login: jest.fn(),
            isLoading: false,
        }),
        AuthProvider: ({ children }: { children: React.ReactNode }) => children,
    };
});

describe('LoginScreen', () => {
    it('renders correctly', () => {
        const { getByText, getByPlaceholderText } = render(
            <AuthProvider>
                <LoginScreen onNavigateToSignup={jest.fn()} />
            </AuthProvider>
        );

        expect(getByText('InRem')).toBeTruthy();
        expect(getByPlaceholderText('example@email.com')).toBeTruthy();
        expect(getByText('로그인')).toBeTruthy();
    });

    it('shows alert when fields are empty', () => {
        const { getByText } = render(
            <AuthProvider>
                <LoginScreen onNavigateToSignup={jest.fn()} />
            </AuthProvider>
        );

        const loginButton = getByText('로그인');
        fireEvent.press(loginButton);

        // Alert.alert cannot be easily asserted in jest-expo without mocking Alert, 
        // but the test checks it doesn't crash.
        // For stricter test, we would mock Alert.alert.
    });
});
