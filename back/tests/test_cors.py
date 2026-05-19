"""CORS middleware behavior tests.

We test the parser directly (env → origins list) and a live preflight
request through the middleware.
"""
from __future__ import annotations

import pytest

from app.main import _cors_origins


def test_cors_origins_defaults_when_unset(monkeypatch):
    from app.core import config as cfg

    monkeypatch.setattr(cfg.settings, "CORS_ALLOW_ORIGINS", "")
    origins = _cors_origins()
    assert "http://localhost:8081" in origins
    assert all(o.startswith("http://localhost:") for o in origins)


def test_cors_origins_parses_csv(monkeypatch):
    from app.core import config as cfg

    monkeypatch.setattr(
        cfg.settings,
        "CORS_ALLOW_ORIGINS",
        "https://app.inrem.io, https://www.inrem.io,  ,https://staging.inrem.io",
    )
    origins = _cors_origins()
    assert origins == [
        "https://app.inrem.io",
        "https://www.inrem.io",
        "https://staging.inrem.io",
    ]


@pytest.mark.asyncio
async def test_cors_preflight_includes_allow_origin_for_dev(async_client):
    """A preflight from an allowed dev origin must echo the origin back."""
    resp = await async_client.options(
        "/api/v1/auth/login",
        headers={
            "origin": "http://localhost:8081",
            "access-control-request-method": "POST",
            "access-control-request-headers": "content-type",
        },
    )
    # 200 from CORSMiddleware on preflight
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:8081"
