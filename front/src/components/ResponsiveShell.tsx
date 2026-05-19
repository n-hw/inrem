/**
 * ResponsiveShell — 어떤 viewport 에서도 동일한 모바일 UX 를 보장하는
 * 최상위 컨테이너.
 *
 * 동작:
 * - 모바일 폭 (≤ MAX_CONTENT_WIDTH): 풀스크린 그대로. 추가 효과 없음.
 * - 태블릿·웹·데스크톱: 480 폭으로 컨텐츠를 중앙 고정. 외곽엔 `colors.shell`
 *   배경을 깔아 모바일 프레임이 카드처럼 떠 있는 형태로 보이게.
 *
 * native(iOS/Android) 와 web 모두 동일하게 작동 — iPad 가로 / 펼친
 * foldable 등에서도 깨지지 않는다.
 */
import React, { ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';

import { MAX_CONTENT_WIDTH, useResponsive } from '../hooks/useResponsive';
import { colors } from '../theme/colors';

interface Props {
    children: ReactNode;
}

export const ResponsiveShell = ({ children }: Props) => {
    const { isShellWider } = useResponsive();

    return (
        <View
            style={[
                styles.outer,
                { backgroundColor: isShellWider ? colors.shell : colors.background },
            ]}
        >
            <View
                style={[
                    styles.inner,
                    isShellWider && styles.innerFramed,
                ]}
            >
                {children}
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    outer: {
        flex: 1,
        width: '100%',
        alignItems: 'center',
        justifyContent: 'center',
    },
    inner: {
        flex: 1,
        width: '100%',
        maxWidth: MAX_CONTENT_WIDTH,
        backgroundColor: colors.background,
    },
    // shell-wider 상태일 때만 적용되는 모바일-프레임 스타일.
    // 그림자로 컨테이너를 "뜬" 느낌으로.
    innerFramed: {
        shadowColor: colors.black,
        shadowOffset: { width: 0, height: 0 },
        shadowOpacity: 0.08,
        shadowRadius: 24,
        elevation: 6,
    },
});
