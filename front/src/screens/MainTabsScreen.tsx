import React, { useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { BottomTabBar, type TabItem } from '../components/BottomTabBar';
import { HomeScreen } from './HomeScreen';
import { HeritageBoxScreen } from './HeritageBoxScreen';
import { SettingsScreen } from './SettingsScreen';
import { colors } from '../theme/colors';

export type MainTabKey = 'home' | 'heritage' | 'settings';

const TABS: TabItem[] = [
    { key: 'home', label: '홈', emoji: '🏠' },
    { key: 'heritage', label: '유산함', emoji: '🗂️' },
    { key: 'settings', label: '설정', emoji: '⚙️' },
];

export const MainTabsScreen = () => {
    const [active, setActive] = useState<MainTabKey>('home');

    return (
        <View style={styles.container}>
            <View style={styles.body}>
                {active === 'home' ? <HomeScreen onNavigate={setActive} /> : null}
                {active === 'heritage' ? <HeritageBoxScreen /> : null}
                {active === 'settings' ? <SettingsScreen /> : null}
            </View>
            <BottomTabBar
                items={TABS}
                activeKey={active}
                onChange={(key) => setActive(key as MainTabKey)}
            />
        </View>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.background },
    body: { flex: 1 },
});
