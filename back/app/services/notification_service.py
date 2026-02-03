"""Firebase Cloud Messaging notification service.

Provides utilities for sending push notifications via FCM.
"""

import logging
from typing import Any
from uuid import UUID

import firebase_admin
from firebase_admin import credentials, messaging
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)

# Firebase app singleton
_firebase_app: firebase_admin.App | None = None


def initialize_firebase() -> firebase_admin.App | None:
    """Initialize Firebase Admin SDK.
    
    Uses GOOGLE_APPLICATION_CREDENTIALS environment variable
    or a service account JSON file path.
    
    Returns:
        Firebase app instance or None if not configured.
    """
    global _firebase_app
    
    if _firebase_app is not None:
        return _firebase_app
    
    try:
        # Try to get credentials from environment or file
        firebase_credentials_path = settings.FIREBASE_CREDENTIALS_PATH
        
        if firebase_credentials_path:
            cred = credentials.Certificate(firebase_credentials_path)
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("[FCM] Firebase initialized with credentials file")
        else:
            # Try default credentials (from GOOGLE_APPLICATION_CREDENTIALS env var)
            _firebase_app = firebase_admin.initialize_app()
            logger.info("[FCM] Firebase initialized with default credentials")
        
        return _firebase_app
    except Exception as e:
        logger.warning(f"[FCM] Failed to initialize Firebase: {e}")
        return None


def get_firebase_app() -> firebase_admin.App | None:
    """Get the Firebase app instance."""
    global _firebase_app
    return _firebase_app


async def send_push_notification(
    token: str,
    title: str,
    body: str,
    data: dict[str, str] | None = None,
) -> bool:
    """Send a push notification to a single device.
    
    Args:
        token: FCM registration token.
        title: Notification title.
        body: Notification body.
        data: Optional data payload.
        
    Returns:
        True if sent successfully, False otherwise.
    """
    if not _firebase_app:
        logger.warning("[FCM] Firebase not initialized, skipping notification")
        return False
    
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
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
        logger.error(f"[FCM] Sender ID mismatch for token: {token[:20]}...")
        return False
    except Exception as e:
        logger.error(f"[FCM] Failed to send notification: {e}")
        return False


async def send_multicast_notification(
    tokens: list[str],
    title: str,
    body: str,
    data: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Send a push notification to multiple devices.
    
    Args:
        tokens: List of FCM registration tokens.
        title: Notification title.
        body: Notification body.
        data: Optional data payload.
        
    Returns:
        Dict with success_count, failure_count, and failed_tokens.
    """
    if not _firebase_app:
        logger.warning("[FCM] Firebase not initialized, skipping notification")
        return {"success_count": 0, "failure_count": len(tokens), "failed_tokens": tokens}
    
    if not tokens:
        return {"success_count": 0, "failure_count": 0, "failed_tokens": []}
    
    try:
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            tokens=tokens,
        )
        
        response = messaging.send_each_for_multicast(message)
        
        # Collect failed tokens
        failed_tokens = []
        for idx, result in enumerate(response.responses):
            if not result.success:
                failed_tokens.append(tokens[idx])
        
        logger.info(
            f"[FCM] Multicast sent: {response.success_count} success, "
            f"{response.failure_count} failures"
        )
        
        return {
            "success_count": response.success_count,
            "failure_count": response.failure_count,
            "failed_tokens": failed_tokens,
        }
        
    except Exception as e:
        logger.error(f"[FCM] Failed to send multicast notification: {e}")
        return {"success_count": 0, "failure_count": len(tokens), "failed_tokens": tokens}


async def update_fcm_token(
    db: AsyncSession,
    user_id: UUID,
    fcm_token: str | None,
) -> None:
    """Update user's FCM token in the database.
    
    Args:
        db: Database session.
        user_id: User's ID.
        fcm_token: New FCM token (or None to clear).
    """
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(fcm_token=fcm_token)
    )
    await db.commit()


async def clear_invalid_token(db: AsyncSession, user_id: UUID) -> None:
    """Clear a user's FCM token when it becomes invalid."""
    await update_fcm_token(db, user_id, None)
    logger.info(f"[FCM] Cleared invalid token for user {user_id}")


async def send_soft_checkin_notification(
    user: User,
    event_id: UUID,
) -> bool:
    """Send 'Soft Check-in' notification to the user.
    
    Args:
        user: User to notify (must have fcm_token).
        event_id: ID of the PulseEvent.
        
    Returns:
        True if sent successfully.
    """
    if not user.fcm_token:
        logger.warning(f"[FCM] User {user.id} has no FCM token")
        return False
        
    title = "잘 지내시나요?"
    body = "오랫동안 활동이 없어 안부 확인차 연락드렸어요. 괜찮으시다면 앱을 열어주세요."
    
    data = {
        "type": "SOFT_CHECKIN",
        "event_id": str(event_id),
        "user_id": str(user.id),
    }
    
    return await send_push_notification(
        token=user.fcm_token,
        title=title,
        body=body,
        data=data,
    )


async def send_guardian_notification(
    ward: User,
    guardians: list[User],
    event_id: UUID,
) -> int:
    """Send 'Guardian Alert' multicast notification to all guardians.
    
    Args:
        ward: The user who is inactive.
        guardians: List of guardian users.
        event_id: ID of the PulseEvent.
        
    Returns:
        Number of notifications sent successfully.
    """
    if not guardians:
        return 0
        
    # Extract tokens, filtering out users without tokens
    tokens = [g.fcm_token for g in guardians if g.fcm_token]
    
    if not tokens:
        logger.warning(f"[FCM] No valid tokens found for guardians of user {ward.id}")
        return 0
        
    title = "긴급: 활동 미감지"
    body = f"{ward.email}님이 오랫동안 활동이 없습니다. 확인이 필요합니다."
    
    data = {
        "type": "GUARDIAN_ALERT",
        "event_id": str(event_id),
        "ward_id": str(ward.id),
        "severity": "HIGH",
    }
    
    result = await send_multicast_notification(
        tokens=tokens,
        title=title,
        body=body,
        data=data,
    )
    
    # Fallback: Check for failed tokens or users without tokens and send email
    # This is a basic structure. In production, you might want to wait longer or check delivery status.
    if result["failure_count"] > 0:
        logger.info(f"[FCM] {result['failure_count']} pushes failed. Initiating email fallback (Mock/Structure).")
        from app.services.email_service import send_guardian_email_alert
        
        # Identify who failed (simplified: just email all guardians if *any* failed for now, 
        # or we could map tokens back to users if we tracked that better)
        # For this MVP structure, we'll iterate guardians and check if their push failed or wasn't attempted.
        
        failed_tokens_set = set(result["failed_tokens"])
        
        for g in guardians:
            # Condition: User has no token OR their token is in failed list
            should_email = (not g.fcm_token) or (g.fcm_token in failed_tokens_set)
            
            if should_email and g.email:
                try:
                    await send_guardian_email_alert(g.email, ward.email, event_id)
                    logger.info(f"[Email] Fallback email sent to {g.email}")
                except Exception as e:
                    logger.error(f"[Email] Failed to send fallback email to {g.email}: {e}")

    return result["success_count"]
