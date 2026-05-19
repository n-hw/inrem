"""Tests for the structured JSON logging formatter."""
from __future__ import annotations

import json
import logging
from io import StringIO

from app.core.logging import JsonFormatter, configure_logging


def test_json_formatter_emits_required_fields():
    fmt = JsonFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="x", lineno=1,
        msg="my_event", args=(), exc_info=None,
    )
    record.user_id = "u-123"
    record.feature = "family_share"

    out = fmt.format(record)
    parsed = json.loads(out)
    assert parsed["event"] == "my_event"
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test"
    assert parsed["user_id"] == "u-123"
    assert parsed["feature"] == "family_share"
    assert "ts" in parsed


def test_configure_logging_writes_json_to_stdout(capsys):
    configure_logging(level="INFO")
    logging.getLogger("inrem.test").info(
        "hello_event", extra={"foo": "bar"}
    )
    captured = capsys.readouterr().out
    # capsys may have multiple lines if other tests logged too; find ours.
    lines = [l for l in captured.splitlines() if "hello_event" in l]
    assert lines, f"event line not found in stdout: {captured!r}"
    parsed = json.loads(lines[-1])
    assert parsed["event"] == "hello_event"
    assert parsed["foo"] == "bar"


def test_json_formatter_coerces_non_serializable():
    """UUIDs, datetimes, custom objects should fall back to str() not crash."""

    class Custom:
        def __repr__(self) -> str:
            return "<custom>"

    fmt = JsonFormatter()
    record = logging.LogRecord(
        name="t", level=logging.INFO, pathname="x", lineno=1,
        msg="evt", args=(), exc_info=None,
    )
    record.obj = Custom()
    parsed = json.loads(fmt.format(record))
    assert parsed["obj"] == "<custom>"
