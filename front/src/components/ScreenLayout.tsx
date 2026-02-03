import React, { ReactNode } from 'react';
import { StyleSheet, View, ViewStyle, StatusBar } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors } from '../theme/colors';

interface ScreenLayoutProps {
    children: ReactNode;
    style?: ViewStyle;
    withSafeArea?: boolean;
}

export const ScreenLayout = ({ children, style, withSafeArea = true }: ScreenLayoutProps) => {
    const Container = withSafeArea ? SafeAreaView : View;

    return (
        <Container style={[styles.container, style]}>
            <StatusBar barStyle="dark-content" backgroundColor={colors.background} />
            <View style={styles.content}>
                {children}
            </View>
        </Container>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: colors.background,
    },
    content: {
        flex: 1,
        paddingHorizontal: 20, // Standard horizontal padding
    },
});
