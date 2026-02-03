import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import { ScreenLayout } from '../components/ScreenLayout';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';
import { useAuth } from '../context/AuthContext';
import { haptic } from '../utils/haptics';

interface SignupScreenProps {
    onNavigateToLogin: () => void;
}

export const SignupScreen = ({ onNavigateToLogin }: SignupScreenProps) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { register } = useAuth();

    const handleSignup = async () => {
        if (!email || !password || !confirmPassword) {
            Alert.alert('오류', '모든 필드를 입력해주세요.');
            return;
        }

        if (password !== confirmPassword) {
            await haptic.warning();
            Alert.alert('오류', '비밀번호가 일치하지 않습니다.');
            return;
        }

        if (password.length < 8) {
            await haptic.warning();
            Alert.alert('오류', '비밀번호는 8자 이상이어야 합니다.');
            return;
        }

        await haptic.selection();
        setIsLoading(true);

        try {
            await register(email, password);
            await haptic.success();
        } catch (_error) {
            await haptic.error();
            Alert.alert('회원가입 실패', '이미 등록된 이메일이거나 서버 오류가 발생했습니다.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <ScreenLayout>
            <View style={styles.container}>
                <View style={styles.header}>
                    <Text style={[typography.heading1, { color: colors.primary }]}>회원가입</Text>
                    <Text style={[typography.body1, { color: colors.text.secondary, marginTop: 8 }]}>
                        InRem과 함께 시작하세요
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
                        placeholder="8자 이상 입력하세요"
                        placeholderTextColor={colors.text.caption}
                        value={password}
                        onChangeText={setPassword}
                        secureTextEntry
                        autoComplete="new-password"
                    />

                    <Text style={[typography.caption, styles.label]}>비밀번호 확인</Text>
                    <TextInput
                        style={styles.input}
                        placeholder="비밀번호를 다시 입력하세요"
                        placeholderTextColor={colors.text.caption}
                        value={confirmPassword}
                        onChangeText={setConfirmPassword}
                        secureTextEntry
                        autoComplete="new-password"
                    />

                    <TouchableOpacity
                        style={[styles.button, isLoading && styles.buttonDisabled]}
                        onPress={handleSignup}
                        disabled={isLoading}
                        activeOpacity={0.8}
                    >
                        {isLoading ? (
                            <ActivityIndicator color={colors.white} />
                        ) : (
                            <Text style={[typography.body1, { color: colors.white }]}>가입하기</Text>
                        )}
                    </TouchableOpacity>
                </View>

                <View style={styles.footer}>
                    <Text style={[typography.caption, { color: colors.text.secondary }]}>
                        이미 계정이 있으신가요?
                    </Text>
                    <TouchableOpacity onPress={onNavigateToLogin}>
                        <Text style={[typography.body2, { color: colors.primary, marginLeft: 8 }]}>
                            로그인
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
