import React, { useState, useEffect, useCallback } from 'react';
import {
    ActivityIndicator,
    RefreshControl,
    ScrollView,
    StyleSheet,
    Text,
    TouchableOpacity,
    View,
} from 'react-native';
import { ScreenLayout } from '../components/ScreenLayout';
import { Toast } from '../components/Toast';
import { colors } from '../theme/colors';
import { radius, spacing } from '../theme/spacing';
import { typography } from '../theme/typography';
import { useAuth } from '../context/AuthContext';
import { CircularTimer } from '../components/CircularTimer';
import { SwipeToConfirm } from '../components/SwipeToConfirm';
import {
    type AssetSummary,
    heritageApi,
    settingsApi,
    signalApi,
    upsellApi,
} from '../api/client';
import { haptic } from '../utils/haptics';
import type { MainTabKey } from './MainTabsScreen';

interface Props {
    /** Optional tab navigator hook so cards can deep-link into other tabs. */
    onNavigate?: (key: MainTabKey) => void;
}

export const HomeScreen: React.FC<Props> = ({ onNavigate }) => {
    const { user } = useAuth();
    const [isLoading, setIsLoading] = useState(true);
    const [thresholdHours, setThresholdHours] = useState(12);
    /**
     * `null` until the first /signal/heartbeat response arrives. We avoid
     * seeding with `new Date()` because that paints a full-bar timer that
     * then jumps to the correct value once the server replies.
     */
    const [lastActiveAt, setLastActiveAt] = useState<Date | null>(null);
    const [remainingSeconds, setRemainingSeconds] = useState(0);
    const [heritageSummary, setHeritageSummary] = useState<AssetSummary | null>(null);
    const [toast, setToast] = useState<{ message: string; tone: 'info' | 'success' } | null>(null);

    // Initial Fetch: Policy & Status. Sends an app_open heartbeat on
    // mount so the user is registered as active; later polls via the
    // read-only /signal/status endpoint (no side effects).
    const fetchData = useCallback(async () => {
        setIsLoading(true);
        try {
            const policy = await settingsApi.getPolicy();
            setThresholdHours(policy.threshold_hours);

            const response = await signalApi.sendHeartbeat('app_open');
            setLastActiveAt(new Date(response.last_active_at));

            try {
                const sum = await heritageApi.getSummary();
                setHeritageSummary(sum);
            } catch (e) {
                console.warn('Heritage summary fetch failed', e);
            }
        } catch (e) {
            console.error('Failed to fetch home data', e);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    // Periodically refresh last_active_at via the read-only status endpoint
    // so activity from other devices (web, second phone) is reflected
    // without minting another heartbeat. 60s is conservative — enough to
    // catch cross-device activity, light enough on battery.
    useEffect(() => {
        const interval = setInterval(async () => {
            try {
                const status = await signalApi.getStatus();
                if (status.last_active_at) {
                    const fresh = new Date(status.last_active_at);
                    setLastActiveAt((prev) =>
                        prev && prev.getTime() >= fresh.getTime() ? prev : fresh,
                    );
                }
            } catch (e) {
                console.warn('status poll failed', e);
            }
        }, 60 * 1000);
        return () => clearInterval(interval);
    }, []);

    // Timer Logic — only runs after we have a real last_active_at from the server.
    useEffect(() => {
        if (!lastActiveAt) return;
        const calculateRemaining = () => {
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
            setToast({ message: '안부 확인 완료! 타이머가 연장됐어요.', tone: 'success' });
        } catch (e) {
            console.error('Check-in failed', e);
            await haptic.error();
            setToast({ message: '안부 확인에 실패했어요. 다시 시도해 주세요.', tone: 'info' });
        }
    };

    const handleFamilyShareTap = async () => {
        await haptic.selection();
        try {
            await upsellApi.logClick('family_share', 'home');
        } catch (e) {
            console.warn('Upsell click log failed', e);
        }
        // Alert.alert 가 RN Web 에서 invisible → inline Toast 로 대체.
        setToast({
            message: '가족공유는 준비 중이에요. 출시되면 가장 먼저 알려드릴게요.',
            tone: 'info',
        });
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

    const heritageTotal = heritageSummary?.total ?? 0;
    const heritageCardTitle =
        heritageTotal === 0
            ? '디지털 유산 정리를 시작해 보세요'
            : `오늘 한 가지 더 정리해 볼까요?`;
    const heritageCardSubtitle =
        heritageTotal === 0
            ? '추천 5가지 중 하나로 1분 안에 시작할 수 있어요.'
            : `현재 ${heritageTotal}개 항목이 안전하게 보관되어 있어요.`;

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
                    {lastActiveAt ? (
                        <CircularTimer
                            percentage={percentage}
                            remainingText={formatTime(remainingSeconds)}
                            subText="다음 확인까지"
                            status={getStatus()}
                        />
                    ) : (
                        <View style={styles.timerPlaceholder}>
                            <ActivityIndicator size="large" color={colors.primary} />
                            <Text
                                style={[
                                    typography.caption,
                                    { color: colors.text.caption, marginTop: spacing.md },
                                ]}
                            >
                                상태 확인 중…
                            </Text>
                        </View>
                    )}
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

                {/* Heritage daily nudge card (PRD §5.2) */}
                <TouchableOpacity
                    style={styles.heritageCard}
                    activeOpacity={0.85}
                    onPress={() => onNavigate?.('heritage')}
                    accessibilityRole="button"
                    accessibilityLabel="유산함으로 이동"
                >
                    <View style={styles.heritageHeader}>
                        <Text style={styles.heritageEmoji}>🗂️</Text>
                        <Text style={[typography.label, { color: colors.text.caption }]}>
                            Heritage Box
                        </Text>
                    </View>
                    <Text style={[typography.body1, { color: colors.text.primary, marginTop: 4 }]}>
                        {heritageCardTitle}
                    </Text>
                    <Text
                        style={[
                            typography.caption,
                            { color: colors.text.secondary, marginTop: spacing.xs },
                        ]}
                    >
                        {heritageCardSubtitle}
                    </Text>
                    <Text style={styles.heritageCta}>지금 정리하기 ›</Text>
                </TouchableOpacity>

                {/* Family share paywall card (PRD §2.1 goal 4) */}
                <TouchableOpacity
                    style={styles.upsellCard}
                    activeOpacity={0.85}
                    onPress={handleFamilyShareTap}
                    accessibilityRole="button"
                    accessibilityLabel="가족공유 알림 신청"
                >
                    <View style={styles.upsellHeader}>
                        <Text style={styles.heritageEmoji}>👨‍👩‍👧</Text>
                        <View style={styles.premiumBadge}>
                            <Text style={styles.premiumBadgeText}>Premium</Text>
                        </View>
                    </View>
                    <Text style={[typography.body1, { color: colors.text.primary, marginTop: 4 }]}>
                        가족과 함께 안전망 만들기
                    </Text>
                    <Text
                        style={[
                            typography.caption,
                            { color: colors.text.secondary, marginTop: spacing.xs },
                        ]}
                    >
                        보호자가 함께 자산을 관리하고 비상 시 더 빠르게 연결돼요.
                    </Text>
                    <Text style={styles.upsellCta}>알림 받기 ›</Text>
                </TouchableOpacity>

            </ScrollView>
            {toast ? (
                <Toast
                    message={toast.message}
                    tone={toast.tone}
                    onDone={() => setToast(null)}
                />
            ) : null}
        </ScreenLayout>
    );
};

const styles = StyleSheet.create({
    container: {
        flexGrow: 1,
        alignItems: 'center',
        paddingVertical: 24,
        paddingHorizontal: spacing.lg,
        paddingBottom: spacing.xxl + spacing.xl,
    },
    header: {
        width: '100%',
        marginBottom: 40,
        alignItems: 'flex-start',
    },
    timerContainer: {
        marginBottom: 40,
    },
    timerPlaceholder: {
        height: 280,
        width: 280,
        alignItems: 'center',
        justifyContent: 'center',
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
    heritageCard: {
        width: '100%',
        backgroundColor: colors.card,
        borderRadius: radius.lg,
        borderWidth: 1,
        borderColor: colors.border,
        padding: spacing.lg,
        marginTop: spacing.xl,
    },
    heritageHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: spacing.sm,
    },
    heritageEmoji: { fontSize: 22 },
    heritageCta: {
        ...typography.label,
        color: colors.primary,
        marginTop: spacing.md,
    },
    upsellCard: {
        width: '100%',
        backgroundColor: colors.card,
        borderRadius: radius.lg,
        borderWidth: 1,
        borderColor: colors.accent,
        padding: spacing.lg,
        marginTop: spacing.md,
    },
    upsellHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
    },
    premiumBadge: {
        backgroundColor: colors.accent,
        paddingHorizontal: spacing.sm,
        paddingVertical: 2,
        borderRadius: radius.full,
    },
    premiumBadgeText: {
        ...typography.caption,
        color: colors.text.inverse,
        fontWeight: '700',
    },
    upsellCta: {
        ...typography.label,
        color: colors.accent,
        marginTop: spacing.md,
    },
});
