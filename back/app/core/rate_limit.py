"""In-memory per-key rate limiter (token bucket).

Designed for single-instance deployments. For multi-instance prod, swap
the backing store for Redis (`INCR` + `EXPIRE`) without changing the
public API.
"""
from __future__ import annotations

import time
from collections import deque
from threading import Lock
from typing import Deque

from fastapi import HTTPException, status


class SlidingWindowRateLimiter:
    """Sliding-window counter: max `limit` events per `window_seconds` per key.

    Not safe across processes — see module docstring.
    """

    def __init__(self, *, limit: int, window_seconds: float) -> None:
        if limit <= 0:
            raise ValueError("limit must be positive")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[str, Deque[float]] = {}
        self._lock = Lock()

    def check(self, key: str) -> None:
        """Record one hit on `key`. Raises 429 if over the limit."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = self._events.setdefault(key, deque())
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self.limit:
                retry_after = max(1, int(self.window_seconds - (now - bucket[0])))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="요청이 너무 잦아요. 잠시 후 다시 시도해 주세요.",
                    headers={"Retry-After": str(retry_after)},
                )
            bucket.append(now)


# Concrete limiters used by the app. Tune here, not at call sites.
SECRET_REVEAL_LIMITER = SlidingWindowRateLimiter(limit=10, window_seconds=60.0)
"""Per-user limiter for `/heritage/assets/{id}/secret` reveals (10 per minute)."""

LOGIN_LIMITER = SlidingWindowRateLimiter(limit=5, window_seconds=60.0)
"""Per (email + client IP) limiter for `/auth/login` (5 attempts per minute).

Conservative: any attempt — success or fail — counts. Brute-force gets
blocked quickly; a legitimate user fat-fingering their password 5 times
also gets blocked, but the message tells them to wait 1 minute.
"""

GUARDIAN_INVITE_LIMITER = SlidingWindowRateLimiter(limit=5, window_seconds=3600.0)
"""Per-user limiter for `/guardian/invite` (5 invitations / hour).

Prevents invitation code spam + protects the in-memory `_invitation_codes`
dict from DoS.
"""

REGISTER_LIMITER = SlidingWindowRateLimiter(limit=5, window_seconds=3600.0)
"""Per client IP limiter for `/auth/register` (5 signups / hour).

Stops automated account-creation farms. A legitimate user almost never
needs to create 5+ accounts from one IP within an hour.
"""

HEARTBEAT_LIMITER = SlidingWindowRateLimiter(limit=60, window_seconds=60.0)
"""Per-user limiter for `/signal/heartbeat` (60 signals / minute = 1/sec).

Catches a malicious client trying to keep the inactivity timer reset
infinitely by hammering heartbeats. Legitimate flow is `app_open` +
periodic foreground heartbeats every ~30s — well under this ceiling.
"""

UPSELL_CLICK_LIMITER = SlidingWindowRateLimiter(limit=30, window_seconds=60.0)
"""Per-user limiter for `/settings/upsell/click` (30 clicks / minute).

Premium 페이월 click 은 KPI 메트릭의 입력 — 동일 사용자가 분당 30회
이상 누를 일이 없다. 메트릭 조작 / 로그 스팸 차단.
"""
