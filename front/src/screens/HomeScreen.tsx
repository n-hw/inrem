import React, { useState, useEffect, useCallback } from 'react';
import { View, StyleSheet, Text, ScrollView, RefreshControl } from 'react-native';
import { ScreenLayout } from '../components/ScreenLayout';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { useAuth } from '../context/AuthContext';
import { CircularTimer } from '../components/CircularTimer';
import { SwipeToConfirm } from '../components/SwipeToConfirm';
import { signalApi, settingsApi } from '../api/client';
import { haptic } from '../utils/haptics';

export const HomeScreen = () => {
    const { user } = useAuth();
    const [isLoading, setIsLoading] = useState(false);
    const [thresholdHours, setThresholdHours] = useState(12);
    const [lastActiveAt, setLastActiveAt] = useState<Date>(new Date());
    const [remainingSeconds, setRemainingSeconds] = useState(0);

    // Initial Fetch: Policy & Status
    const fetchData = useCallback(async () => {
        setIsLoading(true);
        try {
            const policy = await settingsApi.getPolicy();
            setThresholdHours(policy.threshold_hours);

            // In a real scenario, we should fetch 'last_active_at' from user profile or status API
            // For MVP, we presume the local session start or a heartbeat response updates this.
            // Let's manually trigger a heartbeat 'app_open' to sync first.
            const response = await signalApi.sendHeartbeat('app_open');
            setLastActiveAt(new Date(response.last_active_at));
        } catch (e) {
            console.error('Failed to fetch home data', e);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    // Timer Logic
    useEffect(() => {
        const calculateRemaining = () => {
            if (!lastActiveAt) return;
            const now = new Date();
            const thresholdMs = thresholdHours * 60 * 60 * 1000;
            const elapsed = now.getTime() - lastActiveAt.getTime();
            const remaining = Math.max(0, thresholdMs - elapsed);
            setRemainingSeconds(Math.floor(remaining / 1000));
        };

        calculateRemaining();
        const interval = setInterval(calculateRemaining, 1000); // Update every second

        return () => clearInterval(interval);
    }, [lastActiveAt, thresholdHours]);

    const handleConfirm = async () => {
        try {
            // Send heartbeat (manual check-in)
            const response = await signalApi.sendHeartbeat('manual_checkin');
            setLastActiveAt(new Date(response.last_active_at));
            await haptic.success();
        } catch (e) {
            console.error('Check-in failed', e);
            await haptic.error();
        }
    };

    // Calculate percentage for visualization
    const totalSeconds = thresholdHours * 3600;
    const percentage = Math.max(0, Math.min(1, remainingSeconds / totalSeconds));

    // Format timer text
    const formatTime = (secs: number) => {
        const h = Math.floor(secs / 3600);
        const m = Math.floor((secs % 3600) / 60);
        return `${h}시간 ${m}분`;
    };

    // Status Determination
    const getStatus = () => {
        if (remainingSeconds === 0) return 'critical';
        if (remainingSeconds < 3600) return 'warning'; // Less than 1 hour
        return 'safe';
    };

    return (
        <ScreenLayout>
            <ScrollView
                contentContainerStyle={styles.container}
                refreshControl={<RefreshControl refreshing={isLoading} onRefresh={fetchData} />}
            >
                <View style={styles.header}>
                    <Text style={[typography.heading2, { color: colors.text.primary }]}>
                        안녕하세요, {user?.email || '회원'}님
                    </Text>
                    <Text style={[typography.body2, { color: colors.text.secondary }]}>
                        오늘도 안전하게 지켜드릴게요.
                    </Text>
                </View>

                <View style={styles.timerContainer}>
                    <CircularTimer
                        percentage={percentage}
                        remainingText={formatTime(remainingSeconds)}
                        subText="다음 확인까지"
                        status={getStatus()}
                    />
                </View>

                <View style={styles.actionContainer}>
                    <SwipeToConfirm onConfirm={handleConfirm} />
                    <Text style={[typography.caption, { color: colors.text.caption, marginTop: 16 }]}>
                        활동이 감지되면 타이머가 자동으로 연장됩니다.
                    </Text>
                </View>

                {/* Status Badge (Simple for now) */}
                <View style={styles.statusBadge}>
                    <View style={[styles.dot, { backgroundColor: colors.secondary }]} />
                    <Text style={[typography.label, { color: colors.text.secondary }]}>
                        모니터링 중
                    </Text>
                </View>

            </ScrollView>
        </ScreenLayout>
    );
};

const styles = StyleSheet.create({
    container: {
        flexGrow: 1,
        alignItems: 'center',
        paddingVertical: 24,
    },
    header: {
        width: '100%',
        paddingHorizontal: 24,
        marginBottom: 40,
        alignItems: 'flex-start',
    },
    timerContainer: {
        marginBottom: 40,
    },
    actionContainer: {
        alignItems: 'center',
        width: '100%',
    },
    statusBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: colors.white,
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 20,
        borderWidth: 1,
        borderColor: colors.border,
        marginTop: 40,
    },
    dot: {
        width: 8,
        height: 8,
        borderRadius: 4,
        marginRight: 6,
    },
});
