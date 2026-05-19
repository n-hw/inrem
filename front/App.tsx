import React, { useCallback, useState } from 'react';
import { Text, View, StyleSheet, ActivityIndicator } from 'react-native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { useFonts } from 'expo-font';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { ScreenLayout } from './src/components/ScreenLayout';
import { colors } from './src/theme/colors';
import { typography } from './src/theme/typography';
import { AuthProvider, useAuth } from './src/context/AuthContext';
import { LoginScreen } from './src/screens/LoginScreen';
import { SignupScreen } from './src/screens/SignupScreen';
import { useAppStateHeartbeat } from './src/hooks/useAppStateHeartbeat';
import { usePushNotification } from './src/hooks/usePushNotification';

SplashScreen.preventAutoHideAsync();

type AuthScreen = 'login' | 'signup';

import { MainTabsScreen } from './src/screens/MainTabsScreen';

const AuthenticatedApp = () => {
  useAuth(); // keep for future user-aware effects

  // Send heartbeat when app is active
  useAppStateHeartbeat();

  // Handle push notifications (for Soft Check-in)
  usePushNotification();

  // Bottom tabs: 홈(Pulse) · 유산함(Heritage) · 설정(Settings)
  return <MainTabsScreen />;
};

const UnauthenticatedApp = () => {
  const [currentScreen, setCurrentScreen] = useState<AuthScreen>('login');

  if (currentScreen === 'login') {
    return <LoginScreen onNavigateToSignup={() => setCurrentScreen('signup')} />;
  }

  return <SignupScreen onNavigateToLogin={() => setCurrentScreen('login')} />;
};

const AppContent = () => {
  const { isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return (
      <ScreenLayout>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={[typography.body1, { color: colors.text.secondary, marginTop: 16 }]}>
            로딩 중...
          </Text>
        </View>
      </ScreenLayout>
    );
  }

  if (isAuthenticated) {
    return <AuthenticatedApp />;
  }

  return <UnauthenticatedApp />;
};

export default function App() {
  const [fontsLoaded] = useFonts({
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    'Pretendard-Regular': require('./assets/fonts/Pretendard-Regular.otf'),
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    'Pretendard-Medium': require('./assets/fonts/Pretendard-Medium.otf'),
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    'Pretendard-Bold': require('./assets/fonts/Pretendard-Bold.otf'),
  });

  const onLayoutRootView = useCallback(async () => {
    if (fontsLoaded) {
      await SplashScreen.hideAsync();
    }
  }, [fontsLoaded]);

  if (!fontsLoaded) {
    return null;
  }

  return (
    <View style={{ flex: 1 }} onLayout={onLayoutRootView}>
      <GestureHandlerRootView style={{ flex: 1 }}>
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </GestureHandlerRootView>
      <StatusBar style="auto" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoutButton: {
    marginTop: 40,
    padding: 16,
  },
});
