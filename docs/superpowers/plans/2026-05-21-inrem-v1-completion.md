# InRem v1.0 Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 세 가지 묶음 — (1) PRD Epic E1 온보딩 3단계 화면, (2) API base URL 환경변수화, (3) Firebase graceful degradation — 을 구현해 일반 사용자가 실제로 사용할 수 있는 상태로 만든다.

**Architecture:** 온보딩은 `App.tsx` `AppContent`에 세 번째 분기를 추가해 `isAuthenticated + !onboardingCompleted` 상태를 처리한다. Firebase는 email_service.py의 Provider 패턴을 mirror한다. API URL은 `EXPO_PUBLIC_API_URL` 환경변수로 추출한다.

**Tech Stack:** React Native + TypeScript (frontend), FastAPI + SQLAlchemy + Alembic (backend), firebase-admin 7.x, pytest-asyncio

---

## File Map

### 신규 생성
- `front/src/features/onboarding/components/OnboardingFlow.tsx` — 단계 라우터
- `front/src/features/onboarding/components/StepValueIntro.tsx` — Step 1
- `front/src/features/onboarding/components/StepGuardianIntro.tsx` — Step 2
- `front/src/features/onboarding/components/StepFirstPulse.tsx` — Step 3
- `front/src/features/onboarding/hooks/useOnboarding.ts` — 완료 로직
- `front/.env.example` — 환경변수 예시
- `back/alembic/versions/b5c6d7e8f9a0_add_onboarding_completed_at.py` — DB 마이그레이션
- `back/tests/test_onboarding.py` — 온보딩 엔드포인트 테스트
- `back/tests/test_notification_provider.py` — Firebase provider 테스트

### 수정
- `front/src/api/client.ts:5,85` — API_BASE_URL 환경변수화
- `front/src/context/AuthContext.tsx` — User 타입 + completeOnboarding
- `front/App.tsx` — AppContent 세 번째 분기
- `back/app/models/user.py` — onboarding_completed_at 컬럼
- `back/app/schemas/auth.py` — UserResponse + OnboardingResponse
- `back/app/api/v1/auth.py` — PATCH /auth/me/onboarding 엔드포인트
- `back/app/services/notification_service.py` — Provider 패턴으로 전면 리팩터
- `back/app/main.py` — lifespan에 initialize_notification_provider 추가
- `scripts/qa_web.py` — 온보딩 시나리오 추가

---

## Task 1: API base URL 환경변수화

**Files:**
- Modify: `front/src/api/client.ts:5,85`
- Create: `front/.env.example`

- [ ] **Step 1: client.ts API_BASE_URL 수정**

`front/src/api/client.ts`의 5번째 줄을 교체:

```typescript
// 변경 전
const API_BASE_URL = 'http://localhost:8000/api/v1';

// 변경 후 (5번째 줄)
const API_BASE_URL =
    (process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1');
```

85번째 줄 `performRefresh` 내부의 하드코딩도 확인: 이미 `${API_BASE_URL}` 상수를 참조하고 있으므로 별도 변경 불필요.

- [ ] **Step 2: .env.example 생성**

`front/.env.example` 파일 생성:

```env
# API 서버 주소. 미설정 시 개발 기본값(localhost:8000)이 사용됩니다.
# Expo 빌드에서 클라이언트 코드에 노출되는 환경변수는 EXPO_PUBLIC_ prefix 필수.
# 참고: https://docs.expo.dev/guides/environment-variables/
EXPO_PUBLIC_API_URL=http://localhost:8000/api/v1
```

- [ ] **Step 3: TypeScript 확인**

```bash
cd front && npx tsc --noEmit
```

Expected: exit 0 (에러 없음)

- [ ] **Step 4: Commit**

```bash
cd /Users/ig/Desktop/project/InRem
git add front/src/api/client.ts front/.env.example
git commit -m "feat(config): EXPO_PUBLIC_API_URL env var for API base URL"
```

---

## Task 2: Firebase Graceful Degradation — Provider 패턴

**Files:**
- Modify: `back/app/services/notification_service.py` (전면 재작성)
- Test: `back/tests/test_notification_provider.py`

- [ ] **Step 1: 테스트 작성**

`back/tests/test_notification_provider.py` 생성:

```python
"""Tests for NotificationProvider factory and provider behavior."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.services.notification_service import (
    NoopNotificationProvider,
    NotificationConfigError,
    _build_default_provider,
)


def test_noop_provider_returned_when_no_credentials():
    """No FIREBASE_CREDENTIALS_PATH + dev env → NoopNotificationProvider."""
    with patch("app.services.notification_service.settings") as mock_settings:
        mock_settings.FIREBASE_CREDENTIALS_PATH = None
        mock_settings.ENV = "development"
        provider = _build_default_provider()
    assert isinstance(provider, NoopNotificationProvider)


def test_production_without_credentials_raises():
    """No credentials + ENV=production → NotificationConfigError at startup."""
    with patch("app.services.notification_service.settings") as mock_settings:
        mock_settings.FIREBASE_CREDENTIALS_PATH = None
        mock_settings.ENV = "production"
        with pytest.raises(NotificationConfigError):
            _build_default_provider()


@pytest.mark.asyncio
async def test_noop_send_push_returns_false():
    provider = NoopNotificationProvider()
    result = await provider.send_push("token", "title", "body")
    assert result is False


@pytest.mark.asyncio
async def test_noop_send_multicast_returns_zero_success():
    provider = NoopNotificationProvider()
    result = await provider.send_multicast(["t1", "t2"], "title", "body")
    assert result["success_count"] == 0
    assert result["failure_count"] == 2
    assert set(result["failed_tokens"]) == {"t1", "t2"}
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

```bash
cd back && poetry run pytest tests/test_notification_provider.py -v
```

Expected: ImportError 또는 AttributeError (아직 구현 안 됨)

- [ ] **Step 3: notification_service.py 전면 재작성**

`back/app/services/notification_service.py` 를 아래 내용으로 교체:

```python
"""Push notification service — provider pattern.

현재 사용 중인 프로바이더:
- FCMNotificationProvider — FIREBASE_CREDENTIALS_PATH 설정 시 자동 활성화.
- NoopNotificationProvider — credentials 없으면 폴백. 로그에만 기록.

프로덕션 전환: FIREBASE_CREDENTIALS_PATH 를 service account JSON 경로로 설정.
ENV=production + credentials 미설정 시 NotificationConfigError raise (fail-fast).
"""

import logging
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)


# ── Provider Protocol ────────────────────────────────────────────────────────

@runtime_checkable
class NotificationProvider(Protocol):
    async def send_push(
        self,
        token: str,
        title: str,
        body: str,
        data: dict[str, str] | None = None,
    ) -> bool: ...

    async def send_multicast(
        self,
        tokens: list[str],
        title: str,
        body: str,
        data: dict[str, str] | None = None,
    ) -> dict[str, Any]: ...


# ── Providers ────────────────────────────────────────────────────────────────

class NoopNotificationProvider:
    """Logs but never sends. Used when Firebase is not configured."""

    async def send_push(
        self,
        token: str,
        title: str,
        body: str,
        data: dict[str, str] | None = None,
    ) -> bool:
        logger.warning("[FCM] NoopProvider — push skipped (no credentials)")
        return False

    async def send_multicast(
        self,
        tokens: list[str],
        title: str,
        body: str,
        data: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        logger.warning("[FCM] NoopProvider — multicast skipped (no credentials)")
        return {
            "success_count": 0,
            "failure_count": len(tokens),
            "failed_tokens": tokens,
        }


class FCMNotificationProvider:
    """Firebase Cloud Messaging provider.

    firebase_admin import is deferred to __init__ so that a missing or
    misconfigured package does NOT crash the whole module at import time.
    """

    def __init__(self, credentials_path: str) -> None:
        import firebase_admin  # deferred import
        from firebase_admin import credentials as fb_creds

        self._credentials_path = credentials_path

        try:
            firebase_admin.get_app()
            logger.info("[FCM] Reusing existing Firebase app")
        except ValueError:
            cred = fb_creds.Certificate(credentials_path)
            firebase_admin.initialize_app(cred)
            logger.info("[FCM] Firebase initialized with credentials file")

    async def send_push(
        self,
        token: str,
        title: str,
        body: str,
        data: dict[str, str] | None = None,
    ) -> bool:
        from firebase_admin import messaging

        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                token=token,
            )
            response = messaging.send(message)
            logger.info(f"[FCM] Notification sent: {response}")
            return True
        except messaging.UnregisteredError:
            logger.warning(f"[FCM] Token unregistered: {token[:20]}...")
            return False
        except messaging.SenderIdMismatchError:
            logger.error(f"[FCM] Sender ID mismatch: {token[:20]}...")
            return False
        except Exception as e:
            logger.error(f"[FCM] Failed to send push: {e}")
            return False

    async def send_multicast(
        self,
        tokens: list[str],
        title: str,
        body: str,
        data: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        from firebase_admin import messaging

        if not tokens:
            return {"success_count": 0, "failure_count": 0, "failed_tokens": []}

        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                tokens=tokens,
            )
            response = messaging.send_each_for_multicast(message)
            failed = [tokens[i] for i, r in enumerate(response.responses) if not r.success]
            logger.info(
                f"[FCM] Multicast: {response.success_count} ok, {response.failure_count} fail"
            )
            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "failed_tokens": failed,
            }
        except Exception as e:
            logger.error(f"[FCM] Failed to send multicast: {e}")
            return {"success_count": 0, "failure_count": len(tokens), "failed_tokens": tokens}


# ── Factory & singleton ──────────────────────────────────────────────────────

class NotificationConfigError(RuntimeError):
    """Raised at startup when Firebase credentials are missing in production."""


def _build_default_provider() -> NotificationProvider:
    path = settings.FIREBASE_CREDENTIALS_PATH
    if path:
        return FCMNotificationProvider(credentials_path=path)
    if settings.ENV == "production":
        raise NotificationConfigError(
            "FIREBASE_CREDENTIALS_PATH must be set in production (ENV=production)"
        )
    logger.warning("[FCM] No credentials — using NoopNotificationProvider")
    return NoopNotificationProvider()


_provider: NotificationProvider | None = None


def initialize_notification_provider() -> None:
    """Call once at app startup (in lifespan). Raises NotificationConfigError in prod."""
    global _provider
    _provider = _build_default_provider()


def get_provider() -> NotificationProvider:
    global _provider
    if _provider is None:
        # Lazy init for dev/test — explicit call in lifespan guarantees prod behavior.
        _provider = _build_default_provider()
    return _provider


# ── Public API (signatures unchanged — callers don't need to change) ─────────

async def send_push_notification(
    token: str,
    title: str,
    body: str,
    data: dict[str, str] | None = None,
) -> bool:
    return await get_provider().send_push(token, title, body, data)


async def send_multicast_notification(
    tokens: list[str],
    title: str,
    body: str,
    data: dict[str, str] | None = None,
) -> dict[str, Any]:
    return await get_provider().send_multicast(tokens, title, body, data)


async def update_fcm_token(
    db: AsyncSession,
    user_id: UUID,
    fcm_token: str | None,
) -> None:
    await db.execute(
        update(User).where(User.id == user_id).values(fcm_token=fcm_token)
    )
    await db.commit()


async def clear_invalid_token(db: AsyncSession, user_id: UUID) -> None:
    await update_fcm_token(db, user_id, None)
    logger.info(f"[FCM] Cleared invalid token for user {user_id}")


async def send_soft_checkin_notification(user: User, event_id: UUID) -> bool:
    if not user.fcm_token:
        logger.warning(f"[FCM] User {user.id} has no FCM token")
        return False

    return await send_push_notification(
        token=user.fcm_token,
        title="잘 지내시나요?",
        body="오랫동안 활동이 없어 안부 확인차 연락드렸어요. 괜찮으시다면 앱을 열어주세요.",
        data={
            "type": "SOFT_CHECKIN",
            "event_id": str(event_id),
            "user_id": str(user.id),
        },
    )


async def send_guardian_notification(
    ward: User,
    guardians: list[User],
    event_id: UUID,
) -> int:
    if not guardians:
        return 0

    tokens = [g.fcm_token for g in guardians if g.fcm_token]
    if not tokens:
        logger.warning(f"[FCM] No valid tokens for guardians of user {ward.id}")
        return 0

    result = await send_multicast_notification(
        tokens=tokens,
        title="긴급: 활동 미감지",
        body=f"{ward.email}님이 오랫동안 활동이 없습니다. 확인이 필요합니다.",
        data={
            "type": "GUARDIAN_ALERT",
            "event_id": str(event_id),
            "ward_id": str(ward.id),
            "severity": "HIGH",
        },
    )

    if result["failure_count"] > 0:
        from app.services.email_service import send_guardian_email_alert

        failed_tokens_set = set(result["failed_tokens"])
        for g in guardians:
            should_email = (not g.fcm_token) or (g.fcm_token in failed_tokens_set)
            if should_email and g.email:
                try:
                    await send_guardian_email_alert(g.email, ward.email, event_id)
                    logger.info(f"[Email] Fallback email sent to {g.email}")
                except Exception as e:
                    logger.error(f"[Email] Fallback failed for {g.email}: {e}")

    return result["success_count"]
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd back && poetry run pytest tests/test_notification_provider.py -v
```

Expected:
```
PASSED tests/test_notification_provider.py::test_noop_provider_returned_when_no_credentials
PASSED tests/test_notification_provider.py::test_production_without_credentials_raises
PASSED tests/test_notification_provider.py::test_noop_send_push_returns_false
PASSED tests/test_notification_provider.py::test_noop_send_multicast_returns_zero_success
```

- [ ] **Step 5: main.py lifespan 수정**

`back/app/main.py`에서 import 추가 및 lifespan 수정:

```python
# 파일 상단 imports (기존 import 아래에 추가)
from app.services import notification_service

# lifespan 함수 수정
@asynccontextmanager
async def lifespan(app: FastAPI):
    notification_service.initialize_notification_provider()  # fail-fast in prod
    await start_scheduler()
    yield
    await stop_scheduler()
```

- [ ] **Step 6: 전체 백엔드 테스트 통과 확인**

```bash
cd back && poetry run pytest tests/ -v
```

Expected: 기존 테스트 전부 그린 + 신규 4개 통과

- [ ] **Step 7: Commit**

```bash
cd /Users/ig/Desktop/project/InRem
git add back/app/services/notification_service.py back/app/main.py back/tests/test_notification_provider.py
git commit -m "feat(firebase): provider pattern — NoopProvider fallback + prod fail-fast"
```

---

## Task 3: 온보딩 DB 컬럼 + Alembic 마이그레이션

**Files:**
- Modify: `back/app/models/user.py`
- Create: `back/alembic/versions/b5c6d7e8f9a0_add_onboarding_completed_at.py`

- [ ] **Step 1: User 모델에 컬럼 추가**

`back/app/models/user.py`에서 `deletion_requested_at` 컬럼 아래에 추가:

```python
    # 온보딩 완료 시각. NULL 이면 신규 사용자 → 앱이 온보딩 화면으로 라우팅.
    onboarding_completed_at = Column(DateTime, nullable=True, default=None)
```

- [ ] **Step 2: Alembic 마이그레이션 파일 생성**

`back/alembic/versions/b5c6d7e8f9a0_add_onboarding_completed_at.py` 생성:

```python
"""Add onboarding_completed_at to users

Revision ID: b5c6d7e8f9a0
Revises: f4b1c2a3d8e7
Create Date: 2026-05-21 00:00:00.000000

신규 사용자 온보딩 완료 시각을 기록. NULL = 온보딩 미완료.
재로그인 시 NULL 이 아니면 온보딩 건너뜀.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b5c6d7e8f9a0"
down_revision: Union[str, None] = "f4b1c2a3d8e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("onboarding_completed_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "onboarding_completed_at")
```

- [ ] **Step 3: 백엔드 테스트 통과 확인 (모델 변경 후 기존 테스트 회귀 없음)**

```bash
cd back && poetry run pytest tests/ -v
```

Expected: 모든 테스트 그린 (User 모델에 nullable 컬럼 추가는 기존 test fixture와 호환됨)

- [ ] **Step 4: Commit**

```bash
cd /Users/ig/Desktop/project/InRem
git add back/app/models/user.py back/alembic/versions/b5c6d7e8f9a0_add_onboarding_completed_at.py
git commit -m "feat(db): add onboarding_completed_at column + alembic migration"
```

---

## Task 4: 온보딩 API 엔드포인트 + 스키마

**Files:**
- Modify: `back/app/schemas/auth.py`
- Modify: `back/app/api/v1/auth.py`
- Test: `back/tests/test_onboarding.py`

- [ ] **Step 1: 테스트 작성**

`back/tests/test_onboarding.py` 생성:

```python
"""Tests for PATCH /api/v1/auth/me/onboarding."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.models.user import User


@pytest.fixture
def mock_user_no_onboarding():
    return User(
        id=uuid4(),
        email="newuser@inrem.test",
        is_active=True,
        onboarding_completed_at=None,
    )


@pytest.fixture
def mock_user_onboarded():
    ts = datetime(2026, 5, 20, 10, 0, 0)
    return User(
        id=uuid4(),
        email="existing@inrem.test",
        is_active=True,
        onboarding_completed_at=ts,
    )


@pytest.fixture
def override_no_onboarding(mock_user_no_onboarding):
    db_mock = AsyncMock()
    app.dependency_overrides[get_current_user] = lambda: mock_user_no_onboarding
    app.dependency_overrides[get_db] = lambda: db_mock
    yield db_mock
    app.dependency_overrides = {}


@pytest.fixture
def override_onboarded(mock_user_onboarded):
    db_mock = AsyncMock()
    app.dependency_overrides[get_current_user] = lambda: mock_user_onboarded
    app.dependency_overrides[get_db] = lambda: db_mock
    yield db_mock
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_complete_onboarding_sets_timestamp(async_client, override_no_onboarding, mock_user_no_onboarding):
    """First call: sets onboarding_completed_at and returns it."""
    resp = await async_client.patch(
        "/api/v1/auth/me/onboarding",
        headers={"Authorization": "Bearer test"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "onboarding_completed_at" in body
    assert body["onboarding_completed_at"] is not None
    # User object was mutated
    assert mock_user_no_onboarding.onboarding_completed_at is not None


@pytest.mark.asyncio
async def test_complete_onboarding_idempotent(async_client, override_onboarded, mock_user_onboarded):
    """Second call: returns existing timestamp unchanged."""
    original_ts = mock_user_onboarded.onboarding_completed_at
    resp = await async_client.patch(
        "/api/v1/auth/me/onboarding",
        headers={"Authorization": "Bearer test"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["onboarding_completed_at"] == original_ts.isoformat()
    # Timestamp not changed
    assert mock_user_onboarded.onboarding_completed_at == original_ts


@pytest.mark.asyncio
async def test_complete_onboarding_requires_auth(async_client):
    """No token → 401."""
    resp = await async_client.patch("/api/v1/auth/me/onboarding")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_includes_onboarding_field(async_client, override_no_onboarding, mock_user_no_onboarding):
    """GET /auth/me must include onboarding_completed_at."""
    resp = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer test"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "onboarding_completed_at" in body
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd back && poetry run pytest tests/test_onboarding.py -v
```

Expected: FAILED (onboarding_completed_at 필드 없음)

- [ ] **Step 3: UserResponse 스키마 + OnboardingResponse 추가**

`back/app/schemas/auth.py` 수정:

```python
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    user_id: UUID | None = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    is_active: bool
    onboarding_completed_at: datetime | None = None  # ← 추가

    model_config = ConfigDict(from_attributes=True)


class OnboardingResponse(BaseModel):
    onboarding_completed_at: str


class DeletionStatusResponse(BaseModel):
    deletion_requested_at: str | None
    grace_period_days: int
    seconds_remaining: int | None
```

- [ ] **Step 4: PATCH /auth/me/onboarding 엔드포인트 추가**

`back/app/api/v1/auth.py`에서 `router` import 아래에 `datetime` import 추가 후, 파일 끝에 엔드포인트 추가:

파일 상단 imports에 `from datetime import datetime` 추가.

`OnboardingResponse`를 schemas import에 추가:
```python
from app.schemas.auth import (
    DeletionStatusResponse,
    OnboardingResponse,
    RefreshRequest,
    Token,
    UserCreate,
    UserResponse,
)
```

파일 끝에 추가:

```python
@router.patch("/me/onboarding", response_model=OnboardingResponse)
async def complete_onboarding(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark onboarding as completed. Idempotent — safe to call multiple times."""
    if current_user.onboarding_completed_at is None:
        current_user.onboarding_completed_at = datetime.utcnow()
        db.add(current_user)
        await db.commit()
    return OnboardingResponse(
        onboarding_completed_at=current_user.onboarding_completed_at.isoformat()
    )
```

- [ ] **Step 5: 테스트 통과 확인**

```bash
cd back && poetry run pytest tests/test_onboarding.py -v
```

Expected:
```
PASSED tests/test_onboarding.py::test_complete_onboarding_sets_timestamp
PASSED tests/test_onboarding.py::test_complete_onboarding_idempotent
PASSED tests/test_onboarding.py::test_complete_onboarding_requires_auth
PASSED tests/test_onboarding.py::test_get_me_includes_onboarding_field
```

- [ ] **Step 6: 전체 백엔드 테스트**

```bash
cd back && poetry run pytest tests/ -v
```

Expected: 모든 테스트 그린

- [ ] **Step 7: Commit**

```bash
cd /Users/ig/Desktop/project/InRem
git add back/app/schemas/auth.py back/app/api/v1/auth.py back/tests/test_onboarding.py
git commit -m "feat(onboarding): PATCH /auth/me/onboarding endpoint + UserResponse field"
```

---

## Task 5: Frontend AuthContext 업데이트

**Files:**
- Modify: `front/src/context/AuthContext.tsx`

- [ ] **Step 1: AuthContext.tsx 수정**

`front/src/context/AuthContext.tsx` 전체를 아래로 교체:

```tsx
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authApi, tokenStorage, apiClient } from '../api/client';

interface User {
    id: string;
    email: string;
    is_active: boolean;
    onboarding_completed_at: string | null;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    isOnboardingCompleted: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
    completeOnboarding: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const loadToken = async () => {
            try {
                const storedToken = await tokenStorage.getAccess();
                if (storedToken) {
                    setToken(storedToken);
                    const userData = await authApi.getMe();
                    setUser(userData);
                }
            } catch (_error) {
                await tokenStorage.clear();
            } finally {
                setIsLoading(false);
            }
        };
        loadToken();
    }, []);

    const login = async (email: string, password: string) => {
        const response = await authApi.login(email, password);
        await tokenStorage.setBoth(response.access_token, response.refresh_token);
        setToken(response.access_token);
        const userData = await authApi.getMe();
        setUser(userData);
    };

    const register = async (email: string, password: string) => {
        const response = await authApi.register(email, password);
        await tokenStorage.setBoth(response.access_token, response.refresh_token);
        setToken(response.access_token);
        const userData = await authApi.getMe();
        setUser(userData);
    };

    const logout = async () => {
        await tokenStorage.clear();
        setToken(null);
        setUser(null);
    };

    const completeOnboarding = async () => {
        const resp = await apiClient.patch('/auth/me/onboarding');
        setUser(prev =>
            prev ? { ...prev, onboarding_completed_at: resp.data.onboarding_completed_at } : null
        );
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                token,
                isLoading,
                isAuthenticated: !!token && !!user,
                isOnboardingCompleted: !!user?.onboarding_completed_at,
                login,
                register,
                logout,
                completeOnboarding,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
```

- [ ] **Step 2: TypeScript 확인**

```bash
cd front && npx tsc --noEmit
```

Expected: exit 0

- [ ] **Step 3: Commit**

```bash
cd /Users/ig/Desktop/project/InRem
git add front/src/context/AuthContext.tsx
git commit -m "feat(auth): add onboarding_completed_at + completeOnboarding to AuthContext"
```

---

## Task 6: 온보딩 컴포넌트 구현

**Files:**
- Create: `front/src/features/onboarding/hooks/useOnboarding.ts`
- Create: `front/src/features/onboarding/components/OnboardingFlow.tsx`
- Create: `front/src/features/onboarding/components/StepValueIntro.tsx`
- Create: `front/src/features/onboarding/components/StepGuardianIntro.tsx`
- Create: `front/src/features/onboarding/components/StepFirstPulse.tsx`

- [ ] **Step 1: 디렉토리 생성**

```bash
mkdir -p /Users/ig/Desktop/project/InRem/front/src/features/onboarding/components
mkdir -p /Users/ig/Desktop/project/InRem/front/src/features/onboarding/hooks
```

- [ ] **Step 2: useOnboarding.ts 훅 생성**

`front/src/features/onboarding/hooks/useOnboarding.ts` 생성:

```typescript
import { useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { settingsApi, SensitivityLevel } from '../../../api/client';

export const useOnboarding = () => {
    const { completeOnboarding } = useAuth();
    const [isCompleting, setIsCompleting] = useState(false);

    const finishOnboarding = async (sensitivity?: SensitivityLevel) => {
        setIsCompleting(true);
        try {
            if (sensitivity) {
                await settingsApi.updatePolicy({ sensitivity });
            }
            await completeOnboarding();
        } finally {
            setIsCompleting(false);
        }
    };

    return { finishOnboarding, isCompleting };
};
```

- [ ] **Step 3: StepValueIntro.tsx 생성 (Step 1)**

`front/src/features/onboarding/components/StepValueIntro.tsx` 생성:

```tsx
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors } from '../../../theme/colors';
import { typography } from '../../../theme/typography';
import { spacing, radius } from '../../../theme/spacing';

interface Props {
    onNext: () => void;
    onSkipAll: () => void;
}

export const StepValueIntro = ({ onNext, onSkipAll }: Props) => (
    <View style={styles.container}>
        <View style={styles.content}>
            <Text style={styles.icon}>🕰</Text>
            <Text style={[typography.heading2, styles.title]}>InRem이 하는 일</Text>
            <View style={styles.card}>
                <Text style={[typography.body1, styles.cardTitle]}>안부 체크 (Pulse)</Text>
                <Text style={[typography.body2, styles.cardBody]}>
                    매일 앱을 열기만 하면 안부 신호가 자동으로 전달돼요.
                </Text>
            </View>
            <View style={styles.card}>
                <Text style={[typography.body1, styles.cardTitle]}>디지털 유산함 (Heritage)</Text>
                <Text style={[typography.body2, styles.cardBody]}>
                    소중한 디지털 자산을 미리 정리해 안전하게 보관하세요.
                </Text>
            </View>
        </View>
        <View style={styles.actions}>
            <TouchableOpacity style={styles.primaryButton} onPress={onNext}>
                <Text style={[typography.body1, styles.primaryButtonText]}>다음</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.skipButton} onPress={onSkipAll}>
                <Text style={[typography.caption, styles.skipText]}>건너뛰기</Text>
            </TouchableOpacity>
        </View>
    </View>
);

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.background, paddingHorizontal: spacing.lg },
    content: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: spacing.lg },
    icon: { fontSize: 56, textAlign: 'center' },
    title: { color: colors.text.primary, textAlign: 'center' },
    card: {
        width: '100%',
        backgroundColor: colors.card,
        borderRadius: radius.md,
        padding: spacing.md,
        borderWidth: 1,
        borderColor: colors.border,
        gap: spacing.xs,
    },
    cardTitle: { color: colors.primary, fontWeight: '600' },
    cardBody: { color: colors.text.secondary },
    actions: { paddingBottom: spacing.xxl, gap: spacing.sm },
    primaryButton: {
        backgroundColor: colors.primary,
        borderRadius: radius.md,
        paddingVertical: spacing.md,
        alignItems: 'center',
    },
    primaryButtonText: { color: colors.text.inverse },
    skipButton: { alignItems: 'center', paddingVertical: spacing.sm },
    skipText: { color: colors.text.caption },
});
```

- [ ] **Step 4: StepGuardianIntro.tsx 생성 (Step 2)**

`front/src/features/onboarding/components/StepGuardianIntro.tsx` 생성:

```tsx
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors } from '../../../theme/colors';
import { typography } from '../../../theme/typography';
import { spacing, radius } from '../../../theme/spacing';

interface Props {
    onNext: () => void;
    onSkipAll: () => void;
}

export const StepGuardianIntro = ({ onNext, onSkipAll }: Props) => (
    <View style={styles.container}>
        <View style={styles.content}>
            <Text style={styles.icon}>🛡️</Text>
            <Text style={[typography.heading2, styles.title]}>보호자 초대</Text>
            <Text style={[typography.body1, styles.description]}>
                가족이나 신뢰하는 사람에게 보호자 코드를 공유하면, 활동이 감지되지 않을 때 자동으로 알림이 가요.
            </Text>
            <View style={styles.infoBox}>
                <Text style={[typography.caption, styles.infoText]}>
                    💡 지금 바로 하지 않아도 괜찮아요.{'\n'}
                    설정 → 보호자 관리에서 언제든지 추가할 수 있어요.
                </Text>
            </View>
        </View>
        <View style={styles.actions}>
            <TouchableOpacity style={styles.primaryButton} onPress={onNext}>
                <Text style={[typography.body1, styles.primaryButtonText]}>다음</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.skipButton} onPress={onSkipAll}>
                <Text style={[typography.caption, styles.skipText]}>건너뛰기</Text>
            </TouchableOpacity>
        </View>
    </View>
);

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.background, paddingHorizontal: spacing.lg },
    content: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: spacing.lg },
    icon: { fontSize: 56, textAlign: 'center' },
    title: { color: colors.text.primary, textAlign: 'center' },
    description: { color: colors.text.secondary, textAlign: 'center', lineHeight: 28 },
    infoBox: {
        backgroundColor: colors.accent,
        borderRadius: radius.md,
        padding: spacing.md,
        width: '100%',
    },
    infoText: { color: colors.text.secondary, lineHeight: 20 },
    actions: { paddingBottom: spacing.xxl, gap: spacing.sm },
    primaryButton: {
        backgroundColor: colors.primary,
        borderRadius: radius.md,
        paddingVertical: spacing.md,
        alignItems: 'center',
    },
    primaryButtonText: { color: colors.text.inverse },
    skipButton: { alignItems: 'center', paddingVertical: spacing.sm },
    skipText: { color: colors.text.caption },
});
```

- [ ] **Step 5: StepFirstPulse.tsx 생성 (Step 3)**

`front/src/features/onboarding/components/StepFirstPulse.tsx` 생성:

```tsx
import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { colors } from '../../../theme/colors';
import { typography } from '../../../theme/typography';
import { spacing, radius } from '../../../theme/spacing';
import { SensitivityLevel } from '../../../api/client';
import { useOnboarding } from '../hooks/useOnboarding';

const SENSITIVITY_OPTIONS: { value: SensitivityLevel; label: string; description: string }[] = [
    { value: 'relaxed', label: '느슨함', description: '24시간 무활동 시 안부 확인' },
    { value: 'normal', label: '보통', description: '12시간 무활동 시 안부 확인' },
    { value: 'strict', label: '엄격함', description: '6시간 무활동 시 안부 확인' },
];

interface Props {
    onSkipAll: () => void;
}

export const StepFirstPulse = ({ onSkipAll }: Props) => {
    const [selected, setSelected] = useState<SensitivityLevel>('normal');
    const { finishOnboarding, isCompleting } = useOnboarding();

    return (
        <View style={styles.container}>
            <View style={styles.content}>
                <Text style={styles.icon}>💚</Text>
                <Text style={[typography.heading2, styles.title]}>안부 민감도 설정</Text>
                <Text style={[typography.body2, styles.subtitle]}>
                    얼마나 자주 안부를 확인할까요? 나중에 설정에서 바꿀 수 있어요.
                </Text>
                <View style={styles.optionsList}>
                    {SENSITIVITY_OPTIONS.map(opt => (
                        <TouchableOpacity
                            key={opt.value}
                            style={[styles.option, selected === opt.value && styles.optionSelected]}
                            onPress={() => setSelected(opt.value)}
                        >
                            <View style={[styles.radio, selected === opt.value && styles.radioSelected]} />
                            <View style={styles.optionText}>
                                <Text style={[typography.body1, styles.optionLabel]}>{opt.label}</Text>
                                <Text style={[typography.caption, styles.optionDesc]}>{opt.description}</Text>
                            </View>
                        </TouchableOpacity>
                    ))}
                </View>
            </View>
            <View style={styles.actions}>
                <TouchableOpacity
                    style={[styles.primaryButton, isCompleting && styles.disabled]}
                    onPress={() => finishOnboarding(selected)}
                    disabled={isCompleting}
                >
                    {isCompleting ? (
                        <ActivityIndicator color={colors.text.inverse} />
                    ) : (
                        <Text style={[typography.body1, styles.primaryButtonText]}>시작하기</Text>
                    )}
                </TouchableOpacity>
                <TouchableOpacity style={styles.skipButton} onPress={onSkipAll} disabled={isCompleting}>
                    <Text style={[typography.caption, styles.skipText]}>건너뛰기</Text>
                </TouchableOpacity>
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.background, paddingHorizontal: spacing.lg },
    content: { flex: 1, justifyContent: 'center', gap: spacing.lg },
    icon: { fontSize: 56, textAlign: 'center' },
    title: { color: colors.text.primary, textAlign: 'center' },
    subtitle: { color: colors.text.secondary, textAlign: 'center' },
    optionsList: { gap: spacing.sm },
    option: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: colors.card,
        borderRadius: radius.md,
        padding: spacing.md,
        borderWidth: 1,
        borderColor: colors.border,
        gap: spacing.md,
    },
    optionSelected: { borderColor: colors.primary, backgroundColor: '#F0F4FF' },
    radio: {
        width: 20,
        height: 20,
        borderRadius: 10,
        borderWidth: 2,
        borderColor: colors.border,
    },
    radioSelected: { borderColor: colors.primary, backgroundColor: colors.primary },
    optionText: { flex: 1 },
    optionLabel: { color: colors.text.primary },
    optionDesc: { color: colors.text.caption },
    actions: { paddingBottom: spacing.xxl, gap: spacing.sm },
    primaryButton: {
        backgroundColor: colors.primary,
        borderRadius: radius.md,
        paddingVertical: spacing.md,
        alignItems: 'center',
    },
    disabled: { opacity: 0.6 },
    primaryButtonText: { color: colors.text.inverse },
    skipButton: { alignItems: 'center', paddingVertical: spacing.sm },
    skipText: { color: colors.text.caption },
});
```

- [ ] **Step 6: OnboardingFlow.tsx 생성 (단계 라우터)**

`front/src/features/onboarding/components/OnboardingFlow.tsx` 생성:

```tsx
import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { colors } from '../../../theme/colors';
import { spacing } from '../../../theme/spacing';
import { StepValueIntro } from './StepValueIntro';
import { StepGuardianIntro } from './StepGuardianIntro';
import { StepFirstPulse } from './StepFirstPulse';
import { useOnboarding } from '../hooks/useOnboarding';

type Step = 1 | 2 | 3;

const TOTAL_STEPS = 3;

const ProgressDots = ({ current }: { current: Step }) => (
    <View style={dotStyles.row}>
        {([1, 2, 3] as Step[]).map(n => (
            <View key={n} style={[dotStyles.dot, current === n && dotStyles.active]} />
        ))}
    </View>
);

const dotStyles = StyleSheet.create({
    row: { flexDirection: 'row', justifyContent: 'center', gap: 8, paddingTop: spacing.lg },
    dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.border },
    active: { backgroundColor: colors.primary },
});

export const OnboardingFlow = () => {
    const [step, setStep] = useState<Step>(1);
    const { finishOnboarding } = useOnboarding();

    const goNext = () => {
        if (step < TOTAL_STEPS) setStep((s) => (s + 1) as Step);
    };

    const skipAll = () => finishOnboarding();

    return (
        <View style={styles.container}>
            <ProgressDots current={step} />
            <View style={styles.stepContainer}>
                {step === 1 && <StepValueIntro onNext={goNext} onSkipAll={skipAll} />}
                {step === 2 && <StepGuardianIntro onNext={goNext} onSkipAll={skipAll} />}
                {step === 3 && <StepFirstPulse onSkipAll={skipAll} />}
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.background },
    stepContainer: { flex: 1 },
});
```

- [ ] **Step 7: TypeScript 확인**

```bash
cd front && npx tsc --noEmit
```

Expected: exit 0

- [ ] **Step 8: Commit**

```bash
cd /Users/ig/Desktop/project/InRem
git add front/src/features/onboarding/
git commit -m "feat(onboarding): 3-step onboarding flow components"
```

---

## Task 7: App.tsx 통합 + QA 시나리오 추가

**Files:**
- Modify: `front/App.tsx`
- Modify: `scripts/qa_web.py`

- [ ] **Step 1: App.tsx AppContent에 온보딩 분기 추가**

`front/App.tsx`에서 `AppContent` 컴포넌트 수정. import 상단에 추가:

```tsx
import { OnboardingFlow } from './src/features/onboarding/components/OnboardingFlow';
```

`AppContent` 함수 수정:

```tsx
const AppContent = () => {
  const { isLoading, isAuthenticated, isOnboardingCompleted } = useAuth();

  if (isLoading) {
    return (
      <ScreenLayout>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={[typography.body1, { color: colors.text.secondary, marginTop: 16 }]}>
            로딩 중...
          </Text>
        </View>
      </ScreenLayout>
    );
  }

  if (isAuthenticated && !isOnboardingCompleted) {
    return <OnboardingFlow />;
  }

  if (isAuthenticated) {
    return <AuthenticatedApp />;
  }

  return <UnauthenticatedApp />;
};
```

- [ ] **Step 2: TypeScript 확인**

```bash
cd front && npx tsc --noEmit
```

Expected: exit 0

- [ ] **Step 3: qa_web.py에 온보딩 시나리오 추가**

`scripts/qa_web.py`에서 시나리오 목록(주석의 `6)` 다음)에 온보딩 시나리오를 추가한다.

`qa_web.py` 파일에서 기존 시나리오 함수들 아래, `async def main()` 직전에 새 함수 추가:

```python
async def scenario_onboarding_new_user(page, result: Result) -> None:
    """신규 가입 후 온보딩 화면 진입 + 건너뛰기로 홈 도달."""
    import time, random, string
    email = f"qa_onboard_{''.join(random.choices(string.ascii_lowercase, k=6))}@inrem.test"
    password = "Test1234!"

    await page.goto(f"{WEB_BASE}/")
    await page.wait_for_load_state("networkidle")

    # 회원가입
    signup_btn = page.locator("text=회원가입")
    if not await signup_btn.is_visible():
        result.fail("온보딩-회원가입 버튼 없음")
        return
    await signup_btn.click()
    await page.fill("input[type='email']", email)
    pwd_inputs = page.locator("input[type='password']")
    await pwd_inputs.nth(0).fill(password)
    await pwd_inputs.nth(1).fill(password)
    await page.locator("text=가입하기").click()
    await page.wait_for_timeout(1500)

    # 온보딩 Step 1 노출 확인
    intro_text = page.locator("text=InRem이 하는 일")
    if await intro_text.is_visible(timeout=4000):
        result.ok("온보딩 Step 1 노출")
    else:
        result.fail("온보딩 Step 1 미노출")
        return

    # 건너뛰기로 완료
    await page.locator("text=건너뛰기").first.click()
    await page.wait_for_timeout(1500)

    # 홈 화면 도달 확인
    home_indicator = page.locator("text=InRem")
    if await home_indicator.is_visible(timeout=4000):
        result.ok("온보딩 건너뛰기 후 홈 진입")
    else:
        result.fail("온보딩 완료 후 홈 미진입")
```

`main()` 함수에서 기존 시나리오 실행 목록 끝에 추가:

```python
    await scenario_onboarding_new_user(page, result)
```

- [ ] **Step 4: 전체 백엔드 테스트 최종 확인**

```bash
cd back && poetry run pytest tests/ -v
```

Expected: 모든 테스트 그린

- [ ] **Step 5: TypeScript 최종 확인**

```bash
cd front && npx tsc --noEmit
```

Expected: exit 0

- [ ] **Step 6: Commit**

```bash
cd /Users/ig/Desktop/project/InRem
git add front/App.tsx scripts/qa_web.py
git commit -m "feat(onboarding): wire OnboardingFlow into AppContent + qa_web scenario"
```

---

## Task 8: 최종 검증 + Push

**Files:** 없음 (검증만)

- [ ] **Step 1: 백엔드 전체 테스트**

```bash
cd back && poetry run pytest tests/ -v --tb=short
```

Expected: 0 failures. 신규 테스트 `test_onboarding.py` 4개 + `test_notification_provider.py` 4개 포함.

- [ ] **Step 2: 프론트 TypeScript 확인**

```bash
cd front && npx tsc --noEmit
```

Expected: exit 0

- [ ] **Step 3: QA responsive (백엔드·프론트 서버가 실행 중인 경우)**

```bash
python3 scripts/qa_responsive.py
```

Expected: 5/5 통과 (서버 미실행 시 skip)

- [ ] **Step 4: git push**

```bash
cd /Users/ig/Desktop/project/InRem
git log --oneline -8
git push origin main
```

Expected: `main` 브랜치에 Task 1~7의 커밋 모두 push 성공.

---

## 검증 체크리스트 요약

| 항목 | 명령 | 기준 |
|------|------|------|
| 백엔드 테스트 | `poetry run pytest tests/` | 0 failures |
| TypeScript | `npx tsc --noEmit` | exit 0 |
| 온보딩 API | `test_onboarding.py` | 4 PASS |
| Firebase provider | `test_notification_provider.py` | 4 PASS |
| 반응형 회귀 | `qa_responsive.py` | 5/5 |
| E2E 온보딩 | `qa_web.py` (서버 실행 시) | 온보딩 시나리오 PASS |
