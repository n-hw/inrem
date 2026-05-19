from datetime import datetime, timedelta
from typing import Any, Literal

from jose import JWTError, jwt
import bcrypt

from app.core.config import settings

# JWT settings
ALGORITHM = "HS256"

# Token types — embed in payload so we can reject the wrong kind.
TokenType = Literal["access", "refresh"]
ACCESS_TYPE: TokenType = "access"
REFRESH_TYPE: TokenType = "refresh"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """Hash a plain password using bcrypt."""
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')


def _create_token(
    subject: str | Any,
    *,
    token_type: TokenType,
    expires_delta: timedelta,
) -> str:
    """Internal — sign a token with the given type embedded in payload."""
    expire = datetime.utcnow() + expires_delta
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": token_type,
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """Short-lived access token (default `ACCESS_TOKEN_EXPIRE_MINUTES`)."""
    delta = expires_delta or timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return _create_token(subject, token_type=ACCESS_TYPE, expires_delta=delta)


def create_refresh_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """Long-lived refresh token (default `REFRESH_TOKEN_EXPIRE_DAYS`)."""
    delta = expires_delta or timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    return _create_token(subject, token_type=REFRESH_TYPE, expires_delta=delta)


def decode_access_token(token: str) -> str | None:
    """Decode and validate a JWT access token. Returns subject (user_id) or None.

    Rejects refresh tokens — the dependency that protects API endpoints must
    not accept long-lived refresh tokens by accident.
    """
    return _decode_with_type(token, expected_type=ACCESS_TYPE)


def decode_refresh_token(token: str) -> str | None:
    """Decode and validate a JWT refresh token. Returns subject or None.

    Symmetric to `decode_access_token` but only accepts refresh tokens.
    """
    return _decode_with_type(token, expected_type=REFRESH_TYPE)


def _decode_with_type(token: str, *, expected_type: TokenType) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
    if payload.get("type") != expected_type:
        return None
    subject = payload.get("sub")
    if not isinstance(subject, str):
        return None
    return subject
