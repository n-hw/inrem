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
import { settingsApi, MonitoringPolicy, SensitivityLevel } from '../api/client';

interface SettingsScreenProps {
    onBack?: () => void;
}

const SENSITIVITY_OPTIONS: { value: SensitivityLevel; label: string; description: string }[] = [
    { value: 'relaxed', label: '느슨함', description: '24시간 이상 비활동 시 알림' },
    { value: 'normal', label: '보통', description: '12시간 이상 비활동 시 알림' },
    { value: 'strict', label: '엄격함', description: '6시간 이상 비활동 시 알림' },
];

export const SettingsScreen: React.FC<SettingsScreenProps> = ({ onBack }) => {
    const [policy, setPolicy] = useState<MonitoringPolicy | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    // Load policy on mount
    useEffect(() => {
        loadPolicy();
    }, []);

    const loadPolicy = async () => {
        try {
            setLoading(true);
            const data = await settingsApi.getPolicy();
            setPolicy(data);
        } catch (_error) {
            Alert.alert('오류', '설정을 불러오는데 실패했습니다.');
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
        } catch (_error) {
            Alert.alert('오류', '설정 저장에 실패했습니다.');
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
});
