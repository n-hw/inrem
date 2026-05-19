import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { colors } from '../../../theme/colors';
import { radius, spacing } from '../../../theme/spacing';
import { typography } from '../../../theme/typography';

interface Option<T extends string> {
    value: T;
    label: string;
    emoji?: string;
    color?: string;
}

interface Props<T extends string> {
    options: Option<T>[];
    value: T;
    onChange: (value: T) => void;
}

/**
 * Lightweight segmented control / option list — used for picking enum-ish
 * values (action_on_death, asset type) in forms without pulling in extra deps.
 */
export function SegmentedControl<T extends string>({
    options,
    value,
    onChange,
}: Props<T>) {
    return (
        <View style={styles.wrap}>
            {options.map((opt) => {
                const selected = opt.value === value;
                const tint = opt.color ?? colors.primary;
                return (
                    <TouchableOpacity
                        key={opt.value}
                        accessibilityRole="radio"
                        accessibilityState={{ selected }}
                        accessibilityLabel={opt.label}
                        style={[
                            styles.pill,
                            {
                                borderColor: selected ? tint : colors.border,
                                backgroundColor: selected ? `${tint}14` : colors.card,
                            },
                        ]}
                        onPress={() => onChange(opt.value)}
                        activeOpacity={0.7}
                    >
                        {opt.emoji ? <Text style={styles.emoji}>{opt.emoji}</Text> : null}
                        <Text
                            style={[
                                typography.label,
                                {
                                    color: selected ? tint : colors.text.secondary,
                                    fontSize: 14,
                                },
                            ]}
                        >
                            {opt.label}
                        </Text>
                    </TouchableOpacity>
                );
            })}
        </View>
    );
}

const styles = StyleSheet.create({
    wrap: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: spacing.sm,
    },
    pill: {
        flexDirection: 'row',
        alignItems: 'center',
        borderRadius: radius.full,
        borderWidth: 1,
        paddingHorizontal: spacing.md,
        paddingVertical: spacing.sm,
        minHeight: 44, // accessibility touch target
    },
    emoji: { marginRight: 6, fontSize: 14 },
});
