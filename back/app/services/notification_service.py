"""Push notification service — provider pattern.

현재 사용 중인 프로바이더:
- FCMNotificationProvider — FIREBASE_CREDENTIALS_PATH 설정 시 자동 활성화.
- NoopNotificationProvider — credentials 없으면 폴백. 로그에만 기록.

프로덕션 전환: FIREBASE_CREDENTIALS_PATH 를 service account JSON 경로로 설정.
ENV=production + credentials 미설정 시 NotificationConfigError raise (fail-fast).
"""

import asyncio
import logging
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)


# ── Provider Protocol ────────────────────────────────────────────────────────

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
            response = await asyncio.to_thread(messaging.send, message)
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
            response = await asyncio.to_thread(messaging.send_each_for_multicast, message)
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


def initialize_notification_provider(provider: NotificationProvider | None = None) -> None:
    """Call once at app startup (in lifespan). Raises NotificationConfigError in prod."""
    global _provider
    _provider = provider or _build_default_provider()


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
