/**
 * 반응형 유틸 — 화면 폭을 breakpoint 로 환산해 컴포넌트가 쉽게 사용할 수
 * 있게 한다.
 *
 * **설계 원칙**: InRem 은 모바일-퍼스트 앱이고 "어떤 환경에서도 동일한
 * UI/UX" 가 목표다. 그래서 큰 화면(태블릿·웹·데스크톱) 에서 새로운
 * 레이아웃을 그리는 대신, 같은 모바일 디자인을 중앙에 고정 폭으로
 * 띄워서 사용자가 일관된 경험을 받도록 한다.
 *
 * `MAX_CONTENT_WIDTH` 가 그 모바일 프레임의 최대 폭. 가장 큰 핸드폰
 * (iPhone 14 Pro Max 430pt) 보다 약간 여유 두고 480 으로 잡았다.
 */
import { useWindowDimensions } from 'react-native';

/** 어떤 viewport 에서도 모바일 UI 가 들어가는 최대 폭 (dp/px). */
export const MAX_CONTENT_WIDTH = 480;

export interface Responsive {
    width: number;
    height: number;
    /** viewport 가 모바일 프레임보다 커서 outer shell 배경이 보이는 상태. */
    isShellWider: boolean;
}

export function useResponsive(): Responsive {
    const { width, height } = useWindowDimensions();
    return {
        width,
        height,
        isShellWider: width > MAX_CONTENT_WIDTH,
    };
}
