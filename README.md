# InRem (인램) - 디지털 돌봄 & 모니터링 플랫폼

InRem은 비침습적 활동 감지와 자동화된 안부 확인을 통해 1인 가구 및 시니어의 안녕을 모니터링하기 위해 설계된 디지털 돌봄 플랫폼입니다.

## 🏗 기술 스택 (Technology Stack)

- **백엔드**: FastAPI (Python 3.12), SQLAlchemy (Async), Alembic, Pydantic
- **프론트엔드**: React Native (Expo), TypeScript, React Navigation
- **데이터베이스**: PostgreSQL 15 (Docker)
- **인프라**: Docker, Docker Compose
- **알림**: Firebase Cloud Messaging (FCM)
- **보안**: Fernet 암호화 (Cryptography), JWT 인증

---

## 🚀 구현된 서비스 (현재 상태)

### 1. 핵심 인프라 (Core Infrastructure)
- **컨테이너화**: 백엔드 및 데이터베이스 서비스의 완전한 Docker 지원 (`docker-compose.yml`).
- **데이터베이스 관리**:
    - 비동기(Async) SQLAlchemy 세션 관리.
    - Alembic을 통한 자동 마이그레이션 (`alembic upgrade head`).
- **CI/CD**: GitHub Actions 워크플로우 (`ci.yml`)를 통한 자동화된 테스트 및 린팅.

### 2. 인증 및 보안 (Authentication & Security)
- **JWT 인증**: 액세스 토큰 생성 및 검증 (`/api/v1/auth/login`).
- **보안**:
    - bcrypt를 이용한 비밀번호 해싱.
    - **암호화 서비스**: 민감한 사용자 정보(PII)에 대한 Fernet 필드 레벨 암호화 적용.

### 3. 가디언 펄스 (Guardian Pulse - 활동 모니터링 엔진)
비활동을 감지하고 안부 확인 수명주기를 관리하는 핵심 엔진입니다.

- **하트비트 시스템 (Heartbeat System)**:
    - **API**: `POST /api/v1/signal/heartbeat`
    - **앱 상태 로직**: 앱 포그라운드/백그라운드 진입 및 실행 이벤트를 자동으로 추적합니다.
    - **디바운싱**: 서버 과부하 방지를 위해 1분의 쿨다운 타임을 적용했습니다.
- **펄스 엔진 (`services/pulse_engine.py`)**:
    - **비활동 감지**: 백그라운드 스케줄러가 주기적으로 `last_active_at`을 확인합니다.
    - **안심 시간 (Quiet Hours)**: 사용자가 설정한 수면 시간(예: 23:00 - 07:00)에는 오탐 방지를 위해 알림을 억제합니다.
- **소프트 체크인 (Level 1 알림)**:
    - **트리거**: 비활동 임계치 도달 시 FCM을 통해 "잘 지내시나요?" 푸시 알림을 전송합니다.
    - **응답**: 사용자가 "잘 있어요" 버튼을 누르면 (`POST /api/v1/pulse/respond`) 타이머가 초기화됩니다.
- **하드 체크인 (Level 2 에스컬레이션)**:
    - **에스컬레이션 로직**: 소프트 체크인 후 `escalation_delay` 분 동안 응답이 없을 경우 발동합니다.
    - **보호자 알림**: 등록된 모든 보호자에게 멀티캐스트 FCM 긴급 알림을 전송합니다.
    - **이메일 백업**: **[NEW]** 푸시 알림 전송 실패 시 이메일 알림을 자동으로 발송합니다 (`services/email_service.py`).

### 4. 보호자 관리 시스템 (Guardian Management)
- **관계 모델**: N:M 다대다 관계 지원 (한 피보호자가 여러 보호자를, 한 보호자가 여러 피보호자를 가질 수 있음).
- **초대 흐름**:
    - **코드 생성**: `POST /api/v1/guardian/invite` (6자리 숫자 코드 반환, 24시간 유효).
    - **코드 수락**: `POST /api/v1/guardian/accept` (보호자와 피보호자 연결).
- **관리**: 보호자/피보호자 목록 조회 및 연결 해제 API.

### 5. 알림 시스템 (Notification System)
- **FCM 인프라**:
    - 토큰 등록 및 관리 (`/api/v1/device/register`).
    - 멀티캐스트 메시징 지원 (여러 보호자 기기에 동시 전송).
- **백업 메커니즘 (Fallback)**:
    - FCM 전송 실패를 감지합니다.
    - 긴급 알림의 경우 자동으로 이메일 서비스(현재 Mock 구조 구현됨)로 우회 처리합니다.

### 6. 사용자 설정 및 정책 (Settings & Policy)
- **모니터링 정책**:
    - **API**: `GET/PATCH /api/v1/settings/policy`
    - **설정 가능한 옵션**:
        - **민감도**: 느슨함 (24h) / 보통 (12h) / 엄격함 (6h).
        - **안심 시간**: 알림을 받지 않을 시작/종료 시간 설정.
        - **에스컬레이션**: 보호자 알림 활성화/비활성화.
        - **모니터링**: 전체 기능 켜기/끄기.

### 7. 타이머 시스템 (Timer System)
- **데드맨 스위치 (Dead Man's Switch)**:
    - **목적**: 사용자가 일정 기간 동안 활동이 없으면 자동으로 알림을 트리거하는 안전 장치.
    - **구성**:
        - `UserConfig`: 사용자별 주기(Period) 및 유예 시간(Grace Period) 설정.
        - `TimerStatus`: 마지막 체크인 및 마감 기한(Deadline) 관리.
    - **API**: `POST /api/v1/timer/reset` (타이머 리셋 및 마감 기한 갱신).

### 8. 디지털 유산함 (Heritage Box — Stage 2 MVP)
사용자가 떠난 후의 디지털 자산 처리 의사를 미리 정리·암호화해 보관합니다.

- **자산 인벤토리**:
    - **API**: `GET/POST/PATCH/DELETE /api/v1/heritage/assets` + `/summary`
    - **검색·필터**: `?search=`(이름 부분일치 ILIKE) + `?type=`(타입 필터).
    - **민감 정보 암호화**: Fernet 자동 암복호화. 응답에 ciphertext 노출 없음.
- **시크릿 reveal 보안**:
    - **API**: `GET /api/v1/heritage/assets/{id}/secret`
    - **분당 10회 rate-limit** + `inrem.audit.heritage` 구조화 감사 로그.
- **빈 상태 추천 5종**: Instagram·Netflix·Google Drive·은행 계좌·중요 문서.
- **클립보드 자동 클리어** (프론트): 시크릿 페이스트 감지 후 30초 후 OS 클립보드 비움.

### 9. 잊혀질 권리 — PIPA 계정 삭제 흐름
- **삭제 요청**: `DELETE /api/v1/auth/me` (idempotent) → `deletion_requested_at` 스탬프.
- **복구**: `POST /api/v1/auth/me/restore` — grace 만료 시 410.
- **30일 grace 종료 후 영구 삭제**: `AccountPurgeScheduler` (24h 주기 sweep) + User cascade 로 종속 행 자동 정리. cross-user FK (executor·resolver) 는 `ON DELETE SET NULL`.

### 10. Premium 페이월 — 가족공유 (전환 가설 검증)
- **API**: `POST /api/v1/settings/upsell/click` — 결제 모듈 전 단계 KPI 검증용 구조화 클릭 로깅.
- **HomeScreen 노출** + inline Toast 안내. 분당 30회 rate-limit.

### 11. 보안 베이스라인
- **JWT 회전**: access 30분 + refresh 30일. `/auth/refresh` 에서 회전. 토큰 타입 cross-use 거부.
- **Rate-limit 5종** (인메모리 sliding window):
    - `/auth/login` — 5/분 per (email, IP).
    - `/auth/register` — 5/시간 per IP.
    - `/signal/heartbeat` — 60/분 per user.
    - `/heritage/assets/{id}/secret` — 10/분 per user.
    - `/guardian/invite` — 5/시간 per user.
    - `/settings/upsell/click` — 30/분 per user.
- **CORS** 환경변수 화이트리스트 (`CORS_ALLOW_ORIGINS`).
- **production 가드**: `ENV=production` 인데 이메일 프로바이더 자격증명 없으면 startup fail-fast.

### 12. 관측성 (Observability)
- **구조화 JSON 로깅**: `inrem.audit.heritage / account / guardian` + `inrem.upsell` 카테고리.
- **Sentry-ready**: `SENTRY_DSN` 설정 시 자동 활성, 미설정 시 no-op.

### 13. 프론트엔드 — 반응형 + UX
- **반응형 컨테이너 (`ResponsiveShell`)**: 모바일·태블릿·데스크톱·iPad 가로 등 어떤 viewport 에서도 동일한 모바일 UX. 큰 화면에서는 480폭 컨테이너가 중앙 정렬되고 외곽엔 셸 배경.
- **하단 탭 네비**: 홈(Pulse) · 유산함(Heritage) · 설정(Settings).
- **에러 UX**: `describeError()` 헬퍼로 401/403/404/410/422/429+Retry-After/5xx/타임아웃/오프라인 한국어 매핑.
- **인증 화면 inline 에러 배너**: `Alert.alert` 가 RN Web 에서 invisible 한 문제 회피.
- **비밀번호 보기 토글** (Login·Signup).
- **자동 토큰 회전**: axios interceptor 가 401 응답 시 single-in-flight refresh 후 원요청 재시도.

---

## 📦 디자인 자산
- 브랜드 아이덴티티: "Quiet Watch" — Deep Ocean Blue + Soft Sage + Warm Sand
- 마스터 SVG: `front/assets/brand/{icon,adaptive-foreground,splash}.svg`
- 일괄 PNG 렌더링: `python3 scripts/build_brand_assets.py`

## 🧪 QA & 테스트
- 백엔드 pytest: 56+ 통과 (단위 + 통합 + cascade + rate-limit + 감사 로그)
- 프론트 tsc: exit 0
- E2E QA 스크립트:
    - `scripts/qa_smoke.sh` — 백엔드 28 시나리오 (curl)
    - `scripts/qa_web.py` — Playwright happy path
    - `scripts/qa_web_visual.py` — 시각 검증 17 시나리오
    - `scripts/qa_responsive.py` — 5 viewport 매트릭스 (320 / 414 / 768 / 1280 / 1920)

## 📄 주요 문서
- [`document/PRD.md`](document/PRD.md) — 제품 요구사항 v1.0
- [`document/release_checklist.md`](document/release_checklist.md) — 출시 전 잔여 작업
- [`document/operations/qa_report_2026_05_19.md`](document/operations/qa_report_2026_05_19.md) — QA 결과
- [`document/operations/app_store_metadata.md`](document/operations/app_store_metadata.md) — 스토어 카피·심사 대응
- [`document/operations/email_gmail_setup.md`](document/operations/email_gmail_setup.md) — Gmail SMTP 셋업
- [`document/legal/`](document/legal/) — 개인정보처리방침·이용약관 초안 (변호사 검토 전)
- [`CHANGELOG.md`](CHANGELOG.md) — 상세 변경 이력