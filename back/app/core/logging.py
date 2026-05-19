"""Structured (JSON) logging setup.

Goal: make every log line machine-parseable so the future analytics
pipeline (Loki/CloudWatch/Datadog…) can index `event`, `user_id`, etc.
without regex scraping.

Usage — call `configure_logging()` once at app startup.

Convention for callers:
- `logger.info("event_name", extra={"key": "value", ...})`
- `event_name` is the *message* (snake_case). The structured fields go
  in `extra`. The formatter merges them into the JSON output.

Sentry: this module also installs a Sentry handler when
`settings.SENTRY_DSN` is set. Without a DSN, Sentry is a no-op.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

# Standard LogRecord attributes — anything not in this set is treated as
# structured payload from the caller's `extra=` and copied into the JSON.
_STD_ATTRS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "taskName",
    "message",
    "asctime",
}


class JsonFormatter(logging.Formatter):
    """Format every log record as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        # Structured fields from caller's `extra=` kwarg.
        for key, value in record.__dict__.items():
            if key in _STD_ATTRS or key.startswith("_"):
                continue
            payload[key] = _coerce(value)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def _coerce(value: Any) -> Any:
    """Make values JSON-serializable without losing key info."""
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return str(value)


def configure_logging(level: str = "INFO") -> None:
    """Install the JSON formatter on the root logger.

    Idempotent: clears existing handlers first so reloading is safe.
    """
    root = logging.getLogger()
    root.setLevel(level)
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

    # Quiet down a couple of noisy libraries to WARNING at most.
    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def configure_sentry(dsn: str | None) -> None:
    """Install Sentry SDK if a DSN is configured. Safe no-op otherwise.

    Sentry is an *optional* dependency — this function imports lazily so
    the package only needs to be installed in production.
    """
    if not dsn:
        return
    try:
        import sentry_sdk  # type: ignore
    except ImportError:
        logging.getLogger(__name__).warning(
            "sentry_sdk not installed; SENTRY_DSN is set but reporting is disabled. "
            "Add `sentry-sdk` to production dependencies to enable."
        )
        return
    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=0.0,  # Tune in prod.
        send_default_pii=False,
    )
