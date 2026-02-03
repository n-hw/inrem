import { useState, useEffect, useRef } from 'react';
import { Platform, Alert } from 'react-native';
import * as Device from 'expo-device';
import * as Notifications from 'expo-notifications';
import { deviceApi, pulseApi } from '../api/client';
import { useAuth } from '../context/AuthContext';

// Configure notification handler
Notifications.setNotificationHandler({
    handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: false,
        shouldShowBanner: true,
        shouldShowList: true,
    }),
});

export const usePushNotification = () => {
    const { user } = useAuth();
    const [expoPushToken, setExpoPushToken] = useState<string | undefined>();
    const [notification, setNotification] = useState<Notifications.Notification | undefined>();
    const notificationListener = useRef<Notifications.Subscription>(undefined);
    const responseListener = useRef<Notifications.Subscription>(undefined);

    const registerForPushNotificationsAsync = async () => {
        let token;

        if (Platform.OS === 'android') {
            await Notifications.setNotificationChannelAsync('default', {
                name: 'default',
                importance: Notifications.AndroidImportance.MAX,
                vibrationPattern: [0, 250, 250, 250],
                lightColor: '#FF231F7C',
            });
        }

        if (Device.isDevice) {
            const { status: existingStatus } = await Notifications.getPermissionsAsync();
            let finalStatus = existingStatus;
            if (existingStatus !== 'granted') {
                const { status } = await Notifications.requestPermissionsAsync();
                finalStatus = status;
            }
            if (finalStatus !== 'granted') {
                alert('Failed to get push token for push notification!');
                return;
            }

            try {
                // Get device token for FCM
                token = (await Notifications.getDevicePushTokenAsync()).data;
            } catch (e) {
                console.error("Error getting token", e);
            }
        } else {
            alert('Must use physical device for Push Notifications');
        }

        return token;
    };

    useEffect(() => {
        if (user?.email) {
            registerForPushNotificationsAsync().then(async (token) => {
                setExpoPushToken(token);
                if (token) {
                    try {
                        // Register token with backend
                        await deviceApi.register(token);
                        console.log('Registered device token:', token);
                    } catch (error) {
                        console.error('Failed to register device token:', error);
                    }
                }
            });
        }

        notificationListener.current = Notifications.addNotificationReceivedListener(notification => {
            setNotification(notification);

            // Handle Soft Check-in in foreground
            const data = notification.request.content.data;
            if (data?.type === 'SOFT_CHECKIN') {
                Alert.alert(
                    notification.request.content.title || '안부 확인',
                    notification.request.content.body || '괜찮으신가요?',
                    [
                        {
                            text: '응답하기 (I\'m Okay)',
                            onPress: async () => {
                                try {
                                    const eventId = typeof data.event_id === 'string' ? data.event_id : undefined;
                                    await pulseApi.respondToPulse(eventId);
                                    Alert.alert('확인되었습니다', '안부를 확인해주셔서 감사합니다.');
                                } catch (_e) {
                                    Alert.alert('오류', '응답을 전송하지 못했습니다.');
                                }
                            }
                        },
                        {
                            text: '나중에',
                            style: 'cancel',
                        }
                    ]
                );
            }
        });

        responseListener.current = Notifications.addNotificationResponseReceivedListener(async response => {
            const data = response.notification.request.content.data;
            if (data?.type === 'SOFT_CHECKIN') {
                try {
                    const eventId = typeof data.event_id === 'string' ? data.event_id : undefined;
                    await pulseApi.respondToPulse(eventId);
                    Alert.alert('확인되었습니다', '안부를 확인해주셔서 감사합니다.');
                } catch (_e) {
                    Alert.alert('오류', '응답을 전송하지 못했습니다.');
                }
            }
        });

        return () => {
            if (notificationListener.current) {
                notificationListener.current.remove();
            }
            if (responseListener.current) {
                responseListener.current.remove();
            }
        };
    }, [user]);

    return {
        expoPushToken,
        notification,
    };
};
