import React, { useState } from 'react';
import {
    KeyboardAvoidingView,
    Platform,
    ScrollView,
    StyleSheet,
    Text,
    TextInput,
    TouchableOpacity,
    View,
} from 'react-native';

import { ScreenLayout } from '../components/ScreenLayout';
import type {
    ActionOnDeath,
    Asset,
    AssetCreatePayload,
    AssetType,
    AssetUpdatePayload,
} from '../api/client';
import { colors } from '../theme/colors';
import { radius, spacing } from '../theme/spacing';
import { typography } from '../theme/typography';
import { SegmentedControl } from '../features/heritage/components/SegmentedControl';
import {
    ACTION_META,
    ACTION_ORDER,
    ASSET_TYPE_META,
    ASSET_TYPE_ORDER,
} from '../features/heritage/metadata';

interface Props {
    initial?: Partial<Asset> | null;
    editingId?: string;
    onCancel: () => void;
    onSubmit: (payload: AssetCreatePayload & AssetUpdatePayload) => Promise<void>;
    onDelete?: () => void;
}

export const AssetFormScreen = ({
    initial,
    editingId,
    onCancel,
    onSubmit,
    onDelete,
}: Props) => {
    const [name, setName] = useState<string>(initial?.name ?? '');
    const [type, setType] = useState<AssetType>(initial?.type ?? 'custom');
    const [identifier, setIdentifier] = useState<string>(initial?.identifier ?? '');
    const [action, setAction] = useState<ActionOnDeath>(
        initial?.action_on_death ?? 'keep_private',
    );
    const [note, setNote] = useState<string>(initial?.note ?? '');
    const [secret, setSecret] = useState<string>('');
    const [showSecret, setShowSecret] = useState<boolean>(false);
    const [clearSecret, setClearSecret] = useState<boolean>(false);
    const [submitting, setSubmitting] = useState<boolean>(false);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const isEditing = Boolean(editingId);
    const hadSecret = Boolean(initial?.has_secret);
    const canSubmit = name.trim().length > 0 && !submitting;

    const handleSubmit = async () => {
        if (!canSubmit) return;
        setSubmitting(true);
        setErrorMessage(null);
        try {
            await onSubmit({
                name: name.trim(),
                type,
                identifier: identifier.trim() || null,
                action_on_death: action,
                note: note.trim() || null,
                secret: secret.length > 0 ? secret : undefined,
                clear_secret: clearSecret || undefined,
            });
        } catch (e) {
            console.error('AssetFormScreen submit failed', e);
            setErrorMessage('저장에 실패했어요. 잠시 후 다시 시도해 주세요.');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <ScreenLayout>
            <KeyboardAvoidingView
                behavior={Platform.OS === 'ios' ? 'padding' : undefined}
                style={{ flex: 1 }}
            >
                <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
                    <View style={styles.headerRow}>
                        <TouchableOpacity
                            accessibilityRole="button"
                            accessibilityLabel="닫기"
                            onPress={onCancel}
                            style={styles.iconBtn}
                        >
                            <Text style={styles.iconBtnText}>✕</Text>
                        </TouchableOpacity>
                        <Text style={[typography.heading2, { color: colors.text.primary }]}>
                            {isEditing ? '자산 수정' : '새 자산'}
                        </Text>
                        <View style={styles.iconBtn} />
                    </View>

                    {/* Name */}
                    <Text style={styles.label}>이름</Text>
                    <TextInput
                        style={styles.input}
                        value={name}
                        onChangeText={setName}
                        placeholder="예: Instagram 계정"
                        placeholderTextColor={colors.text.caption}
                        accessibilityLabel="자산 이름"
                    />

                    {/* Type */}
                    <Text style={styles.label}>분류</Text>
                    <SegmentedControl<AssetType>
                        value={type}
                        onChange={setType}
                        options={ASSET_TYPE_ORDER.map((t) => ({
                            value: t,
                            label: ASSET_TYPE_META[t].label,
                            emoji: ASSET_TYPE_META[t].emoji,
                        }))}
                    />

                    {/* Identifier */}
                    <Text style={styles.label}>식별자 (선택)</Text>
                    <TextInput
                        style={styles.input}
                        value={identifier}
                        onChangeText={setIdentifier}
                        placeholder="이메일·아이디·핸들 등"
                        placeholderTextColor={colors.text.caption}
                        autoCapitalize="none"
                        accessibilityLabel="자산 식별자"
                    />

                    {/* Action on death */}
                    <Text style={styles.label}>떠나신 후 처리 방식</Text>
                    <SegmentedControl<ActionOnDeath>
                        value={action}
                        onChange={setAction}
                        options={ACTION_ORDER.map((a) => ({
                            value: a,
                            label: ACTION_META[a].label,
                            emoji: ACTION_META[a].emoji,
                            color: ACTION_META[a].color,
                        }))}
                    />

                    {/* Secret */}
                    <View style={styles.secretHeader}>
                        <Text style={styles.label}>비밀번호 · 시드 (선택)</Text>
                        <View style={styles.encryptedTag}>
                            <Text style={styles.encryptedTagText}>🔒 암호화 저장</Text>
                        </View>
                    </View>

                    {hadSecret && !clearSecret ? (
                        <View style={styles.savedSecretBanner}>
                            <Text style={[typography.caption, { color: colors.text.secondary }]}>
                                저장된 비밀이 있어요. 비워두면 그대로 유지됩니다.
                            </Text>
                        </View>
                    ) : null}

                    {clearSecret ? (
                        <View style={styles.clearSecretBanner}>
                            <Text style={[typography.caption, { color: colors.danger, flex: 1 }]}>
                                저장 시 기존 비밀이 삭제됩니다.
                            </Text>
                            <TouchableOpacity
                                onPress={() => setClearSecret(false)}
                                accessibilityRole="button"
                                accessibilityLabel="삭제 취소"
                                hitSlop={8}
                            >
                                <Text style={[typography.caption, { color: colors.primary }]}>
                                    되돌리기
                                </Text>
                            </TouchableOpacity>
                        </View>
                    ) : null}

                    <TextInput
                        style={styles.input}
                        value={secret}
                        onChangeText={(v) => {
                            setSecret(v);
                            if (v.length > 0 && clearSecret) setClearSecret(false);
                        }}
                        placeholder={
                            hadSecret
                                ? '새 값을 입력하면 교체됩니다 (비워두면 유지)'
                                : '저장하면 본인만 열람할 수 있어요'
                        }
                        placeholderTextColor={colors.text.caption}
                        secureTextEntry={!showSecret}
                        autoCapitalize="none"
                        accessibilityLabel="민감 정보"
                    />
                    <View style={styles.secretActionRow}>
                        <TouchableOpacity
                            onPress={() => setShowSecret((s) => !s)}
                        >
                            <Text style={[typography.caption, { color: colors.primary }]}>
                                {showSecret ? '숨기기' : '보기'}
                            </Text>
                        </TouchableOpacity>
                        {hadSecret && !clearSecret ? (
                            <TouchableOpacity
                                onPress={() => {
                                    setSecret('');
                                    setClearSecret(true);
                                }}
                                accessibilityRole="button"
                                accessibilityLabel="저장된 비밀 삭제"
                            >
                                <Text style={[typography.caption, { color: colors.danger }]}>
                                    저장된 비밀 삭제
                                </Text>
                            </TouchableOpacity>
                        ) : null}
                    </View>

                    {/* Note */}
                    <Text style={styles.label}>메모 (선택)</Text>
                    <TextInput
                        style={[styles.input, styles.multiline]}
                        value={note}
                        onChangeText={setNote}
                        placeholder="가족에게 남기고 싶은 안내 등"
                        placeholderTextColor={colors.text.caption}
                        multiline
                        accessibilityLabel="자산 메모"
                    />

                    {errorMessage ? (
                        <Text style={[typography.caption, { color: colors.danger, marginTop: spacing.sm }]}>
                            {errorMessage}
                        </Text>
                    ) : null}

                    <TouchableOpacity
                        onPress={handleSubmit}
                        disabled={!canSubmit}
                        style={[
                            styles.primaryBtn,
                            { opacity: canSubmit ? 1 : 0.4 },
                        ]}
                        accessibilityRole="button"
                        accessibilityLabel={isEditing ? '저장하기' : '추가하기'}
                    >
                        <Text style={styles.primaryBtnText}>
                            {submitting ? '저장 중...' : isEditing ? '저장하기' : '추가하기'}
                        </Text>
                    </TouchableOpacity>

                    {isEditing && onDelete ? (
                        <TouchableOpacity
                            onPress={onDelete}
                            style={styles.dangerBtn}
                            accessibilityRole="button"
                            accessibilityLabel="이 자산 삭제"
                        >
                            <Text style={styles.dangerBtnText}>이 자산 삭제</Text>
                        </TouchableOpacity>
                    ) : null}
                </ScrollView>
            </KeyboardAvoidingView>
        </ScreenLayout>
    );
};

const styles = StyleSheet.create({
    container: {
        paddingVertical: spacing.lg,
        paddingBottom: spacing.xxl,
    },
    headerRow: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: spacing.lg,
    },
    iconBtn: {
        width: 44,
        height: 44,
        borderRadius: radius.full,
        alignItems: 'center',
        justifyContent: 'center',
    },
    iconBtnText: { fontSize: 22, color: colors.text.secondary },
    label: {
        ...typography.label,
        color: colors.text.secondary,
        marginTop: spacing.lg,
        marginBottom: spacing.sm,
        fontSize: 14,
    },
    input: {
        backgroundColor: colors.card,
        borderRadius: radius.md,
        borderWidth: 1,
        borderColor: colors.border,
        paddingHorizontal: spacing.md,
        paddingVertical: 14,
        minHeight: 48,
        color: colors.text.primary,
        fontSize: 16,
        fontFamily: 'Pretendard-Regular',
    },
    multiline: {
        minHeight: 96,
        paddingTop: spacing.md,
        textAlignVertical: 'top',
    },
    secretHeader: {
        flexDirection: 'row',
        alignItems: 'flex-end',
        justifyContent: 'space-between',
    },
    encryptedTag: {
        backgroundColor: `${colors.primary}14`,
        borderRadius: radius.full,
        paddingHorizontal: spacing.sm,
        paddingVertical: 2,
        marginBottom: spacing.sm,
    },
    encryptedTagText: {
        ...typography.label,
        color: colors.primary,
        fontSize: 12,
    },
    toggleSecretBtn: {
        alignSelf: 'flex-end',
        paddingVertical: spacing.xs,
        marginTop: spacing.xs,
    },
    savedSecretBanner: {
        backgroundColor: `${colors.primary}0E`,
        borderRadius: radius.sm,
        paddingHorizontal: spacing.md,
        paddingVertical: spacing.sm,
        marginBottom: spacing.sm,
    },
    clearSecretBanner: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: `${colors.danger}10`,
        borderRadius: radius.sm,
        paddingHorizontal: spacing.md,
        paddingVertical: spacing.sm,
        marginBottom: spacing.sm,
        gap: spacing.sm,
    },
    secretActionRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginTop: spacing.xs,
        paddingHorizontal: spacing.xs,
    },
    primaryBtn: {
        marginTop: spacing.xl,
        backgroundColor: colors.primary,
        borderRadius: radius.md,
        paddingVertical: 16,
        alignItems: 'center',
    },
    primaryBtnText: {
        color: colors.text.inverse,
        fontFamily: 'Pretendard-Bold',
        fontSize: 16,
    },
    dangerBtn: {
        marginTop: spacing.md,
        paddingVertical: 14,
        alignItems: 'center',
    },
    dangerBtnText: {
        color: colors.danger,
        fontFamily: 'Pretendard-Medium',
        fontSize: 14,
    },
});
