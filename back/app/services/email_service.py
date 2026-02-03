"""Email notification service for fallback alerts.

This module provides email notification capabilities as a backup
when push notifications fail. Currently a skeleton - implement
with SendGrid, Mailgun, or AWS SES as needed.
"""

import logging
from typing import Protocol
from uuid import UUID

logger = logging.getLogger(__name__)


class EmailProvider(Protocol):
    """Protocol for email providers (SendGrid, Mailgun, AWS SES, etc.)."""
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
    ) -> bool:
        """Send an email.
        
        Args:
            to_email: Recipient email address.
            subject: Email subject.
            body_text: Plain text body.
            body_html: Optional HTML body.
            
        Returns:
            True if sent successfully.
        """
        ...


class MockEmailProvider:
    """Mock email provider for development/testing."""
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
    ) -> bool:
        logger.info(f"[MockEmail] Would send to {to_email}: {subject}")
        logger.debug(f"[MockEmail] Body: {body_text[:100]}...")
        return True


# TODO: Implement real providers
# class SendGridProvider:
#     def __init__(self, api_key: str):
#         self.api_key = api_key
#     
#     async def send_email(self, to_email, subject, body_text, body_html=None):
#         # Use sendgrid library
#         pass


# Singleton provider instance
_email_provider: EmailProvider | None = None


def initialize_email_provider(provider: EmailProvider | None = None) -> None:
    """Initialize the email provider.
    
    Args:
        provider: Email provider instance. Defaults to MockEmailProvider.
    """
    global _email_provider
    _email_provider = provider or MockEmailProvider()
    logger.info(f"[Email] Initialized provider: {type(_email_provider).__name__}")


def get_email_provider() -> EmailProvider:
    """Get the email provider instance."""
    global _email_provider
    if _email_provider is None:
        initialize_email_provider()
    return _email_provider  # type: ignore


async def send_guardian_email_alert(
    guardian_email: str,
    ward_email: str,
    event_id: UUID,
) -> bool:
    """Send guardian alert via email (fallback for push failure).
    
    Args:
        guardian_email: Guardian's email address.
        ward_email: Ward's email (for identification).
        event_id: PulseEvent ID.
        
    Returns:
        True if sent successfully.
    """
    provider = get_email_provider()
    
    subject = "[긴급] InRem 안부 확인 요청"
    body_text = f"""
안녕하세요,

귀하가 보호자로 등록된 {ward_email}님의 활동이 오랫동안 감지되지 않았습니다.

안부 확인이 필요합니다.
앱에서 자세한 내용을 확인해주세요.

이벤트 ID: {event_id}

- InRem 팀
"""
    
    body_html = f"""
<html>
<body style="font-family: sans-serif; line-height: 1.6;">
    <h2 style="color: #E57373;">⚠️ 긴급: 안부 확인 필요</h2>
    <p>안녕하세요,</p>
    <p>귀하가 보호자로 등록된 <strong>{ward_email}</strong>님의 활동이 오랫동안 감지되지 않았습니다.</p>
    <p><strong>안부 확인이 필요합니다.</strong></p>
    <p>앱에서 자세한 내용을 확인해주세요.</p>
    <hr>
    <p style="color: #888; font-size: 12px;">이벤트 ID: {event_id}</p>
    <p style="color: #888; font-size: 12px;">- InRem 팀</p>
</body>
</html>
"""
    
    return await provider.send_email(
        to_email=guardian_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
    )


async def send_soft_checkin_email(
    user_email: str,
    event_id: UUID,
) -> bool:
    """Send soft check-in via email (fallback for push failure).
    
    Args:
        user_email: User's email address.
        event_id: PulseEvent ID.
        
    Returns:
        True if sent successfully.
    """
    provider = get_email_provider()
    
    subject = "[InRem] 잘 지내시나요?"
    body_text = f"""
안녕하세요,

오랫동안 앱 활동이 없어 안부 확인차 연락드렸습니다.
괜찮으시다면 앱을 열어 확인해주세요.

이벤트 ID: {event_id}

- InRem 팀
"""
    
    return await provider.send_email(
        to_email=user_email,
        subject=subject,
        body_text=body_text,
    )
