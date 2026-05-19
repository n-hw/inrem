import React, { useState, useEffect, useCallback } from 'react';
import {
    Alert,
    RefreshControl,
    ScrollView,
    StyleSheet,
    Text,
    TouchableOpacity,
    View,
} from 'react-native';
import { ScreenLayout } from '../components/ScreenLayout';
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
    const [isLoading, setIsLoading] = useState(false);
    const [thresholdHours, setThresholdHours] = useState(12);
    const [lastActiveAt, setLastActiveAt] = useState<Date>(new Date());
    const [remainingSeconds, setRemainingSeconds] = useState(0);
    const [heritageSummary, setHeritageSummary] = useState<AssetSummary | null>(null);

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

    const handleFamilyShareTap = async () => {
        await haptic.selection();
        try {
            await upsellApi.logClick('family_share', 'home');
        } catch (e) {
            console.warn('Upsell click log failed', e);
        }
        Alert.alert(
            '곧 만나요',
            '가족공유 기능은 준비 중이에요. 출시되면 가장 먼저 알려드릴게요.',
            [{ text: '확인', style: 'default' }],
        );
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
