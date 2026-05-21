# InRem v1.0 완성 작업 — 설계 문서

> 작성: 2026-05-21  
> 대상 작업: (1) PRD Epic E1 온보딩, (2) API base URL 환경변수화, (3) Firebase graceful degradation

---

## 1. PRD Epic E1 — 온보딩 화면

### 1.1 전체 흐름

```
회원가입/로그인 성공
    └── GET /auth/me → onboarding_completed_at == null?
            YES → <OnboardingFlow />  (Step 1 → 2 → 3 → 완료)
            NO  → <AuthenticatedApp /> (기존 MainTabs)
```

재로그인 시 `onboarding_completed_at` 이 non-null 이면 온보딩 진입 없음.

### 1.2 내비게이션 패턴

`App.tsx`의 `AppContent` 컴포넌트에 세 번째 분기 추가:

```tsx
// 현재:
isAuthenticated → AuthenticatedApp | UnauthenticatedApp

// 변경 후:
isAuthenticated + !onboardingCompleted → OnboardingFlow
isAuthenticated + onboardingCompleted  → AuthenticatedApp
!isAuthenticated                       → UnauthenticatedApp
```

`AuthContext.User` 타입에 `onboarding_completed_at: string | null` 추가.  
`AuthContext`가 `isOnboardingCompleted` 파생 boolean을 제공.

### 1.3 온보딩 3단계 컴포넌트 구조

위치: `front/src/features/onboarding/`

```
onboarding/
├── components/
│   ├── OnboardingFlow.tsx       ← 단계 상태 관리, 스텝 라우터
│   ├── StepValueIntro.tsx       ← Step 1: 핵심 가치 소개
│   ├── StepGuardianIntro.tsx    ← Step 2: 보호자 초대 안내
│   └── StepFirstPulse.tsx       ← Step 3: 민감도 선택 + 첫 안부 시연
└── hooks/
    └── useOnboarding.ts         ← 완료 API 호출, 단계 전진 로직
```

#### Step 1 — 가치 소개
- "Quiet Watch" 아이콘 (텍스트 이모지·SVG 아이콘 fallback)
- 헤드라인: "InRem이 하는 일" (heading2)
- Pulse 한 줄: "매일 앱을 열기만 하면 안부 신호가 자동으로 전달돼요."
- Heritage 한 줄: "소중한 디지털 자산을 미리 정리해 두세요."
- "다음" 버튼, "건너뛰기" 텍스트 버튼

#### Step 2 — 보호자 초대 안내
- "보호자 코드 발급" 흐름 설명 (정적 안내 — 실제 코드 발급은 설정에서)
- "나중에 설정 > 보호자에서도 할 수 있어요." 캡션
- "다음" 버튼, "건너뛰기"

#### Step 3 — 첫 안부 + 민감도 선택
- 민감도 3가지 라디오 버튼: 느슨함(24h) / 보통(12h) / 엄격함(6h)
- 선택 시 `PATCH /settings/policy` (기존 API) 호출
- "InRem이 지금 첫 안부를 기록할게요." 안내 후 "시작하기" 버튼
- 건너뛰기 시 민감도 변경 없이 바로 완료

### 1.4 진행 인디케이터
- 상단 `•••` 3-dot 진행 표시 (active dot = `colors.primary`, inactive = `colors.border`)
- `OnboardingFlow` 내부 상태 `currentStep: 1 | 2 | 3`

### 1.5 완료 처리
- Step 3 "시작하기" 또는 어느 단계에서든 "건너뛰기" 탭 시:
  - `PATCH /auth/me/onboarding` 호출 → `onboarding_completed_at` 기록
  - AuthContext의 user를 갱신 → `isOnboardingCompleted = true`
  - `AppContent` 자동으로 `<AuthenticatedApp />`으로 전환

### 1.6 반응형
- `OnboardingFlow`는 `ResponsiveShell` 안에서 동작 (이미 `App.tsx` 레벨에서 감쌈)
- 별도 responsive 처리 불필요

---

## 2. 백엔드 — 온보딩 DB + API

### 2.1 DB 마이그레이션

`users` 테이블에 컬럼 추가:
```sql
ALTER TABLE users ADD COLUMN onboarding_completed_at TIMESTAMP NULL DEFAULT NULL;
```

Alembic 마이그레이션 파일: `back/alembic/versions/<hash>_add_onboarding_completed_at.py`

`User` 모델에 컬럼 추가:
```python
onboarding_completed_at = Column(DateTime, nullable=True, default=None)
```

### 2.2 API 변경

#### `GET /auth/me` — UserResponse에 필드 추가
```python
class UserResponse(BaseModel):
    id: UUID
    email: str
    is_active: bool
    onboarding_completed_at: datetime | None  # ← 추가
```

#### `PATCH /auth/me/onboarding` — 새 엔드포인트
```
PATCH /api/v1/auth/me/onboarding
Authorization: Bearer <token>

Response 200: { "onboarding_completed_at": "2026-05-21T..." }
```

- 이미 완료된 경우에도 idempotent (200 반환, 기존 timestamp 유지)
- 로직: `user.onboarding_completed_at = user.onboarding_completed_at or datetime.utcnow()`

---

## 3. API Base URL 환경변수화

### 3.1 `front/src/api/client.ts` 변경

```typescript
// 변경 전
const API_BASE_URL = 'http://localhost:8000/api/v1';

// 변경 후
const API_BASE_URL =
    process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';
```

`performRefresh()` 내부의 하드코딩도 같이 제거 (`API_BASE_URL` 상수를 이미 참조).

### 3.2 `front/.env.example` 신규 파일

```env
# API 서버 주소. 미설정 시 개발 기본값(localhost:8000) 사용.
# Expo 빌드에서 클라이언트 코드에 노출되는 env는 EXPO_PUBLIC_ prefix 필수.
# (참고: https://docs.expo.dev/guides/environment-variables/)
EXPO_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 4. Firebase Graceful Degradation

### 4.1 Provider 인터페이스 (email_service.py 패턴 mirror)

```python
class NotificationProvider(Protocol):
    async def send_push(self, token: str, title: str, body: str,
                        data: dict[str, str] | None = None) -> bool: ...
    async def send_multicast(self, tokens: list[str], title: str, body: str,
                             data: dict[str, str] | None = None) -> dict[str, Any]: ...

class NoopNotificationProvider:
    """Logs but does not send. Used when Firebase is not configured."""
    async def send_push(self, ...) -> bool:
        logger.warning("[FCM] Noop provider — not sending push")
        return False
    async def send_multicast(self, ...) -> dict:
        logger.warning("[FCM] Noop provider — not sending multicast")
        return {"success_count": 0, "failure_count": len(tokens), "failed_tokens": tokens}

class FCMNotificationProvider:
    """Firebase Cloud Messaging provider. firebase_admin import is deferred
    inside this class to avoid import-time failure."""
    def __init__(self, credentials_path: str): ...
    async def send_push(self, ...) -> bool: ...
    async def send_multicast(self, ...) -> dict: ...
```

### 4.2 팩토리 함수

```python
class NotificationConfigError(RuntimeError):
    """Raised at startup in production when Firebase credentials are missing."""

def _build_default_provider() -> NotificationProvider:
    path = settings.FIREBASE_CREDENTIALS_PATH
    if path:
        return FCMNotificationProvider(credentials_path=path)
    if settings.ENV == "production":
        raise NotificationConfigError(
            "FIREBASE_CREDENTIALS_PATH must be set in production"
        )
    logger.warning("[FCM] No credentials — using NoopNotificationProvider")
    return NoopNotificationProvider()

# 모듈 싱글톤 (lifespan에서 initialize_notification_provider() 호출)
_provider: NotificationProvider | None = None

def initialize_notification_provider() -> None:
    global _provider
    _provider = _build_default_provider()

def get_provider() -> NotificationProvider:
    if _provider is None:
        raise RuntimeError("Notification provider not initialized")
    return _provider
```

### 4.3 기존 함수들 provider 경유로 리팩터

`send_push_notification`, `send_multicast_notification` 등 기존 public 함수를  
`get_provider().send_push(...)` / `get_provider().send_multicast(...)` 위임으로 교체.  
호출부(`pulse_engine.py`)는 변경 없음 (함수 시그니처 유지).

### 4.4 `main.py` lifespan 변경

```python
from app.services import notification_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    notification_service.initialize_notification_provider()  # fail-fast in prod
    await start_scheduler()
    yield
    await stop_scheduler()
```

---

## 5. 테스트 계획

### 백엔드 신규 테스트
- `test_onboarding.py`: PATCH /auth/me/onboarding 성공, 멱등성, 미인증 401
- `test_notification_provider.py`: NoopProvider 반환 (credentials 없음), NotificationConfigError (ENV=production), FCMProvider 생성 (경로 있을 때)

### 프론트엔드
- `npx tsc --noEmit` exit 0

### QA
- `qa_web.py`: 온보딩 진입 시나리오 추가 (신규 가입 후 온보딩 화면 노출, 건너뛰기 후 홈 진입)
- `qa_responsive.py`: 5/5 회귀 통과

---

## 6. 검증 기준 (Definition of Done)

1. `cd back && poetry run pytest tests/` 모두 그린 (신규 테스트 포함)
2. `cd front && npx tsc --noEmit` exit 0
3. `bash scripts/qa_smoke.sh` 28/28 (있는 경우)
4. `python3 scripts/qa_web.py` 통과 + 온보딩 시나리오 포함
5. `python3 scripts/qa_responsive.py` 5/5
6. `git push origin main` 완료
