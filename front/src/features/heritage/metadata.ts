/**
 * Display metadata for Heritage Box asset types and post-mortem actions.
 * Pulled out so screens stay declarative.
 *
 * See: document/design_system.md §7
 */
import { colors } from '../../theme/colors';
import type { ActionOnDeath, AssetType } from '../../api/client';

export const ASSET_TYPE_META: Record<AssetType, { label: string; emoji: string }> = {
    social_account: { label: '소셜 계정', emoji: '💬' },
    subscription: { label: '구독 서비스', emoji: '📺' },
    cloud_storage: { label: '클라우드', emoji: '☁️' },
    crypto: { label: '가상자산', emoji: '🪙' },
    bank_account: { label: '금융 계정', emoji: '🏦' },
    document: { label: '중요 문서', emoji: '📄' },
    custom: { label: '기타', emoji: '✨' },
};

export const ASSET_TYPE_ORDER: AssetType[] = [
    'social_account',
    'subscription',
    'cloud_storage',
    'crypto',
    'bank_account',
    'document',
    'custom',
];

export const ACTION_META: Record<
    ActionOnDeath,
    { label: string; emoji: string; color: string }
> = {
    delete: { label: '삭제', emoji: '🗑️', color: colors.danger },
    memorialize: { label: '추모 보존', emoji: '🕯️', color: colors.secondary },
    transfer: { label: '승계', emoji: '🤝', color: colors.primary },
    keep_private: { label: '비공개', emoji: '🔒', color: colors.accent },
};

export const ACTION_ORDER: ActionOnDeath[] = [
    'keep_private',
    'memorialize',
    'transfer',
    'delete',
];

/**
 * Empty-state recommendations — kicks new users into adding their first item.
 * See: document/user_journey_map.md §4
 */
export const EMPTY_STATE_SUGGESTIONS: Array<{
    name: string;
    type: AssetType;
    action_on_death: ActionOnDeath;
}> = [
    { name: 'Instagram', type: 'social_account', action_on_death: 'memorialize' },
    { name: 'Netflix', type: 'subscription', action_on_death: 'delete' },
    { name: 'Google Drive', type: 'cloud_storage', action_on_death: 'transfer' },
    { name: '주거래 은행 계좌', type: 'bank_account', action_on_death: 'transfer' },
    { name: '중요 문서 (보험증서 등)', type: 'document', action_on_death: 'transfer' },
];

/**
 * 분류별 권장 처리 방식 — 새 자산을 만들 때 합리적인 기본값.
 * 사용자가 분류를 바꾸면 처리 방식을 부드럽게 동기화한다 (편집 모드 제외).
 */
export const DEFAULT_ACTION_FOR_TYPE: Record<AssetType, ActionOnDeath> = {
    social_account: 'memorialize',
    subscription: 'delete',
    cloud_storage: 'transfer',
    crypto: 'transfer',
    bank_account: 'transfer',
    document: 'transfer',
    custom: 'keep_private',
};
