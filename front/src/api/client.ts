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

export type SignalType = 'app_open' | 'app_foreground' | 'touch_event' | 'heartbeat' | 'manual_checkin';

export interface HeartbeatResponse {
    success: boolean;
    last_active_at: string;
    signal_id: string;
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
