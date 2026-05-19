import React, { useState, useEffect, useCallback } from 'react';
import {
    View,
    Text,
    StyleSheet,
    Switch,
    TouchableOpacity,
    ScrollView,
    ActivityIndicator,
    Alert,
} from 'react-native';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import {
    accountApi,
    type DeletionStatus,
    describeError,
    settingsApi,
    MonitoringPolicy,
    SensitivityLevel,
} from '../api/client';
import { useAuth } from '../context/AuthContext';

interface SettingsScreenProps {
    onBack?: () => void;
}

const SENSITIVITY_OPTIONS: { value: SensitivityLevel; label: string; description: string }[] = [
    { value: 'relaxed', label: '느슨함', description: '24시간 이상 비활동 시 알림' },
    { value: 'normal', label: '보통', description: '12시간 이상 비활동 시 알림' },
    { value: 'strict', label: '엄격함', description: '6시간 이상 비활동 시 알림' },
];

export const SettingsScreen: React.FC<SettingsScreenProps> = ({ onBack }) => {
    const { logout } = useAuth();
    const [policy, setPolicy] = useState<MonitoringPolicy | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [deletionStatus, setDeletionStatus] = useState<DeletionStatus | null>(null);

    // Load policy on mount
    useEffect(() => {
        loadPolicy();
    }, []);

    const handleRequestDeletion = useCallback(() => {
        Alert.alert(
            '계정 삭제',
            '계정 삭제를 요청하면 30일 후 모든 데이터가 영구 삭제됩니다.\n그 전까지 언제든 복구할 수 있어요.',
            [
                { text: '취소', style: 'cancel' },
                {
                    text: '삭제 요청',
                    style: 'destructive',
                    onPress: async () => {
                        try {
                            const status = await accountApi.requestDeletion();
                            setDeletionStatus(status);
                        } catch (e) {
                            Alert.alert('삭제 요청 실패', describeError(e, '삭제 요청에 실패했어요.'));
                        }
                    },
                },
            ],
        );
    }, []);

    const handleRestore = useCallback(async () => {
        try {
            const status = await accountApi.restore();
            setDeletionStatus(status);
        } catch (e) {
            Alert.alert('복구 실패', describeError(e, '복구에 실패했어요.'));
        }
    }, []);

    const loadPolicy = async () => {
        try {
            setLoading(true);
            const data = await settingsApi.getPolicy();
            setPolicy(data);
        } catch (error) {
            Alert.alert('설정 불러오기 실패', describeError(error, '설정을 불러오지 못했어요.'));
        } finally {
            setLoading(false);
        }
    };

    const updatePolicy = useCallback(async (updates: Partial<MonitoringPolicy>) => {
        if (!policy) return;

        try {
            setSaving(true);
            const updated = await settingsApi.updatePolicy(updates);
            setPolicy(updated);
        } catch (error) {
            Alert.alert('저장 실패', describeError(error, '설정 저장에 실패했어요.'));
        } finally {
            setSaving(false);
        }
    }, [policy]);

    const handleSensitivityChange = (sensitivity: SensitivityLevel) => {
        updatePolicy({ sensitivity });
    };

    const handleToggleMonitoring = (value: boolean) => {
        updatePolicy({ is_active: value });
    };

    const handleToggleEscalation = (value: boolean) => {
        updatePolicy({ escalation_enabled: value });
    };

    if (loading) {
        return (
            <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color={colors.primary} />
            </View>
        );
    }

    if (!policy) {
        return (
            <View style={styles.errorContainer}>
                <Text style={styles.errorText}>설정을 불러올 수 없습니다.</Text>
            </View>
        );
    }

    return (
        <ScrollView style={styles.container} contentContainerStyle={styles.contentContainer}>
            {/* Header */}
            <View style={styles.header}>
                {onBack && (
                    <TouchableOpacity onPress={onBack} style={styles.backButton}>
                        <Text style={styles.backButtonText}>← 뒤로</Text>
                    </TouchableOpacity>
                )}
                <Text style={styles.title}>모니터링 설정</Text>
            </View>

            {/* Master Switch */}
            <View style={styles.section}>
                <View style={styles.row}>
                    <View style={styles.rowText}>
                        <Text style={styles.rowTitle}>모니터링 활성화</Text>
                        <Text style={styles.rowDescription}>비활동 감지 기능을 켜거나 끕니다</Text>
                    </View>
                    <Switch
                        value={policy.is_active}
                        onValueChange={handleToggleMonitoring}
                        trackColor={{ false: colors.text.caption, true: colors.primary }}
                        disabled={saving}
                    />
                </View>
            </View>

            {/* Sensitivity */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>민감도</Text>
                {SENSITIVITY_OPTIONS.map((option) => (
                    <TouchableOpacity
                        key={option.value}
                        style={[
                            styles.optionCard,
                            policy.sensitivity === option.value && styles.optionCardActive,
                        ]}
                        onPress={() => handleSensitivityChange(option.value)}
                        disabled={saving}
                    >
                        <View style={styles.optionRadio}>
                            {policy.sensitivity === option.value && (
                                <View style={styles.optionRadioInner} />
                            )}
                        </View>
                        <View style={styles.optionContent}>
                            <Text style={styles.optionLabel}>{option.label}</Text>
                            <Text style={styles.optionDescription}>{option.description}</Text>
                        </View>
                    </TouchableOpacity>
                ))}
            </View>

            {/* Quiet Hours Info */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>안심 시간</Text>
                <View style={styles.infoCard}>
                    <Text style={styles.infoText}>
                        {policy.quiet_start.slice(0, 5)} ~ {policy.quiet_end.slice(0, 5)}
                    </Text>
                    <Text style={styles.infoDescription}>
                        이 시간 동안에는 비활동 알림이 발송되지 않습니다
                    </Text>
                </View>
            </View>

            {/* Escalation Toggle */}
            <View style={styles.section}>
                <View style={styles.row}>
                    <View style={styles.rowText}>
                        <Text style={styles.rowTitle}>보호자 에스컬레이션</Text>
                        <Text style={styles.rowDescription}>
                            응답이 없을 경우 보호자에게 알림을 보냅니다
                        </Text>
                    </View>
                    <Switch
                        value={policy.escalation_enabled}
                        onValueChange={handleToggleEscalation}
                        trackColor={{ false: colors.text.caption, true: colors.primary }}
                        disabled={saving}
                    />
                </View>
            </View>

            {saving && (
                <View style={styles.savingOverlay}>
                    <ActivityIndicator size="small" color={colors.primary} />
                    <Text style={styles.savingText}>저장 중...</Text>
                </View>
            )}

            {/* 계정 (Account) */}
            <View style={[styles.section, { marginTop: 32 }]}>
                <Text style={styles.sectionTitle}>계정</Text>
                <TouchableOpacity
                    style={styles.linkRow}
                    onPress={async () => {
                        await logout();
                    }}
                >
                    <Text style={[typography.body1, { color: colors.text.primary }]}>로그아웃</Text>
                </TouchableOpacity>
            </View>

            {/* 위험 영역 (PIPA 잊혀질 권리) */}
            <View style={[styles.section, styles.dangerZone]}>
                <Text style={styles.dangerTitle}>위험 영역</Text>
                {deletionStatus?.deletion_requested_at ? (
                    <View>
                        <Text style={[typography.body2, { color: colors.danger }]}>
                            계정 삭제가 예약되었습니다.
                        </Text>
                        <Text
                            style={[
                                typography.caption,
                                { color: colors.text.secondary, marginTop: 4 },
                            ]}
                        >
                            남은 기간: {Math.ceil((deletionStatus.seconds_remaining ?? 0) / 86400)}
                            일 (영구 삭제까지). 그 전까지 언제든 복구할 수 있어요.
                        </Text>
                        <TouchableOpacity
                            style={[styles.dangerBtn, { marginTop: 12 }]}
                            onPress={handleRestore}
                        >
                            <Text style={[typography.body1, { color: colors.primary }]}>
                                삭제 요청 취소
                            </Text>
                        </TouchableOpacity>
                    </View>
                ) : (
                    <TouchableOpacity style={styles.dangerBtn} onPress={handleRequestDeletion}>
                        <Text style={[typography.body1, { color: colors.danger }]}>
                            계정 삭제 요청
                        </Text>
                    </TouchableOpacity>
                )}
                <Text style={[typography.caption, { color: colors.text.caption, marginTop: 12 }]}>
                    개인정보보호법(PIPA)에 따라 30일 유예 기간을 둡니다.
                </Text>
            </View>
        </ScrollView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: colors.background,
    },
    contentContainer: {
        padding: 20,
        paddingBottom: 40,
    },
    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: colors.background,
    },
    errorContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: colors.background,
    },
    errorText: {
        ...typography.body1,
        color: colors.danger,
    },
    header: {
        marginBottom: 24,
    },
    backButton: {
        marginBottom: 12,
    },
    backButtonText: {
        ...typography.body1,
        color: colors.primary,
    },
    title: {
        ...typography.heading1,
        color: colors.text.primary,
    },
    section: {
        marginBottom: 24,
    },
    sectionTitle: {
        ...typography.body1,
        color: colors.text.primary,
        fontWeight: '600',
        marginBottom: 12,
    },
    row: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        backgroundColor: colors.white,
        padding: 16,
        borderRadius: 12,
    },
    rowText: {
        flex: 1,
        marginRight: 12,
    },
    rowTitle: {
        ...typography.body1,
        color: colors.text.primary,
        fontWeight: '600',
    },
    rowDescription: {
        ...typography.caption,
        color: colors.text.secondary,
        marginTop: 4,
    },
    optionCard: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: colors.white,
        padding: 16,
        borderRadius: 12,
        marginBottom: 8,
        borderWidth: 2,
        borderColor: colors.transparent,
    },
    optionCardActive: {
        borderColor: colors.primary,
    },
    optionRadio: {
        width: 20,
        height: 20,
        borderRadius: 10,
        borderWidth: 2,
        borderColor: colors.text.caption,
        marginRight: 12,
        justifyContent: 'center',
        alignItems: 'center',
    },
    optionRadioInner: {
        width: 10,
        height: 10,
        borderRadius: 5,
        backgroundColor: colors.primary,
    },
    optionContent: {
        flex: 1,
    },
    optionLabel: {
        ...typography.body1,
        color: colors.text.primary,
        fontWeight: '600',
    },
    optionDescription: {
        ...typography.caption,
        color: colors.text.secondary,
        marginTop: 2,
    },
    infoCard: {
        backgroundColor: colors.white,
        padding: 16,
        borderRadius: 12,
    },
    infoText: {
        ...typography.heading2,
        color: colors.primary,
        textAlign: 'center',
    },
    infoDescription: {
        ...typography.caption,
        color: colors.text.secondary,
        textAlign: 'center',
        marginTop: 8,
    },
    savingOverlay: {
        flexDirection: 'row',
        justifyContent: 'center',
        alignItems: 'center',
        padding: 12,
    },
    savingText: {
        ...typography.caption,
        color: colors.text.secondary,
        marginLeft: 8,
    },
    linkRow: {
        backgroundColor: colors.white,
        padding: 16,
        borderRadius: 12,
    },
    dangerZone: {
        backgroundColor: colors.white,
        padding: 16,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: colors.danger + '40',
    },
    dangerTitle: {
        ...typography.body1,
        color: colors.danger,
        fontWeight: '600',
        marginBottom: 12,
    },
    dangerBtn: {
        paddingVertical: 12,
        alignItems: 'flex-start',
    },
});
