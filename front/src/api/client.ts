import axios from 'axios';
import * as SecureStore from 'expo-secure-store';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
    async (config) => {
        const token = await SecureStore.getItemAsync('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
    (response) => response,
    async (error) => {
        if (error.response?.status === 401) {
            // Token expired or invalid - clear storage
            await SecureStore.deleteItemAsync('access_token');
        }
        return Promise.reject(error);
    }
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
