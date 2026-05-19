import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const ACCESS_KEY = 'access_token';
const REFRESH_KEY = 'refresh_token';

/**
 * Platform-aware secure-ish key/value storage.
 *
 * - **iOS / Android**: `expo-secure-store` (Keychain / Keystore).
 * - **Web**: `localStorage`. Note this is NOT actually secure — it is
 *   readable by any same-origin script — but the alternative is a runtime
 *   crash (`deleteValueWithKeyAsync is not a function`). Web is dev / preview
 *   only; production targets are native, where SecureStore applies.
 */
const isWeb = Platform.OS === 'web';

async function getItem(key: string): Promise<string | null> {
    if (isWeb) {
        return typeof window !== 'undefined' ? window.localStorage.getItem(key) : null;
    }
    return SecureStore.getItemAsync(key);
}

async function setItem(key: string, value: string): Promise<void> {
    if (isWeb) {
        if (typeof window !== 'undefined') window.localStorage.setItem(key, value);
        return;
    }
    await SecureStore.setItemAsync(key, value);
}

async function deleteItem(key: string): Promise<void> {
    if (isWeb) {
        if (typeof window !== 'undefined') window.localStorage.removeItem(key);
        return;
    }
    await SecureStore.deleteItemAsync(key);
}

export const tokenStorage = {
    getAccess: () => getItem(ACCESS_KEY),
    getRefresh: () => getItem(REFRESH_KEY),
    setBoth: async (access: string, refresh: string) => {
        await setItem(ACCESS_KEY, access);
        await setItem(REFRESH_KEY, refresh);
    },
    clear: async () => {
        await deleteItem(ACCESS_KEY);
        await deleteItem(REFRESH_KEY);
    },
};

export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

apiClient.interceptors.request.use(
    async (config) => {
        const token = await tokenStorage.getAccess();
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error),
);

// --- 401 → automatic refresh + retry ---
// Single in-flight refresh promise so concurrent 401s don't fan out into
// N refresh calls. Anyone who hits a 401 while one is pending awaits it.
let refreshInFlight: Promise<string | null> | null = null;

async function performRefresh(): Promise<string | null> {
    const refresh = await tokenStorage.getRefresh();
    if (!refresh) return null;
    try {
        const resp = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refresh,
        });
        const { access_token, refresh_token } = resp.data;
        await tokenStorage.setBoth(access_token, refresh_token);
        return access_token;
    } catch {
        await tokenStorage.clear();
        return null;
    }
}

/**
 * Map any API error into a user-facing Korean message.
 *
 * Use this everywhere we'd otherwise print a generic "오류" — the UX
 * difference between "비밀번호가 틀렸어요" vs "잠시 후 다시 시도해
 * 주세요" matters more than the actual status code.
 *
 * Falls back to `fallback` (caller's screen-specific copy) for unknown
 * shapes — never surfaces the raw axios message or English text.
 */
export function describeError(error: unknown, fallback = '문제가 발생했어요.'): string {
    if (!axios.isAxiosError(error)) return fallback;
    if (error.code === 'ECONNABORTED') return '요청 시간이 초과됐어요. 네트워크 상태를 확인해 주세요.';
    if (!error.response) return '인터넷에 연결되지 않은 것 같아요. 잠시 후 다시 시도해 주세요.';

    const status = error.response.status;
    const detail = (error.response.data as { detail?: string } | undefined)?.detail;

    switch (status) {
        case 400:
            return detail || '요청 내용을 확인해 주세요.';
        case 401:
            return '로그인이 필요해요. 다시 로그인해 주세요.';
        case 403:
            return '접근 권한이 없어요.';
        case 404:
            return '대상을 찾을 수 없어요.';
        case 410:
            return detail || '유효 기간이 만료됐어요.';
        case 422:
            return detail || '입력 형식을 확인해 주세요.';
        case 429: {
            const retry = error.response.headers?.['retry-after'];
            return retry
                ? `요청이 너무 잦아요. ${retry}초 후 다시 시도해 주세요.`
                : '요청이 너무 잦아요. 잠시 후 다시 시도해 주세요.';
        }
        case 500:
        case 502:
        case 503:
        case 504:
            return '서버가 응답하지 않아요. 잠시 후 다시 시도해 주세요.';
        default:
            return fallback;
    }
}

apiClient.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        const original = error.config as
            | (InternalAxiosRequestConfig & { _retried?: boolean })
            | undefined;
        const status = error.response?.status;

        // Don't try to refresh the refresh call itself (would loop).
        const isRefreshCall = original?.url?.endsWith('/auth/refresh');

        if (status === 401 && original && !original._retried && !isRefreshCall) {
            original._retried = true;
            refreshInFlight ??= performRefresh().finally(() => {
                refreshInFlight = null;
            });
            const newAccess = await refreshInFlight;
            if (newAccess) {
                original.headers.Authorization = `Bearer ${newAccess}`;
                return apiClient.request(original);
            }
            // Refresh failed — propagate so AuthContext can sign the user out.
        }
        return Promise.reject(error);
    },
);

export const authApi = {
    register: async (email: string, password: string) => {
        const response = await apiClient.post('/auth/register', { email, password });
        return response.data;
    },

    login: async (email: string, password: string) => {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const response = await apiClient.post('/auth/login', formData.toString(), {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        });
        return response.data;
    },

    getMe: async () => {
        const response = await apiClient.get('/auth/me');
        return response.data;
    },
};

export interface DeletionStatus {
    deletion_requested_at: string | null;
    grace_period_days: number;
    seconds_remaining: number | null;
}

export const accountApi = {
    /** PIPA 잊혀질 권리: 계정 삭제 요청 (30일 grace, idempotent). */
    requestDeletion: async (): Promise<DeletionStatus> => {
        const response = await apiClient.delete('/auth/me');
        return response.data;
    },
    /** Grace 기간 중 삭제 요청 취소. 410 시 grace 만료. */
    restore: async (): Promise<DeletionStatus> => {
        const response = await apiClient.post('/auth/me/restore');
        return response.data;
    },
};

export type SignalType = 'app_open' | 'app_foreground' | 'touch_event' | 'heartbeat' | 'manual_checkin';

export interface HeartbeatResponse {
    success: boolean;
    last_active_at: string;
    signal_id: string;
}

export interface StatusResponse {
    last_active_at: string | null;
    deletion_requested_at: string | null;
}

export const signalApi = {
    /**
     * Send a heartbeat signal to the server.
     * This updates the user's last_active_at and records the activity.
     */
    sendHeartbeat: async (signalType: SignalType = 'heartbeat', deviceInfo?: string): Promise<HeartbeatResponse> => {
        const response = await apiClient.post('/signal/heartbeat', {
            signal_type: signalType,
            device_info: deviceInfo,
        });
        return response.data;
    },
    /**
     * Read-only status snapshot — no side effects.
     * Used by HomeScreen polling so the timer reflects activity from
     * other devices without minting another heartbeat.
     */
    getStatus: async (): Promise<StatusResponse> => {
        const response = await apiClient.get('/signal/status');
        return response.data;
    },
};

export const pulseApi = {
    /**
     * Respond to a Soft Check-in.
     * Confirms user is okay and resets the timer.
     */
    respondToPulse: async (eventId?: string): Promise<{ success: boolean; message: string; status: string }> => {
        const response = await apiClient.post('/pulse/respond', {
            event_id: eventId,
        });
        return response.data;
    },
};

export const deviceApi = {
    register: async (fcmToken: string): Promise<{ success: boolean; message: string }> => {
        const response = await apiClient.post('/device/register', {
            fcm_token: fcmToken,
        });
        return response.data;
    },
    unregister: async (): Promise<{ success: boolean; message: string }> => {
        const response = await apiClient.delete('/device/unregister');
        return response.data;
    },
};

export type SensitivityLevel = 'relaxed' | 'normal' | 'strict';

export interface MonitoringPolicy {
    threshold_hours: number;
    quiet_start: string;
    quiet_end: string;
    escalation_enabled: boolean;
    escalation_delay_minutes: number;
    sensitivity: SensitivityLevel;
    is_active: boolean;
    sms_fallback_enabled: boolean;
}

export interface MonitoringPolicyUpdate {
    threshold_hours?: number;
    quiet_start?: string;
    quiet_end?: string;
    escalation_enabled?: boolean;
    escalation_delay_minutes?: number;
    sensitivity?: SensitivityLevel;
    is_active?: boolean;
    sms_fallback_enabled?: boolean;
}

export const settingsApi = {
    getPolicy: async (): Promise<MonitoringPolicy> => {
        const response = await apiClient.get('/settings/policy');
        return response.data;
    },
    updatePolicy: async (data: MonitoringPolicyUpdate): Promise<MonitoringPolicy> => {
        const response = await apiClient.patch('/settings/policy', data);
        return response.data;
    },
};

// ──────────────────────────────────────────────────────────────────────────
// Upsell / Paywall click logging (Premium conversion KPI validation).
// See: document/PRD.md §2.1 goal 4.
// ──────────────────────────────────────────────────────────────────────────

export type UpsellFeature = 'family_share' | 'report_export' | 'extended_storage';

export const upsellApi = {
    /**
     * Log a paywall card tap. Backend just records to structured logs;
     * no DB write yet (analytics pipeline aggregates later).
     */
    logClick: async (feature: UpsellFeature, surface?: string): Promise<void> => {
        await apiClient.post('/settings/upsell/click', { feature, surface });
    },
};

// ──────────────────────────────────────────────────────────────────────────
// Heritage Box (Stage 2 — Digital legacy inventory)
// See: document/PRD.md §5.1
// ──────────────────────────────────────────────────────────────────────────

export type AssetType =
    | 'social_account'
    | 'subscription'
    | 'cloud_storage'
    | 'crypto'
    | 'bank_account'
    | 'document'
    | 'custom';

export type ActionOnDeath = 'delete' | 'memorialize' | 'transfer' | 'keep_private';

export interface Asset {
    id: string;
    user_id: string;
    name: string;
    type: AssetType;
    identifier: string | null;
    action_on_death: ActionOnDeath;
    designated_executor_id: string | null;
    note: string | null;
    has_secret: boolean;
    created_at: string;
    updated_at: string;
}

export interface AssetCreatePayload {
    name: string;
    type: AssetType;
    identifier?: string | null;
    action_on_death: ActionOnDeath;
    designated_executor_id?: string | null;
    note?: string | null;
    secret?: string | null;
}

export interface AssetUpdatePayload {
    name?: string;
    type?: AssetType;
    identifier?: string | null;
    action_on_death?: ActionOnDeath;
    designated_executor_id?: string | null;
    note?: string | null;
    secret?: string | null;
    clear_secret?: boolean;
}

export interface AssetSummary {
    total: number;
    by_type: Record<string, number>;
    by_action: Record<string, number>;
}

export const heritageApi = {
    listAssets: async (params?: {
        type?: AssetType;
        search?: string;
        limit?: number;
        offset?: number;
    }): Promise<Asset[]> => {
        const response = await apiClient.get('/heritage/assets', { params });
        return response.data;
    },
    getSummary: async (): Promise<AssetSummary> => {
        const response = await apiClient.get('/heritage/assets/summary');
        return response.data;
    },
    getAsset: async (id: string): Promise<Asset> => {
        const response = await apiClient.get(`/heritage/assets/${id}`);
        return response.data;
    },
    createAsset: async (data: AssetCreatePayload): Promise<Asset> => {
        const response = await apiClient.post('/heritage/assets', data);
        return response.data;
    },
    updateAsset: async (id: string, data: AssetUpdatePayload): Promise<Asset> => {
        const response = await apiClient.patch(`/heritage/assets/${id}`, data);
        return response.data;
    },
    deleteAsset: async (id: string): Promise<void> => {
        await apiClient.delete(`/heritage/assets/${id}`);
    },
    revealSecret: async (id: string): Promise<{ id: string; secret: string | null }> => {
        const response = await apiClient.get(`/heritage/assets/${id}/secret`);
        return response.data;
    },
};
