import React, { useEffect, useMemo, useState } from 'react';
import {
    ActivityIndicator,
    Alert,
    RefreshControl,
    ScrollView,
    StyleSheet,
    Text,
    TextInput,
    TouchableOpacity,
    View,
} from 'react-native';

import { ScreenLayout } from '../components/ScreenLayout';
import type { Asset, AssetType } from '../api/client';
import { colors } from '../theme/colors';
import { radius, spacing } from '../theme/spacing';
import { typography } from '../theme/typography';
import { AssetFormScreen } from './AssetFormScreen';
import { AssetListItem } from '../features/heritage/components/AssetListItem';
import { useAssets } from '../features/heritage/hooks/useAssets';
import {
    ACTION_META,
    ASSET_TYPE_META,
    ASSET_TYPE_ORDER,
    EMPTY_STATE_SUGGESTIONS,
} from '../features/heritage/metadata';
import { haptic } from '../utils/haptics';

const SEARCH_DEBOUNCE_MS = 300;

export const HeritageBoxScreen = () => {
    const [searchInput, setSearchInput] = useState('');
    const [debouncedSearch, setDebouncedSearch] = useState('');
    const [typeFilter, setTypeFilter] = useState<AssetType | null>(null);

    useEffect(() => {
        const handle = setTimeout(
            () => setDebouncedSearch(searchInput),
            SEARCH_DEBOUNCE_MS,
        );
        return () => clearTimeout(handle);
    }, [searchInput]);

    const {
        assets,
        summary,
        isLoading,
        error,
        refresh,
        createAsset,
        updateAsset,
        deleteAsset,
    } = useAssets({ search: debouncedSearch, typeFilter });

    const [mode, setMode] = useState<
        { kind: 'list' } | { kind: 'create'; suggested?: Partial<Asset> } | { kind: 'edit'; asset: Asset }
    >({ kind: 'list' });

    const isFilterActive = !!debouncedSearch || typeFilter !== null;

    const grouped = useMemo(() => {
        const m: Record<string, Asset[]> = {};
        for (const a of assets) {
            (m[a.type] = m[a.type] || []).push(a);
        }
        return m;
    }, [assets]);

    if (mode.kind === 'create') {
        return (
            <AssetFormScreen
                initial={mode.suggested}
                onCancel={() => setMode({ kind: 'list' })}
                onSubmit={async (payload) => {
                    await createAsset(payload);
                    await haptic.success();
                    setMode({ kind: 'list' });
                }}
            />
        );
    }

    if (mode.kind === 'edit') {
        return (
            <AssetFormScreen
                initial={mode.asset}
                editingId={mode.asset.id}
                onCancel={() => setMode({ kind: 'list' })}
                onSubmit={async (payload) => {
                    await updateAsset(mode.asset.id, payload);
                    await haptic.success();
                    setMode({ kind: 'list' });
                }}
                onDelete={async () => {
                    Alert.alert(
                        '항목 삭제',
                        '이 자산을 인벤토리에서 삭제할까요?',
                        [
                            { text: '취소', style: 'cancel' },
                            {
                                text: '삭제',
                                style: 'destructive',
                                onPress: async () => {
                                    await deleteAsset(mode.asset.id);
                                    await haptic.warning();
                                    setMode({ kind: 'list' });
                                },
                            },
                        ],
                    );
                }}
            />
        );
    }

    return (
        <ScreenLayout>
            <ScrollView
                contentContainerStyle={styles.container}
                refreshControl={
                    <RefreshControl refreshing={isLoading} onRefresh={refresh} />
                }
            >
                <View style={styles.header}>
                    <Text style={[typography.heading2, { color: colors.text.primary }]}>
                        유산함
                    </Text>
                    <Text
                        style={[typography.caption, { color: colors.text.secondary, marginTop: 4 }]}
                    >
                        떠난 뒤를 미리 정리해 두세요. 한 번에 한 가지면 충분해요.
                    </Text>
                </View>

                {summary && summary.total > 0 ? (
                    <View style={styles.filterBlock}>
                        <View style={styles.searchRow}>
                            <Text style={styles.searchIcon}>🔍</Text>
                            <TextInput
                                value={searchInput}
                                onChangeText={setSearchInput}
                                placeholder="이름으로 검색"
                                placeholderTextColor={colors.text.caption}
                                style={styles.searchInput}
                                autoCorrect={false}
                                autoCapitalize="none"
                                returnKeyType="search"
                            />
                            {searchInput.length > 0 ? (
                                <TouchableOpacity
                                    onPress={() => setSearchInput('')}
                                    accessibilityRole="button"
                                    accessibilityLabel="검색어 지우기"
                                    hitSlop={8}
                                >
                                    <Text style={styles.searchClear}>✕</Text>
                                </TouchableOpacity>
                            ) : null}
                        </View>

                        <ScrollView
                            horizontal
                            showsHorizontalScrollIndicator={false}
                            contentContainerStyle={styles.chipRow}
                        >
                            <TouchableOpacity
                                key="all"
                                style={[
                                    styles.chip,
                                    typeFilter === null && styles.chipActive,
                                ]}
                                onPress={() => setTypeFilter(null)}
                                activeOpacity={0.7}
                                accessibilityRole="button"
                            >
                                <Text
                                    style={[
                                        styles.chipLabel,
                                        typeFilter === null && styles.chipLabelActive,
                                    ]}
                                >
                                    전체
                                </Text>
                            </TouchableOpacity>
                            {ASSET_TYPE_ORDER.map((t) => {
                                const count = summary.by_type[t] ?? 0;
                                if (count === 0) return null;
                                const meta = ASSET_TYPE_META[t];
                                const active = typeFilter === t;
                                return (
                                    <TouchableOpacity
                                        key={t}
                                        style={[styles.chip, active && styles.chipActive]}
                                        onPress={() => setTypeFilter(active ? null : t)}
                                        activeOpacity={0.7}
                                        accessibilityRole="button"
                                    >
                                        <Text style={styles.chipEmoji}>{meta.emoji}</Text>
                                        <Text
                                            style={[
                                                styles.chipLabel,
                                                active && styles.chipLabelActive,
                                            ]}
                                        >
                                            {meta.label} {count}
                                        </Text>
                                    </TouchableOpacity>
                                );
                            })}
                        </ScrollView>
                    </View>
                ) : null}

                {summary && summary.total > 0 ? (
                    <View style={styles.summaryCard}>
                        <Text style={[typography.label, { color: colors.text.caption }]}>
                            전체
                        </Text>
                        <Text
                            style={[typography.heading1, { color: colors.primary, marginTop: 2 }]}
                        >
                            {summary.total}
                            <Text style={[typography.body2, { color: colors.text.secondary }]}>
                                {' '}
                                항목
                            </Text>
                        </Text>
                        <View style={styles.summaryActionRow}>
                            {Object.entries(summary.by_action).map(([action, count]) => {
                                if (!count) return null;
                                const meta = ACTION_META[action as keyof typeof ACTION_META];
                                if (!meta) return null;
                                return (
                                    <View key={action} style={styles.summaryChip}>
                                        <Text style={styles.summaryChipEmoji}>{meta.emoji}</Text>
                                        <Text
                                            style={[
                                                typography.caption,
                                                { color: colors.text.secondary },
                                            ]}
                                        >
                                            {meta.label} {count}
                                        </Text>
                                    </View>
                                );
                            })}
                        </View>
                    </View>
                ) : null}

                {error ? (
                    <View style={styles.errorBanner}>
                        <Text style={[typography.body2, { color: colors.danger }]}>{error}</Text>
                    </View>
                ) : null}

                {isLoading && assets.length === 0 ? (
                    <View style={styles.loadingWrap}>
                        <ActivityIndicator size="large" color={colors.primary} />
                    </View>
                ) : assets.length === 0 && isFilterActive ? (
                    <View style={styles.emptyWrap}>
                        <Text style={styles.emptyEmoji}>🔍</Text>
                        <Text
                            style={[
                                typography.body1,
                                { color: colors.text.primary, textAlign: 'center' },
                            ]}
                        >
                            조건에 맞는 자산이 없어요.
                        </Text>
                        <Text
                            style={[
                                typography.caption,
                                {
                                    color: colors.text.caption,
                                    textAlign: 'center',
                                    marginTop: spacing.xs,
                                    marginBottom: spacing.lg,
                                },
                            ]}
                        >
                            검색어 또는 필터를 바꿔 보세요.
                        </Text>
                        <TouchableOpacity
                            style={styles.clearFiltersButton}
                            onPress={() => {
                                setSearchInput('');
                                setTypeFilter(null);
                            }}
                            activeOpacity={0.7}
                            accessibilityRole="button"
                        >
                            <Text style={[typography.body2, { color: colors.primary }]}>
                                필터 초기화
                            </Text>
                        </TouchableOpacity>
                    </View>
                ) : assets.length === 0 ? (
                    <View style={styles.emptyWrap}>
                        <Text style={styles.emptyEmoji}>📦</Text>
                        <Text
                            style={[
                                typography.body1,
                                { color: colors.text.primary, textAlign: 'center' },
                            ]}
                        >
                            아직 정리한 자산이 없어요.
                        </Text>
                        <Text
                            style={[
                                typography.caption,
                                {
                                    color: colors.text.caption,
                                    textAlign: 'center',
                                    marginTop: spacing.xs,
                                    marginBottom: spacing.lg,
                                },
                            ]}
                        >
                            아래 추천 중 하나로 시작해 보세요.
                        </Text>

                        {EMPTY_STATE_SUGGESTIONS.map((s) => (
                            <TouchableOpacity
                                key={s.name}
                                style={styles.suggestion}
                                activeOpacity={0.7}
                                onPress={() =>
                                    setMode({
                                        kind: 'create',
                                        suggested: {
                                            name: s.name,
                                            type: s.type,
                                            action_on_death: s.action_on_death,
                                        } as Partial<Asset>,
                                    })
                                }
                            >
                                <Text style={styles.suggestionEmoji}>
                                    {ASSET_TYPE_META[s.type].emoji}
                                </Text>
                                <Text style={[typography.body2, { color: colors.text.primary }]}>
                                    {s.name}
                                </Text>
                                <Text style={[typography.caption, { color: colors.text.caption }]}>
                                    추가하기 ›
                                </Text>
                            </TouchableOpacity>
                        ))}
                    </View>
                ) : (
                    Object.entries(grouped).map(([type, items]) => (
                        <View key={type} style={{ marginBottom: spacing.lg }}>
                            <Text style={styles.groupTitle}>
                                {ASSET_TYPE_META[type as keyof typeof ASSET_TYPE_META]?.label ??
                                    type}
                                <Text style={[typography.caption, { color: colors.text.caption }]}>
                                    {'  '}
                                    {items.length}
                                </Text>
                            </Text>
                            {items.map((asset) => (
                                <AssetListItem
                                    key={asset.id}
                                    asset={asset}
                                    onPress={() => setMode({ kind: 'edit', asset })}
                                />
                            ))}
                        </View>
                    ))
                )}
            </ScrollView>

            <TouchableOpacity
                accessibilityRole="button"
                accessibilityLabel="자산 추가"
                style={styles.fab}
                activeOpacity={0.85}
                onPress={() => setMode({ kind: 'create' })}
            >
                <Text style={styles.fabPlus}>＋</Text>
            </TouchableOpacity>
        </ScreenLayout>
    );
};

const styles = StyleSheet.create({
    container: {
        flexGrow: 1,
        paddingVertical: spacing.lg,
        paddingBottom: spacing.xxl + spacing.xl,
    },
    header: { marginBottom: spacing.lg },
    summaryCard: {
        backgroundColor: colors.card,
        borderRadius: radius.lg,
        padding: spacing.lg,
        marginBottom: spacing.lg,
        borderWidth: 1,
        borderColor: colors.border,
    },
    summaryActionRow: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: spacing.sm,
        marginTop: spacing.md,
    },
    summaryChip: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: spacing.sm,
        paddingVertical: 4,
        borderRadius: radius.full,
        backgroundColor: colors.background,
    },
    summaryChipEmoji: { fontSize: 14, marginRight: 4 },
    filterBlock: { marginBottom: spacing.md },
    searchRow: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: colors.card,
        borderRadius: radius.md,
        borderWidth: 1,
        borderColor: colors.border,
        paddingHorizontal: spacing.md,
        paddingVertical: spacing.sm,
        gap: spacing.sm,
    },
    searchIcon: { fontSize: 14 },
    searchInput: {
        flex: 1,
        ...typography.body2,
        color: colors.text.primary,
        paddingVertical: 0,
    },
    searchClear: {
        ...typography.body2,
        color: colors.text.caption,
        paddingHorizontal: spacing.xs,
    },
    chipRow: {
        flexDirection: 'row',
        gap: spacing.sm,
        paddingVertical: spacing.sm,
        paddingRight: spacing.lg,
    },
    chip: {
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: spacing.md,
        paddingVertical: 6,
        borderRadius: radius.full,
        backgroundColor: colors.card,
        borderWidth: 1,
        borderColor: colors.border,
        gap: 4,
    },
    chipActive: {
        backgroundColor: colors.primary,
        borderColor: colors.primary,
    },
    chipEmoji: { fontSize: 13 },
    chipLabel: {
        ...typography.caption,
        color: colors.text.secondary,
    },
    chipLabelActive: { color: colors.text.inverse, fontWeight: '600' },
    clearFiltersButton: {
        alignSelf: 'center',
        paddingHorizontal: spacing.lg,
        paddingVertical: spacing.sm,
        borderRadius: radius.full,
        borderWidth: 1,
        borderColor: colors.primary,
    },
    errorBanner: {
        backgroundColor: '#FCEBEA',
        borderRadius: radius.md,
        padding: spacing.md,
        marginBottom: spacing.md,
    },
    loadingWrap: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
        paddingVertical: spacing.xxl,
    },
    emptyWrap: {
        alignItems: 'stretch',
        marginTop: spacing.lg,
    },
    emptyEmoji: { fontSize: 48, textAlign: 'center', marginBottom: spacing.md },
    suggestion: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: colors.card,
        borderRadius: radius.md,
        padding: spacing.md,
        marginBottom: spacing.sm,
        borderWidth: 1,
        borderColor: colors.border,
        gap: spacing.md,
    },
    suggestionEmoji: { fontSize: 20 },
    groupTitle: {
        ...typography.label,
        color: colors.text.secondary,
        marginBottom: spacing.sm,
        marginLeft: spacing.xs,
    },
    fab: {
        position: 'absolute',
        right: spacing.lg,
        bottom: spacing.lg,
        width: 60,
        height: 60,
        borderRadius: radius.full,
        backgroundColor: colors.primary,
        alignItems: 'center',
        justifyContent: 'center',
        shadowColor: colors.black,
        shadowOpacity: 0.18,
        shadowOffset: { width: 0, height: 4 },
        shadowRadius: 8,
        elevation: 5,
    },
    fabPlus: {
        color: colors.text.inverse,
        fontSize: 28,
        lineHeight: 28,
        marginTop: -2,
    },
});
