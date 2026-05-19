import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { colors } from '../theme/colors';
import { spacing } from '../theme/spacing';
import { typography } from '../theme/typography';

export interface TabItem {
    key: string;
    label: string;
    emoji: string;
}

interface Props {
    items: TabItem[];
    activeKey: string;
    onChange: (key: string) => void;
}

/**
 * Lightweight bottom tab bar — no extra navigation dependency required.
 * Used by MainTabsScreen to switch between Pulse / Heritage / Settings.
 */
export const BottomTabBar = ({ items, activeKey, onChange }: Props) => {
    const insets = useSafeAreaInsets();

    return (
        <View
            style={[
                styles.bar,
                { paddingBottom: Math.max(insets.bottom, spacing.sm) },
            ]}
        >
            {items.map((item) => {
                const active = item.key === activeKey;
                return (
                    <TouchableOpacity
                        key={item.key}
                        accessibilityRole="tab"
                        accessibilityState={{ selected: active }}
                        accessibilityLabel={item.label}
                        style={styles.tab}
                        onPress={() => onChange(item.key)}
                        activeOpacity={0.7}
                    >
                        <Text
                            style={[
                                styles.emoji,
                                active ? styles.emojiActive : styles.emojiInactive,
                            ]}
                        >
                            {item.emoji}
                        </Text>
                        <Text
                            style={[
                                typography.label,
                                {
                                    color: active ? colors.primary : colors.text.caption,
                                    fontSize: 12,
                                    marginTop: 2,
                                },
                            ]}
                        >
                            {item.label}
                        </Text>
                    </TouchableOpacity>
                );
            })}
        </View>
    );
};

const styles = StyleSheet.create({
    bar: {
        flexDirection: 'row',
        backgroundColor: colors.card,
        borderTopWidth: 1,
        borderTopColor: colors.border,
        paddingTop: spacing.sm,
    },
    tab: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 44,
    },
    emoji: { fontSize: 22 },
    emojiActive: { opacity: 1 },
    emojiInactive: { opacity: 0.55 },
});
