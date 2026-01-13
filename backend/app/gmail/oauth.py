from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("utf-8"))


def _sign_state(payload_b64: str, secret: str) -> str:
    sig = hmac.new(secret.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    return _b64url(sig)


def create_state(secret: str, *, max_age_seconds: int = 600) -> str:
    now = int(time.time())
    payload = {
        "ts": now,
        "exp": now + max_age_seconds,
        "nonce": secrets.token_urlsafe(24),
    }
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig = _sign_state(payload_b64, secret)
    return f"{payload_b64}.{sig}"


def verify_state(state: str, secret: str) -> bool:
    try:
        payload_b64, sig = state.split(".", 1)
    except ValueError:
        return False

    expected = _sign_state(payload_b64, secret)
    if not hmac.compare_digest(expected, sig):
        return False

    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception:
        return False

    now = int(time.time())
    exp = int(payload.get("exp", 0))
    return now <= exp


def build_authorization_url(state: str) -> str:
    settings = get_settings()

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": settings.google_scopes,
        "access_type": "offline",
        "include_granted_scopes": "true",
        "state": state,
        # prompt=consent helps ensure refresh_token is returned in some cases.
        # Keep it on for MVP to reduce "no refresh token" surprises.
        "prompt": "consent",
    }

    from urllib.parse import urlencode

    return f"{settings.google_auth_url}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    settings = get_settings()

    data = {
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": settings.google_redirect_uri,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(settings.google_token_url, data=data)
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    settings = get_settings()

    data = {
        "refresh_token": refresh_token,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "grant_type": "refresh_token",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(settings.google_token_url, data=data)
        resp.raise_for_status()
        return resp.json()


def compute_expires_at(expires_in_seconds: Optional[int]) -> Optional[datetime]:
    if not expires_in_seconds:
        return None
    return datetime.utcnow() + timedelta(seconds=int(expires_in_seconds))
