# Changelog

InRem 프로젝트의 주요 변경 이력입니다.
[Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 규칙을 따릅니다.

## [Unreleased] - 2026-05-19 (오후 늦게) — Bug·보안·UX·정리 16건 일괄

### Fixed (Bug 3건)
- **HomeScreen 페이월 Alert invisible (RN Web)** — `Alert.alert` 대신
  새 `Toast` 컴포넌트로 inline 안내. 체크인 성공/실패도 같은 토스트로.
- **`useAssets` 검색 race condition** — `requestSeq` ref 로 stale 응답
  무시. 빠른 타이핑 시 늦게 도착한 결과가 최신 결과를 덮어쓰지 않음.
- **AssetFormScreen 클립보드 타이머 무한 갱신** — `secret` 변경마다
  timer 가 reset 되어 영원히 안 비워지던 버그. 페이스트 감지 시 한 번만
  timer 예약, snapshot 으로 동일 paste 재예약 방지. UI 안내도 동기화.

### Added (보안 5건)
- **`REGISTER_LIMITER`** 5/시간 per IP — 자동 가입 farm 차단.
- **`HEARTBEAT_LIMITER`** 60/분 per user — 무한 reset 공격 차단.
- **`UPSELL_CLICK_LIMITER`** 30/분 per user — KPI 메트릭 조작 차단.
- **Guardian 양방향 cascade 검증** — ward 측·guardian 측 어느 쪽을
  삭제해도 매핑 행이 사라지는지 통합 테스트로 확인.
- **production 가드** — `ENV=production` + Gmail 미설정 시
  `EmailConfigError` startup fail-fast. silent Mock 폴백 차단.

### Added (UX 3건)
- **비밀번호 보기 토글** — Login 입력 우측 inline 버튼, Signup 라벨 우측
  버튼 (양쪽 비밀번호·확인 동시 토글).
- **AssetFormScreen 분류 → 처리 방식 자동 추천** —
  `DEFAULT_ACTION_FOR_TYPE` 매핑 (social→memorialize / subscription→
  delete / cloud·crypto·bank·document→transfer / custom→keep_private).
  사용자가 처리 방식을 직접 만진 적 없을 때만 동기화. 안내 문구 노출.
- **체크인 성공 토스트** — SwipeToConfirm 후 "안부 확인 완료! 타이머가
  연장됐어요" 토스트로 명시적 피드백.

### Changed (코드 품질 / 문서 2건)
- **Pydantic v1 → v2 `ConfigDict` 마이그레이션** — 6개 schema +
  `config.py`. `class Config:` 패턴 모두 제거, deprecation warning 8건
  → 0건 (sqlalchemy 1건만 잔존, 별개 마이그레이션).
- **README 전면 갱신** — v1.0 진행 상황 반영 (Heritage·삭제 흐름·페이월·
  JWT 회전·rate-limit 6종·CORS·prod 가드·반응형·관측성·QA 스크립트).

### Verified
- 백엔드 pytest **56/56** (이전 52 + 4 신규 — register rate-limit·
  cascade 대칭·prod 가드 등).
- `tsc --noEmit` exit 0.
- 회귀: 기존 109/109 모두 통과 유지.

### Known Gaps (이후)
- 백엔드 docker 이미지 stale (Docker Hub 액세스 막혀 재빌드 안 됨).
  로컬 native poetry 환경으로 QA 진행, 호스팅 환경에서 재빌드 필요.
- Jest 인프라 잔여 — Expo winter runtime + Node 25 호환성.

---

## [Unreleased] - 2026-05-19 (점심) — 반응형 컨테이너

"어떤 환경에서도 동일한 UI/UX" 를 위해 모바일-퍼스트 디자인을 모든
viewport 에서 보존하는 ResponsiveShell 도입. 새로운 레이아웃을 그리지
않고 모바일 UX 를 중앙 고정 폭으로 띄워서 일관성을 보장한다.

### Added
- `src/hooks/useResponsive.ts` — `useWindowDimensions` 기반.
  `MAX_CONTENT_WIDTH = 480` 상수 + `{ width, height, isShellWider }` 반환.
- `src/components/ResponsiveShell.tsx`
  - 모바일 폭(≤480): 풀스크린, 추가 효과 없음.
  - 태블릿·웹·데스크톱: 480 폭 컨테이너 중앙 정렬, 외곽 `colors.shell`
    배경 + 그림자로 카드처럼 떠 있는 효과.
  - native (iPad 가로 등) 와 web 모두 동일 동작.
- `colors.shell = #E3E7EC` — 모바일 프레임 외곽 셸 배경.
- `scripts/qa_responsive.py` — 5 viewport 매트릭스 자동 QA
  (320 / 414 / 768 / 1280 / 1920). 각 viewport 별:
  · 회원가입 → 홈 → 유산함 자동 시나리오
  · `min(viewport, 480)` 으로 inner 컨테이너 폭 정확히 측정
  · 스크린샷 3장씩 캡처 (로그인 · 홈 · 유산함)

### Changed
- `App.tsx` 최상위 `<GestureHandlerRootView>` 아래에 `<ResponsiveShell>`
  추가. 자식 트리 (AuthProvider → AppContent) 가 그 안에서 렌더링.

### Verified
- **5/5 viewport QA 통과** — 모든 화면 폭에서 모바일 프레임 무결성·
  width 측정 정확.
- `tsc --noEmit` exit 0.
- 회귀: 기존 109/109 (단위·백엔드·프론트 happy·visual) 영향 없음.
- 스크린샷: `resp-{phone-small,phone,tablet,desktop,desktop-xl}-
  {1-login,2-home,3-heritage}.png` 총 15장.

---

## [Unreleased] - 2026-05-19 (오전) — 시각 QA 보완 + Alert→inline 에러 배너

### Fixed (Bug #3, visual QA 도중 발견)
- **`Alert.alert` invisible on RN Web** → LoginScreen / SignupScreen
  은 사용자 입력 에러를 alert dialog 로 띄우는데 Web 에서 안 보임.
  inline `errorBanner` state + `<View>` 로 교체. Web/Native 모두
  동일하게 노출.

### Added
- `scripts/qa_web_visual.py` — Playwright 17 시나리오:
  · Login 화면 직접 노출
  · 잘못된 로그인 → 빨간 배너 노출 검증
  · HomeScreen 페이월 카드 (Premium 배지 + 가족공유)
  · 유산함 빈 상태 추천 5종 + 자산 폼 6필드
  · 시크릿 입력 → "30초 후 클립보드 비움" 안내
  · 자산 저장 후 목록 (검색바·필터 칩·요약 카드)
  · 설정 위험 영역 (계정 삭제 + PIPA 30일 안내)
  · runtime console.error 0 (의도된 401 4xx 부산물 제외)
- 보완 스크린샷 (`/tmp/inrem-qa-screenshots/visual-*`,
  `extra-*-bottom.png`) — ScrollView 내부 강제 스크롤로 페이월 카드·
  위험 영역까지 풀 캡처.

### Verified
- 시각 QA **17/17** 통과.
- 누적 109/109: 백엔드 28 + 프론트 happy 12 + 프론트 visual 17 + pytest 52.

---

## [Unreleased] - 2026-05-19 (이른아침) — Cross-user FK SET NULL + E2E QA

### Fixed (실제 production bug 2건 — QA 도중 발견)
- **`SafeAreaProvider` 누락 → React 트리 crash**: Web 빌드에서 페이지가 완전히 빈 화면. iOS/Android 에서도 `useSafeAreaInsets`/`SafeAreaView` 가 사용 중이라 잠재적 위험. `App.tsx` 최상위에 추가.
- **`expo-secure-store` Web crash**: `n.default.deleteValueWithKeyAsync is not a function` → 회원가입 후 토큰 저장 실패 → 인증 진행 차단. `tokenStorage` 를 platform-aware 로 변경 (Web → `localStorage`, native → SecureStore).

### Added
- **`ON DELETE SET NULL` 마이그레이션** (`f4b1c2a3d8e7_cross_user_fk_set_null`):
  - `assets.designated_executor_id` (FK 이름 `fk_assets_designated_executor_id_users`)
  - `pulse_events.resolved_by` (FK 이름 `pulse_events_resolved_by_fkey`)
  - 다른 사용자(executor / resolver) 가 PIPA purge 로 삭제돼도 자산/이벤트는 보존, 포인터만 NULL.
- **QA 인프라**:
  - `scripts/qa_smoke.sh` — 백엔드 8 시나리오 (28 assertions) curl 기반 E2E.
  - `scripts/qa_web.py` — Playwright 헤드리스 Chromium 으로 Expo Web 정적 번들 driving (12 assertions, full signup → home → tabs flow + 콘솔/네트워크 클린 검증).
- **`document/operations/qa_report_2026_05_19.md`**: QA 실행 결과, 발견 버그, 미커버 영역, 재현 절차.

### Changed
- `back/app/main.py` — CORS 기본 화이트리스트에 `http://localhost:8090` 추가 (QA 정적 서버).

### Verified (QA)
- 백엔드 API E2E **28/28** (qa_smoke.sh).
- 프론트 Web E2E **12/12** (qa_web.py).
- 단위/통합 pytest **52/52**.
- `tsc --noEmit` exit 0.
- 실 렌더링 스크린샷 6장 (`/tmp/inrem-qa-screenshots/01..06.png`).

### Known Gaps (출시 전)
- iOS / Android 실 디바이스 베타 — TestFlight / Play Internal 단계.
- 푸시 알림 (FCM) 실 발송 — Firebase 자격증명 필요.
- 이메일 fallback 실 발송 — 사용자가 Gmail 앱 비밀번호 발급 후.
- Jest 잔여 — Expo winter runtime + Node 25 호환성 (LoginScreen 1 테스트 미실행).

---

## [Unreleased] - 2026-05-19 (새벽) — 디자인 자산 + 출시 직전 7건

### Added
- **브랜드 디자인 자산** — "Quiet Watch" (조용한 시선) 컨셉
  - `front/assets/brand/icon.svg` · `adaptive-foreground.svg` · `splash.svg`
  - `scripts/build_brand_assets.py` — cairosvg 일괄 렌더링
  - 생성된 PNG: `icon.png` `adaptive-icon.png` `splash.png` `splash-icon.png` `favicon.png` `logo.png` `logo_with_background.png`
  - `app.json` 갱신: icon/splash/adaptiveIcon, 배경 `#003366`
- **앱 스토어 메타데이터** (`document/operations/app_store_metadata.md`)
  - 한/영 카피 (subtitle/short/long), 키워드, Apple Privacy Labels / Google Data Safety, 심사 우려 사항·대응
- **JWT refresh token 메커니즘**
  - access 30분 + refresh 30일 분리. `_create_token`/`_decode_with_type` 으로 토큰 타입 격리 (cross-type 거부)
  - `POST /api/v1/auth/refresh` — 회전 + 사용자 상태 재검증 (deletion-pending/inactive 거부)
  - 프론트 axios interceptor 401 자동 재시도 (single in-flight refresh promise, refresh URL 무한루프 방지)
- **시크릿 클립보드 자동 클리어** — `expo-clipboard` 사용, 30초 후 OS 클립보드 현재값이 입력 secret 과 일치할 때만 비움. 안내 배너 표시
- **에러 메시지 다양화** — `describeError()` 헬퍼 (`api/client.ts`). 401/403/404/410/422/429+Retry-After/5xx/타임아웃/오프라인 분기. useAssets·SettingsScreen·LoginScreen 적용
- **Guardian 보안 강화** (감사 결과)
  - 초대 rate-limit `GUARDIAN_INVITE_LIMITER` (5/시간/사용자) — invitation 코드 dict DoS 방지
  - `inrem.audit.guardian` 감사 로그 — invitation_created / accepted / removed
  - `UniqueConstraint(ward_id, guardian_id)` + alembic `e3a9f1b2c4d5`
- **User cascade 무결성** — `User` ORM cascade `all, delete-orphan` 추가 (activity_signals/assets/monitoring_policy/pulse_events/timer_status/user_config/guardians/wards/records). PIPA purge 가 IntegrityError 없이 동작

### Tests
- `tests/test_auth_refresh.py` 5종 — 타입 격리·회전·계정 상태 검증
- `tests/test_account_cascade.py` 2종 — 통합 cascade 검증 (in-memory SQLite, Record JSONB swap)
- `tests/test_guardian_security.py` 5종 — invite rate-limit·audit 3종·unique 제약 통합
- 백엔드 전체 **52/52 통과**, 프론트 `tsc --noEmit` exit 0
- `describeError` 7/7 — Jest 인프라 잔여로 별도 node 런타임 검증

### Changed
- `back/app/core/security.py` — TokenType literal + create_refresh_token/decode_refresh_token.
- `back/app/services/auth_service.py` — register/authenticate 가 `(user, access, refresh)` 튜플 반환.
- `back/app/core/config.py` — `REFRESH_TOKEN_EXPIRE_DAYS` 추가.
- `back/app/models/user.py` — 모든 owner-side relationship 에 `cascade="all, delete-orphan"`.
- `back/app/models/guardian.py` — `UniqueConstraint(ward_id, guardian_id)`.
- `front/src/api/client.ts` — `tokenStorage`, `describeError`, axios refresh interceptor.
- `front/src/context/AuthContext.tsx` — refresh token 함께 저장.
- `front/src/screens/AssetFormScreen.tsx` — 클립보드 자동 wipe + 안내 배너.
- `front/src/screens/{Login,Settings}Screen.tsx`, `features/heritage/hooks/useAssets.ts` — `describeError` 적용.
- `front/app.json` — 새 브랜드 자산 + 배경색 `#003366`.

### Known Gaps (출시 전)
- `Asset.designated_executor_id` / `PulseEvent.resolved_by` 의 dangling FK — `ON DELETE SET NULL` alembic 마이그레이션 필요.
- 스토어 스크린샷 — 빌드 후 실 화면 캡처 필요 (디자이너 없이는 디바이스 mockup 만 가능).
- 도메인 / 고객 지원 이메일 (`{{TBD@inrem.app}}`) 발급 후 약관·정책 placeholder 치환.

---

## [Unreleased] - 2026-05-19 (심야) — 출시 차단 항목 4건 처리

`document/release_checklist.md` 의 P1~P4 자율 처리 가능 항목 일괄 진행.

### Added
- **30일 grace 만료 영구 삭제 스케줄러** (PIPA 잊혀질 권리 완결)
  - `account_service.purge_expired_deletions()` — `deletion_requested_at < now-30d` 인 사용자 hard-delete.
  - `scheduler.AccountPurgeScheduler` — 24h 주기 + 시작 시 1회 즉시 sweep.
  - `inrem.audit.account` 에 `account_purged` 이벤트 (커밋 전 로그 → 재시도 안전).
- **로그인 rate-limit (브루트포스 방지)**
  - `LOGIN_LIMITER` (분당 5회, `email + client_ip` 키).
  - `X-Forwarded-For` 우선 → 직접 IP 폴백.
  - 초과 시 429 + Retry-After.
- **CORS 명시화**
  - `CORSMiddleware` 추가, `CORS_ALLOW_ORIGINS` 환경변수로 화이트리스트.
  - 미설정 시 `localhost:8081/19006/3000` 개발 기본값.
- **`GET /api/v1/signal/status` (부수효과 없는 조회)**
  - `last_active_at` + `deletion_requested_at` 스냅샷.
  - HomeScreen 60초 폴링용 → 다른 디바이스 활동을 새 heartbeat 없이 반영.
- **HomeScreen 폴링** — `signalApi.getStatus()` 60초 간격, 활동 최신 값만 채택.

### Tests
- `tests/test_account.py` purge 2종 + login rate-limit 2종 (= 4 신규).
- `tests/test_cors.py` 3종 (파서 + 프리플라이트).
- `tests/test_signal_status.py` 3종 (status 응답·삭제대기 노출·부수효과 없음).
- 백엔드 전체 **39/39 통과**, 프론트 `tsc --noEmit` exit 0.

### Changed
- `back/app/main.py` — `_cors_origins()` parser + CORSMiddleware.
- `back/app/core/config.py` — `CORS_ALLOW_ORIGINS` 환경 설정.
- `.env.example` — CORS / Gmail 안내 갱신.

---

## [Unreleased] - 2026-05-19 (밤) — Gmail SMTP 이메일 프로바이더

### Added
- **`GmailSMTPProvider`** (`back/app/services/email_service.py`)
  - `aiosmtplib` 기반 STARTTLS / 587 / App Password 인증.
  - 발송 성공·실패 모두 구조화 로그 (`gmail_send_ok` / `gmail_send_failed`).
  - 실패는 ERROR + exc_info=True 로 강제 노출 — 안전 알림 미도달은 치명적.
- **자동 프로바이더 선택** (`_build_default_provider`):
  - `GMAIL_USERNAME` + `GMAIL_APP_PASSWORD` 설정되면 Gmail 사용.
  - 미설정이면 `MockEmailProvider` 폴백 (개발 안전).
- **환경 변수** (`back/app/core/config.py`):
  - `GMAIL_USERNAME`, `GMAIL_APP_PASSWORD`, `GMAIL_FROM_NAME` (기본 "InRem").
- **셋업 가이드**: `document/operations/email_gmail_setup.md`
  - 2단계 인증 활성화 → 앱 비밀번호 생성 → `.env` 입력 → 발송 테스트 절차.
  - 발송 한도(500/일)·스팸 분류 회피·프로덕션 마이그레이션 체크리스트.
- **`.env.example`** 갱신.
- **의존성**: `aiosmtplib ^5.1.0`

### Tests
- `back/tests/test_email.py` — 5종 (프로바이더 선택 2 + 발송 성공/실패 2 + Mock 1)
- 백엔드 전체 **29/29 통과**.

### Known Gaps (출시 전)
- Gmail 은 dev/alpha 한정. Public launch 전 Resend/SendGrid/SES 로 교체 필요 (가이드 문서 마지막 섹션 참조).
- 발송 실패 시 자동 재시도 / bounce webhook 처리 없음 (Gmail SMTP 한계).

---

## [Unreleased] - 2026-05-19 (저녁) — 출시 베이스라인 강화

### Added (신규)
- **계정 삭제 / 잊혀질 권리 (PIPA, PRD §6 NFR)**
  - 백엔드: `DELETE /api/v1/auth/me` (idempotent), `POST /api/v1/auth/me/restore` (grace 만료 시 410)
  - `back/app/services/account_service.py` — `request_deletion`/`restore`/`grace_remaining` (30일 grace)
  - `back/alembic/versions/d2e8f4b6c1a3_…` — `users.deletion_requested_at` 마이그레이션
  - `auth_service.authenticate_user` — pending-deletion 사용자 새 로그인 차단 (기존 세션은 grace 동안 restore 가능)
  - 감사 로그: `inrem.audit.account` ("account_deletion_requested" / "_restored")
  - 프론트: `SettingsScreen` 위험 영역 섹션 + `accountApi`
- **시크릿 reveal 보안 강화 (PRD §5.1.3)**
  - `back/app/core/rate_limit.py` — `SlidingWindowRateLimiter` (인메모리 토큰 버킷)
  - `GET /api/v1/heritage/assets/{id}/secret` 분당 10회 제한 + 감사 로그 (`inrem.audit.heritage`)
- **법적 베이스라인 문서**
  - `document/legal/README.md`, `privacy_policy.md`, `terms_of_service.md` — 초안 (변호사 자문 전, `{{TBD}}` 플레이스홀더)
- **구조화 (JSON) 로깅 베이스**
  - `back/app/core/logging.py` — `JsonFormatter` + `configure_logging()` + `configure_sentry()` (옵션)
  - `main.py` 모듈 import 시점에 초기화. `SENTRY_DSN` 환경변수로 Sentry on/off.

### Fixed (버그)
- **HomeScreen lastActiveAt 초기값**: 마운트 직후 잘못된 "풀바" 표시 → 서버 응답 도착 전까지 로딩 스피너로 대체.
- **AssetFormScreen 시크릿 편집 UX**: "기존 정보 덮어씀" 모호한 placeholder 제거. 저장된 비밀이 있을 때 상태 배너 표시, "저장된 비밀 삭제" 버튼 추가 (clear_secret 백엔드 옵션 연결).
- **useAssets 에러 회복**: HeritageBoxScreen 에러 배너에 "다시 시도" 버튼.

### Changed (변경)
- `back/app/models/user.py` — `deletion_requested_at` 컬럼 추가.
- `back/app/api/v1/auth.py` — DELETE/me, POST/me/restore 라우트.
- `back/app/core/config.py` — `LOG_LEVEL`, `SENTRY_DSN` 환경 설정.
- `back/app/main.py` — JSON 로깅·Sentry 초기화 hook.
- `front/src/api/client.ts` — `accountApi` 추가.
- `front/src/screens/SettingsScreen.tsx` — 위험 영역(계정 삭제) + 로그아웃 섹션.
- `front/package.json` — `react-native-worklets`, `babel-preset-expo` devDep, `react-test-renderer` 19.1.0 핀, test script에 `NODE_OPTIONS` 추가.
- `front/jest.setup.js` — stale `@react-navigation/native` 모킹 제거.

### Verified (검증)
- 백엔드: pytest **24/24 통과** (Heritage 9 + Settings 2 + Account 8 + Timer 2 + Logging 3)
- 프론트엔드: `tsc --noEmit` exit 0
- Jest: 4개 인프라 이슈 해소 (worklets·babel-preset-expo·stale mock·tester 버전), **잔여 1건** (Expo winter runtime + Node 25 호환성) 별도 작업 필요 — LoginScreen 테스트는 임시로 실행 불가.

### Known Gaps (출시 전 추가 작업 필요)
- **30일 grace 종료 시 사용자 + 데이터 영구 삭제 cron job** — `back/app/services/scheduler.py` 에 sweep 작업 추가 필요.
- **법무 자문 후 `{{TBD}}` 치환 및 약관 동의 흐름 UI**.
- **Sentry 실제 DSN 설정 + sentry-sdk 의존성 추가** (현재는 코드만 ready).
- **결제 모듈**: 사업자 등록 후 진행.

---

## [Unreleased] - 2026-05-19 (오후)

### Added (신규)
- **Heritage Box 검색·필터** (PRD §5.1.4)
  - 백엔드: `GET /api/v1/heritage/assets?search=&type=` — 이름 부분일치(ILIKE) + 타입 필터
  - 프론트: `HeritageBoxScreen` 상단 검색 TextInput (300ms debounce) + 타입 필터 칩 가로 스크롤
  - 결과 0건 시 "필터 초기화" CTA
- **HomeScreen 데일리 Heritage 추천 카드** (PRD §5.2)
  - 진입 시 `heritageApi.getSummary()` 호출, 0항목/N항목 분기 메시지
  - 탭 시 유산함 탭으로 이동 (`MainTabsScreen` → `HomeScreen` `onNavigate` prop)
- **Premium 페이월 카드 — 가족공유** (PRD §2.1 goal 4 / §5.5 신규)
  - HomeScreen 하단 카드, 탭 시 백엔드 클릭 로깅 + "곧 출시" Alert
  - 백엔드: `POST /api/v1/settings/upsell/click` (logger `inrem.upsell` 구조화 기록, DB 미도입)
  - 프론트: `upsellApi.logClick(feature, surface)`
- **테스트**
  - `back/tests/test_settings.py` — 페이월 클릭 로깅·스키마 검증 2종
  - `back/tests/test_heritage.py` — 검색·타입 쿼리 전달 검증 1종 추가

### Changed (변경)
- `back/app/repositories/asset_repository.py` — `list_by_user` 에 `search: str | None` 인자 추가
- `back/app/services/asset_service.py` — `list_assets` `search` pass-through
- `back/app/api/v1/heritage.py` — `search` 쿼리 파라미터 (max_length=120)
- `back/app/schemas/settings.py` — `UpsellClickRequest` / `UpsellClickResponse`
- `front/src/api/client.ts` — `heritageApi.listAssets({ search })`, `upsellApi` 추가
- `front/src/features/heritage/hooks/useAssets.ts` — `UseAssetsOptions { search, typeFilter }` 지원
- `front/src/screens/MainTabsScreen.tsx` — `MainTabKey` export, `HomeScreen` 에 `onNavigate` 전달
- `document/PRD.md` — §5.1.2 search 쿼리, §5.1.4 필터 UX, §5.5 페이월 절 추가

### Verified (검증)
- 백엔드: pytest **9/9 통과** (Heritage 7 + Settings 2)
- 프론트엔드: `tsc --noEmit` exit 0

---

## [Unreleased] - 2026-05-19

### Added (신규)
- **문서 4종**
  - `document/personas.md` — 페르소나·핵심 타겟 정의 (P1 1인 가구 중년, P2 보호자, P3 시니어)
  - `document/user_journey_map.md` — 5단계 사용자 여정 지도, 감정 곡선, Moments of Truth
  - `document/PRD.md` — v1.0 PRD (Stage 1 완성 + Stage 2 Heritage Box MVP)
  - `document/design_system.md` — "Warm Serenity" 디자인 시스템 토큰
- **Heritage Box (Stage 2 - 디지털 유산 인벤토리) 백엔드**
  - `back/app/api/v1/heritage.py` — REST 엔드포인트 7종
  - `back/app/services/asset_service.py` — Fernet 자동 암복호화, 소유자 격리
  - `back/app/repositories/asset_repository.py`
  - `back/app/schemas/asset.py`
  - `back/alembic/versions/c1a2b3d4e5f6_expand_assets_for_heritage_box.py` — DB 마이그레이션
  - `back/tests/test_heritage.py` — 단위·API 테스트 6종
- **Heritage Box 프론트엔드**
  - `front/src/screens/HeritageBoxScreen.tsx` — 자산 목록·요약·빈 상태 추천
  - `front/src/screens/AssetFormScreen.tsx` — 자산 추가/수정 폼 (암호화 표시)
  - `front/src/features/heritage/` — 메타데이터, AssetListItem, SegmentedControl, useAssets 훅 (MVVM)
- **네비게이션**
  - `front/src/components/BottomTabBar.tsx` — 외부 의존성 없는 하단 탭
  - `front/src/screens/MainTabsScreen.tsx` — 홈/유산함/설정 3탭
- **디자인 토큰**
  - `front/src/theme/spacing.ts` — 8pt 그리드, radius 토큰

### Changed (변경)
- `back/app/models/asset.py` — Heritage Box용 컬럼 확장 (name, identifier, action_on_death, designated_executor_id, note, timestamps)
- `back/app/api/v1/__init__.py` — heritage 라우터 등록
- `back/app/models/__init__.py`, `repositories/__init__.py`, `services/__init__.py`, `schemas/__init__.py` — Heritage 모듈 export
- `front/App.tsx` — 인증 후 진입을 HomeScreen → MainTabsScreen
- `front/src/api/client.ts` — `heritageApi` 추가, 타입(`Asset`, `AssetType`, `ActionOnDeath` 등) 추가
- `front/src/theme/colors.ts` — `success`, `warning`, `overlay` 토큰 추가

### Verified (검증)
- 백엔드: pytest 8/8 통과 (Heritage 6 + Timer 2)
- 프론트엔드: `tsc --noEmit` exit 0
- FastAPI: `/api/v1/heritage/*` 7개 라우트 정상 등록 확인

---

## [기존 커밋 이력 — git log]

- `91551d9` test: add testing infrastructure, scripts and guidelines
- `2f32335` feat: implement monitoring policy settings, email fallback service, and update documentation
- `b7db56a` Initial commit
