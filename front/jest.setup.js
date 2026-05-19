import 'react-native-gesture-handler/jestSetup';

jest.mock('react-native-reanimated', () => {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const Reanimated = require('react-native-reanimated/mock');
    Reanimated.default.call = () => { };
    return Reanimated;
});

jest.mock('expo-secure-store', () => ({
    getItemAsync: jest.fn(),
    setItemAsync: jest.fn(),
    deleteItemAsync: jest.fn(),
}));

jest.mock('expo-haptics', () => ({
    notificationAsync: jest.fn(),
    NotificationFeedbackType: {
        Success: 'success',
        Error: 'error',
    },
}));

// 참고: @react-navigation/native 는 사용하지 않음 (BottomTabBar 자체 구현).
