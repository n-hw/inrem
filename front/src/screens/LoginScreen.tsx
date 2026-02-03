import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import { ScreenLayout } from '../components/ScreenLayout';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { useAuth } from '../context/AuthContext';
import { haptic } from '../utils/haptics';

interface LoginScreenProps {
    onNavigateToSignup: () => void;
}

export const LoginScreen = ({ onNavigateToSignup }: LoginScreenProps) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { login } = useAuth();

    const handleLogin = async () => {
        if (!email || !password) {
            Alert.alert('오류', '이메일과 비밀번호를 입력해주세요.');
            return;
        }

        await haptic.selection();
        setIsLoading(true);

        try {
            await login(email, password);
            await haptic.success();
        } catch (_error) {
            await haptic.error();
            Alert.alert('로그인 실패', '이메일 또는 비밀번호가 올바르지 않습니다.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <ScreenLayout>
            <View style={styles.container}>
                <View style={styles.header}>
                    <Text style={[typography.heading1, { color: colors.primary }]}>InRem</Text>
                    <Text style={[typography.body1, { color: colors.text.secondary, marginTop: 8 }]}>
                        소중한 기록을 안전하게
                    </Text>
                </View>

                <View style={styles.form}>
                    <Text style={[typography.caption, styles.label]}>이메일</Text>
                    <TextInput
                        style={styles.input}
                        placeholder="example@email.com"
                        placeholderTextColor={colors.text.caption}
                        value={email}
                        onChangeText={setEmail}
                        keyboardType="email-address"
                        autoCapitalize="none"
                        autoComplete="email"
                    />

                    <Text style={[typography.caption, styles.label]}>비밀번호</Text>
                    <TextInput
                        style={styles.input}
                        placeholder="비밀번호를 입력하세요"
                        placeholderTextColor={colors.text.caption}
                        value={password}
                        onChangeText={setPassword}
                        secureTextEntry
                        autoComplete="password"
                    />

                    <TouchableOpacity
                        style={[styles.button, isLoading && styles.buttonDisabled]}
                        onPress={handleLogin}
                        disabled={isLoading}
                        activeOpacity={0.8}
                    >
                        {isLoading ? (
                            <ActivityIndicator color={colors.white} />
                        ) : (
                            <Text style={[typography.body1, { color: colors.white }]}>로그인</Text>
                        )}
                    </TouchableOpacity>
                </View>

                <View style={styles.footer}>
                    <Text style={[typography.caption, { color: colors.text.secondary }]}>
                        아직 계정이 없으신가요?
                    </Text>
                    <TouchableOpacity onPress={onNavigateToSignup}>
                        <Text style={[typography.body2, { color: colors.primary, marginLeft: 8 }]}>
                            회원가입
                        </Text>
                    </TouchableOpacity>
                </View>
            </View>
        </ScreenLayout>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
    },
    header: {
        alignItems: 'center',
        marginBottom: 48,
    },
    form: {
        marginBottom: 32,
    },
    label: {
        marginBottom: 8,
        color: colors.text.secondary,
    },
    input: {
        height: 56,
        borderWidth: 1.5,
        borderColor: colors.border,
        borderRadius: 16,
        paddingHorizontal: 20,
        marginBottom: 24,
        fontSize: 18,
        fontFamily: 'Pretendard-Regular',
        backgroundColor: colors.white,
        color: colors.text.primary,
    },
    button: {
        height: 56,
        backgroundColor: colors.primary,
        borderRadius: 16,
        justifyContent: 'center',
        alignItems: 'center',
        marginTop: 16,
        shadowColor: colors.primary,
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.2,
        shadowRadius: 8,
        elevation: 4,
    },
    buttonDisabled: {
        opacity: 0.6,
        shadowOpacity: 0,
        elevation: 0,
    },
    footer: {
        flexDirection: 'row',
        justifyContent: 'center',
        alignItems: 'center',
        paddingVertical: 16,
    },
});
