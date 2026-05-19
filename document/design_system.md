# InRem 디자인 시스템 (Design System v1.0)

> 문서 버전: v1.0 · 최종 업데이트: 2026-05-19  
> 컨셉: **"Warm Serenity (따뜻한 평온)"**  
> 관련 문서: `ui_guide.md` (원본), `PRD.md`, `personas.md`

---

## 1. 디자인 원칙 (Design Principles)

1. **Calm by Default**: 죽음·돌봄을 다루는 서비스. 강한 색·과한 모션 금지. 차분한 색조와 여백.
2. **Senior-Friendly First**: 시니어가 쓸 수 있으면 모두가 쓸 수 있다. 큰 글자·큰 터치·낮은 인지 부하.
3. **Trustable Surface**: 보안·신뢰가 핵심. 민감 정보 입력 화면은 시각적으로 "잠금/보호" 신호.
4. **One Screen, One Action**: 한 화면은 한 가지 일을 한다. 의사결정 분기 최소화.
5. **No Dark Patterns**: 결제·권한·삭제 등 중요한 선택은 항상 명확한 confirmation.

---

## 2. 컬러 시스템 (Color System)

> 코드 위치: `front/src/theme/colors.ts`

### 2.1 Primary Palette
| Role | Token | HEX | 용도 |
| --- | --- | --- | --- |
| Primary | `colors.primary` | `#003366` | Deep Ocean Blue — 메인 CTA, 헤더, 강조 텍스트 |
| Secondary | `colors.secondary` | `#B2AC88` | Soft Sage — 안정·생명 포인트, 보조 버튼 |
| Accent | `colors.accent` | `#D4C4B5` | Warm Sand — 따뜻함, 인터랙티브 배경 |

### 2.2 Surface & Text
| Token | HEX | 용도 |
| --- | --- | --- |
| `colors.background` | `#F8F9FA` | 앱 전체 배경 |
| `colors.card` | `#FFFFFF` | 카드/시트 |
| `colors.border` | `#E0E0E0` | 1px 라인 |
| `colors.text.primary` | `#111111` | 본문 |
| `colors.text.secondary` | `#424242` | 보조 |
| `colors.text.caption` | `#757575` | 캡션 |
| `colors.text.inverse` | `#FFFFFF` | 어두운 배경 위 텍스트 |

### 2.3 Semantic
| Token | HEX | 용도 |
| --- | --- | --- |
| `colors.danger` | `#D32F2F` | 삭제·중단·임계치 초과 |
| (추가) `success` | `#2E7D32` | 정상·체크인 성공 |
| (추가) `warning` | `#F57C00` | 1시간 이내 임계 |

### 2.4 Status Mapping (Pulse Timer)
| 상태 | 색상 | 조건 |
| --- | --- | --- |
| safe | `secondary` (#B2AC88) | 임계치 > 1h |
| warning | `warning` (#F57C00) | 0 < 임계치 ≤ 1h |
| critical | `danger` (#D32F2F) | 임계치 도달 |

---

## 3. 타이포그래피 (Typography)

> 코드 위치: `front/src/theme/typography.ts`  
> 폰트: **Pretendard** (Regular/Medium/Bold)

| Token | Size | Weight | 용도 |
| --- | --- | --- | --- |
| `heading1` | 28pt | Bold | 화면 타이틀 (대) |
| `heading2` | 24pt | Bold | 화면 타이틀 |
| `heading3` | 20pt | Bold | 섹션 헤더 |
| `body1` | 18pt | Medium | 본문 (시니어 대응 +2pt) |
| `body2` | 16pt | Regular | 보조 본문 |
| `caption` | 14pt | Regular | 캡션·메타 |
| `label` | 14pt | Medium | 버튼·태그 |

원칙:
- 기본 라인하이트 `1.5×` 이상.
- 시니어 모드(Phase 5): 모든 사이즈 +2pt 옵션.

---

## 4. 간격 시스템 (Spacing)

8pt 그리드 베이스.

| Token | 값 |
| --- | --- |
| `spacing.xs` | 4 |
| `spacing.sm` | 8 |
| `spacing.md` | 16 |
| `spacing.lg` | 24 |
| `spacing.xl` | 32 |
| `spacing.xxl` | 48 |

---

## 5. 모서리 & 그림자 (Radius & Elevation)

### Radius
| Token | 값 | 용도 |
| --- | --- | --- |
| `radius.sm` | 8 | 작은 배지, 인풋 |
| `radius.md` | 12 | 버튼, 카드 |
| `radius.lg` | 20 | 시트, 모달 |
| `radius.full` | 9999 | Pill, FAB |

### Elevation (iOS shadow / Android elevation)
| Token | iOS shadow | Android elevation |
| --- | --- | --- |
| `elevation.0` | none | 0 |
| `elevation.1` | (0,1,2,0.05) | 1 |
| `elevation.2` | (0,2,6,0.08) | 3 |
| `elevation.3` | (0,4,12,0.12) | 6 |

---

## 6. 컴포넌트 라이브러리 (Components)

### 6.1 기본 컴포넌트

| 컴포넌트 | 위치 | 상태 | 핵심 props |
| --- | --- | --- | --- |
| `Button` (Primary/Secondary/Ghost) | `components/Button.tsx` | 🚧 Planned | variant, size, loading, disabled |
| `Card` | `components/Card.tsx` | 🚧 Planned | title, subtitle, onPress |
| `TextField` | `components/TextField.tsx` | 🚧 Planned | label, error, secureTextEntry |
| `ScreenLayout` | `components/ScreenLayout.tsx` | ✅ Implemented | — |
| `CircularTimer` | `components/CircularTimer.tsx` | ✅ Implemented | size, progress, label |
| `SwipeToConfirm` | `components/SwipeToConfirm.tsx` | ✅ Implemented | onConfirm, label |
| `BottomTabBar` | `components/BottomTabBar.tsx` | ✅ Implemented | tabs, activeKey, onChange |

### 6.2 도메인 컴포넌트 (Heritage Box)
| 컴포넌트 | 위치 | 설명 |
| --- | --- | --- |
| `AssetListItem` | `features/heritage/components/AssetListItem.tsx` | 아이콘 + 이름 + 타입 칩 + 사후처리 배지 |
| `AssetTypeIcon` | `features/heritage/components/AssetTypeIcon.tsx` | 타입별 이모지/아이콘 |
| `ActionBadge` | `features/heritage/components/ActionBadge.tsx` | delete/keep/transfer/memorial 배지 |

---

## 7. 아이콘 & 일러스트

- 1차: 이모지 기반 (간단·국제화 OK).
- 2차(M3 이후): Phosphor Icons 또는 자체 SVG로 통일.

**자산 타입별 이모지 매핑**
| 타입 | 이모지 |
| --- | --- |
| social_account | 💬 |
| subscription | 📺 |
| cloud_storage | ☁️ |
| crypto | 🪙 |
| bank_account | 🏦 |
| document | 📄 |
| custom | ✨ |

**사후 처리 액션 색상**
| Action | 색상 | 이모지 |
| --- | --- | --- |
| delete | danger | 🗑️ |
| memorialize | secondary | 🕯️ |
| transfer | primary | 🤝 |
| keep_private | accent | 🔒 |

---

## 8. 모션 & 햅틱 (Motion & Haptics)

| 이벤트 | 모션 | 햅틱 |
| --- | --- | --- |
| 버튼 탭 | scale 0.96 (150ms) | `haptic.light` |
| 안부 확인 성공 | fade + bounce | `haptic.success` |
| 알림 도달 | 상단 슬라이드 | OS 표준 |
| 삭제 확인 | shake 한 번 | `haptic.warning` |

모션 timing: 기본 `cubic-bezier(0.4, 0.0, 0.2, 1)` (Material Standard).

---

## 9. 화면 레이아웃 패턴 (Layout Patterns)

### 9.1 표준 화면
```
┌───────────────────────────┐
│ SafeArea Top              │
│ ┌─────── Header ────────┐ │
│ │ 타이틀                │ │
│ └───────────────────────┘ │
│                           │
│   Body (ScrollView)       │
│                           │
│   ↑ padding 24px 좌우     │
│                           │
└───────────────────────────┘
│ ┌── Bottom TabBar ──────┐ │
│ │ 홈 │ 유산함 │ 설정    │ │
│ └───────────────────────┘ │
└───────────────────────────┘
```

### 9.2 폼 화면
- 한 화면 최대 5필드.
- 라벨은 인풋 위에. 플레이스홀더 의존 금지.
- 에러는 빨강 1줄 + 햅틱 warning.

### 9.3 빈 상태 (Empty State)
- 일러스트 + 1줄 안내 + 1개 CTA + 추천 항목 리스트.

---

## 10. 접근성 (Accessibility)

| 항목 | 기준 |
| --- | --- |
| 최소 폰트 | 14pt (시스템 설정 따름) |
| 최소 터치 영역 | 44×44 dp |
| 색대비 | WCAG AA (4.5:1 본문, 3:1 큰 글자) |
| 화면 회전 | 세로 고정 (v1.0) |
| 스크린리더 | 모든 인터랙티브 요소 `accessibilityLabel` 필수 |
| 다이내믹 타입 | iOS Dynamic Type 대응 (M4) |

---

## 11. 보이스 & 톤 (Voice & Tone)

| 상황 | 톤 | 예시 |
| --- | --- | --- |
| 환영 | 따뜻·격려 | "오늘도 안전하게 지켜드릴게요." |
| 성공 | 차분 | "안부를 확인했어요." (느낌표 자제) |
| 경고 | 단정·구체 | "8시간째 활동이 없습니다. 괜찮으신가요?" |
| 죽음·민감 | 존중·정중 | "이 항목은 떠나신 후 어떻게 처리할까요?" |
| 결제 | 투명 | "월 4,900원 · 언제든 해지" |

금기:
- "사망", "돌연사" 같은 단어는 본문에서 자제. UI에서는 "떠나신 후", "사후" 등으로.
- 느낌표·이모지 남발 금지 (의례성 손상).

---

## 12. 다크 모드 (Dark Mode)

v1.0 라이트 모드만. v1.1 다크 모드 토큰 정의 예정.

- Primary는 `#5A8FBF` (탈도 낮춤)
- Background `#121417`
- Surface `#1C1F23`

---

## 13. 디자인 핸드오프 체크리스트

신규 화면 추가 시 다음 항목을 모두 충족해야 머지 가능.

- [ ] 폰트 토큰 사용 (raw 숫자 금지)
- [ ] 색상 토큰 사용 (HEX 직접 금지)
- [ ] 8pt 그리드 준수
- [ ] 터치 영역 44dp 이상
- [ ] accessibilityLabel 모두 부여
- [ ] 빈 상태 / 에러 상태 / 로딩 상태 디자인
- [ ] 다이내믹 폰트 사이즈에서 깨지지 않음
- [ ] 색대비 WCAG AA
