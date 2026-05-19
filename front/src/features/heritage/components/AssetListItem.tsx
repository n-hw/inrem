import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import type { Asset } from '../../../api/client';
import { colors } from '../../../theme/colors';
import { radius, spacing } from '../../../theme/spacing';
import { typography } from '../../../theme/typography';
import { ACTION_META, ASSET_TYPE_META } from '../metadata';

interface Props {
    asset: Asset;
    onPress?: (asset: Asset) => void;
}

export const AssetListItem = ({ asset, onPress }: Props) => {
    const typeMeta = ASSET_TYPE_META[asset.type];
    const actionMeta = ACTION_META[asset.action_on_death];

    return (
        <TouchableOpacity
            accessibilityRole="button"
            accessibilityLabel={`${asset.name}, ${typeMeta.label}, ${actionMeta.label} 처리`}
            onPress={() => onPress?.(asset)}
            style={styles.row}
            activeOpacity={0.7}
        >
            <View style={styles.iconWrap}>
                <Text style={styles.icon}>{typeMeta.emoji}</Text>
            </View>

            <View style={styles.body}>
                <View style={styles.titleRow}>
                    <Text
                        style={[typography.body1, { color: colors.text.primary }]}
                        numberOfLines={1}
                    >
                        {asset.name}
                    </Text>
                    {asset.has_secret ? (
                        <Text style={styles.lock} accessibilityLabel="암호화 저장됨">
                            🔒
                        </Text>
                    ) : null}
                </View>
                <Text
                    style={[typography.caption, { color: colors.text.caption }]}
                    numberOfLines={1}
                >
                    {typeMeta.label}
                    {asset.identifier ? `  ·  ${asset.identifier}` : ''}
                </Text>
            </View>

            <View
                style={[
                    styles.actionBadge,
                    { borderColor: actionMeta.color, backgroundColor: `${actionMeta.color}14` },
                ]}
            >
                <Text style={styles.actionEmoji}>{actionMeta.emoji}</Text>
                <Text style={[styles.actionLabel, { color: actionMeta.color }]}>
                    {actionMeta.label}
                </Text>
            </View>
        </TouchableOpacity>
    );
};

const styles = StyleSheet.create({
    row: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: colors.card,
        borderRadius: radius.md,
        padding: spacing.md,
        marginBottom: spacing.sm,
        borderWidth: 1,
        borderColor: colors.border,
    },
    iconWrap: {
        width: 44,
        height: 44,
        borderRadius: radius.full,
        backgroundColor: colors.background,
        alignItems: 'center',
        justifyContent: 'center',
        marginRight: spacing.md,
    },
    icon: { fontSize: 22 },
    body: { flex: 1 },
    titleRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 2,
    },
    lock: { marginLeft: spacing.xs, fontSize: 14 },
    actionBadge: {
        flexDirection: 'row',
        alignItems: 'center',
        borderRadius: radius.full,
        borderWidth: 1,
        paddingHorizontal: spacing.sm,
        paddingVertical: 4,
        marginLeft: spacing.sm,
    },
    actionEmoji: { fontSize: 12, marginRight: 4 },
    actionLabel: { fontSize: 12, fontFamily: 'Pretendard-Medium' },
});
