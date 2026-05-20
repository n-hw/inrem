"""Email notification service for fallback alerts.

알림 푸시가 실패한 경우의 백업 채널. 프로바이더는 `EmailProvider`
Protocol 만 구현하면 어디서든 갈아끼울 수 있다.

현재 사용 중인 프로바이더:
- `GmailSMTPProvider` — `.env` 의 `GMAIL_USERNAME` + `GMAIL_APP_PASSWORD`
  가 설정되어 있으면 자동 활성화. dev/alpha 단계용.
- `MockEmailProvider` — env 가 없으면 폴백. 로그에만 찍고 실제 발송 안 함.

**프로덕션 전환 가이드**: Gmail 은 ~500/일 한도 + 스팸 분류 위험이
있어, public launch 전에 Resend/SendGrid/SES 중 하나로 갈아탈 것을
권장한다. 새 `*Provider` 클래스를 추가하고 `_build_default_provider()`
에 케이스를 더하면 끝.
"""

import logging
from email.message import EmailMessage
from typing import Protocol
from uuid import UUID

import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailProvider(Protocol):
    """Protocol for email providers (SendGrid, Mailgun, AWS SES, Gmail SMTP, …)."""

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
    ) -> bool:
        """Send an email. Returns True on success, False on failure."""
        ...


class MockEmailProvider:
    """Mock email provider for development/testing (no real SMTP traffic)."""

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
    ) -> bool:
        logger.info(
            "mock_email_send",
            extra={"to": to_email, "subject": subject},
        )
        return True


class GmailSMTPProvider:
    """Gmail SMTP provider using App Password.

    Requirements (사용자가 한 번만 셋업):
    1. Google 계정 → 보안 → 2단계 인증 활성화.
    2. 같은 페이지 → "앱 비밀번호" 생성 (16자리, 공백 제거하고 사용).
    3. `.env` 에 `GMAIL_USERNAME=…@gmail.com`, `GMAIL_APP_PASSWORD=…`,
       선택적으로 `GMAIL_FROM_NAME="InRem"` 추가.

    Limits (출시 전 알아두기):
    - Personal Gmail: ~500 emails/day, Workspace: 2,000/day.
    - 본인이 ToS 위반(자동 트랜잭션 발송) 으로 분류되면 계정 정지 가능.
    - bounce webhook 없음 — 실패는 SMTP 에러로만 알 수 있음.
    """

    def __init__(
        self,
        *,
        username: str,
        app_password: str,
        from_name: str = "InRem",
        host: str = "smtp.gmail.com",
        port: int = 587,
    ) -> None:
        self.username = username
        self.app_password = app_password
        self.from_name = from_name
        self.host = host
        self.port = port

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: str | None = None,
    ) -> bool:
        msg = EmailMessage()
        msg["From"] = f"{self.from_name} <{self.username}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body_text)
        if body_html:
            msg.add_alternative(body_html, subtype="html")

        try:
            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                start_tls=True,
                username=self.username,
                password=self.app_password,
                timeout=15,
            )
            logger.info(
                "gmail_send_ok",
                extra={"to": to_email, "subject": subject},
            )
            return True
        except Exception as e:
            # SMTP 실패는 안전 알림 도달 실패와 같음 — 로그로 강제 노출.
            logger.error(
                "gmail_send_failed",
                extra={"to": to_email, "subject": subject, "error": str(e)},
                exc_info=True,
            )
            return False


# Singleton provider instance
_email_provider: EmailProvider | None = None


class EmailConfigError(RuntimeError):
    """Raised when production env tries to start without a real email provider."""


def _build_default_provider() -> EmailProvider:
    """Pick the right provider based on env.

    Gmail 자격증명이 있으면 Gmail SMTP, 없으면 dev 안전망으로 Mock.

    **Production 가드**: `ENV=production` 인데 Gmail (혹은 향후 다른 실 발송)
    프로바이더 자격증명이 없다면 silent 로 Mock 폴백하지 않고 startup 에서
    에러를 던진다 — 알림이 실제로 도달하지 않는 상태로 prod 가 떠 있는
    것은 안전 알림 서비스에 치명적.
    """
    username = settings.GMAIL_USERNAME
    password = settings.GMAIL_APP_PASSWORD
    if username and password:
        logger.info(
            "email_provider_init",
            extra={"provider": "GmailSMTPProvider", "from": username},
        )
        return GmailSMTPProvider(
            username=username,
            app_password=password,
            from_name=settings.GMAIL_FROM_NAME or "InRem",
        )

    if settings.ENV == "production":
        raise EmailConfigError(
            "ENV=production 인데 이메일 프로바이더 자격증명이 없습니다. "
            "GMAIL_USERNAME + GMAIL_APP_PASSWORD 또는 다른 실 발송 "
            "프로바이더를 설정하세요. 안부 알림 미도달은 서비스 결함입니다."
        )

    logger.warning(
        "email_provider_init_mock",
        extra={"reason": "GMAIL_USERNAME / GMAIL_APP_PASSWORD not set"},
    )
    return MockEmailProvider()


def initialize_email_provider(provider: EmailProvider | None = None) -> None:
    """Install a provider. `None` → auto-detect from env."""
    global _email_provider
    _email_provider = provider or _build_default_provider()


def get_email_provider() -> EmailProvider:
    """Get the email provider instance, lazy-init from env if needed."""
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
