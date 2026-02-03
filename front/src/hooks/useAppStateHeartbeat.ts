/**
 * Custom hook to send heartbeat signals when app comes to foreground.
 * Uses debouncing to prevent excessive API calls.
 */

import { useEffect, useRef, useCallback } from 'react';
import { AppState, AppStateStatus, Platform } from 'react-native';
import { signalApi, SignalType } from '../api/client';
import { useAuth } from '../context/AuthContext';

const DEBOUNCE_INTERVAL_MS = 60 * 1000; // 1 minute cooldown between heartbeats

interface UseAppStateHeartbeatOptions {
    /** Enable/disable the hook */
    enabled?: boolean;
    /** Interval between allowed heartbeats in ms */
    debounceMs?: number;
    /** Callback when heartbeat succeeds */
    onSuccess?: () => void;
    /** Callback when heartbeat fails */
    onError?: (error: Error) => void;
}

export const useAppStateHeartbeat = (options: UseAppStateHeartbeatOptions = {}) => {
    const {
        enabled = true,
        debounceMs = DEBOUNCE_INTERVAL_MS,
        onSuccess,
        onError,
    } = options;

    const { isAuthenticated } = useAuth();
    const lastSentTimeRef = useRef<number>(0);
    const appStateRef = useRef<AppStateStatus>(AppState.currentState);

    const sendHeartbeat = useCallback(async (signalType: SignalType) => {
        const now = Date.now();

        // Skip if not authenticated
        if (!isAuthenticated) {
            return;
        }

        // Debounce: skip if cooldown hasn't passed
        if (now - lastSentTimeRef.current < debounceMs) {
            console.log('[Heartbeat] Skipping - debounce active');
            return;
        }

        try {
            const deviceInfo = `${Platform.OS} ${Platform.Version}`;
            await signalApi.sendHeartbeat(signalType, deviceInfo);
            lastSentTimeRef.current = now;
            console.log('[Heartbeat] Sent successfully');
            onSuccess?.();
        } catch (error) {
            console.warn('[Heartbeat] Failed to send:', error);
            onError?.(error as Error);
        }
    }, [isAuthenticated, debounceMs, onSuccess, onError]);

    useEffect(() => {
        if (!enabled) return;

        // Send initial heartbeat when hook mounts (app opened)
        sendHeartbeat('app_open');

        const handleAppStateChange = (nextAppState: AppStateStatus) => {
            // Detect transition to active (foreground)
            if (
                appStateRef.current.match(/inactive|background/) &&
                nextAppState === 'active'
            ) {
                console.log('[Heartbeat] App came to foreground');
                sendHeartbeat('app_foreground');
            }

            appStateRef.current = nextAppState;
        };

        const subscription = AppState.addEventListener('change', handleAppStateChange);

        return () => {
            subscription?.remove();
        };
    }, [enabled, sendHeartbeat]);

    return {
        sendManualHeartbeat: () => sendHeartbeat('manual_checkin'),
    };
};
