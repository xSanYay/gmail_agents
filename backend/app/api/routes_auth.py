from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.db import crud
from app.db.models import GmailAccountToken
from app.db.session import get_session
from app.gmail import client as gmail_client
from app.gmail import oauth

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


@router.get("/auth/start")
async def auth_start(settings: Settings = Depends(get_settings)):
    if not settings.google_client_id or not settings.google_client_secret:
        logger.error("oauth_start google_oauth_not_configured")
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    state = oauth.create_state(settings.oauth_state_secret)
    url = oauth.build_authorization_url(state)
    logger.info("oauth_start redirecting_to_google")
    return RedirectResponse(url=url, status_code=302)


@router.get("/api/callback")
async def auth_callback(
    code: str = Query(...),
    state: str = Query(...),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    if not oauth.verify_state(state, settings.oauth_state_secret):
        logger.warning("oauth_callback invalid_state")
        raise HTTPException(status_code=400, detail="Invalid state")

    try:
        token_data = await oauth.exchange_code_for_tokens(code)
    except Exception as e:
        logger.exception("oauth_callback token_exchange_failed")
        raise HTTPException(status_code=502, detail="Token exchange failed") from e

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    token_type = token_data.get("token_type")
    scope = token_data.get("scope")
    expires_at = oauth.compute_expires_at(token_data.get("expires_in"))

    if not access_token:
        raise HTTPException(status_code=502, detail="Missing access_token")

    # Try to determine email for nicer storage
    email = None
    try:
        email = await gmail_client.get_profile_email(access_token)
    except Exception:
        logger.info("oauth_callback profile_email_unavailable")

    token = GmailAccountToken(
        email=email,
        access_token=access_token,
        refresh_token=refresh_token,
        token_type=token_type,
        scope=scope,
        expires_at=expires_at,
    )

    saved = crud.upsert_account_token(session, token)

    logger.info(
        "oauth_callback success account_id=%s email=%s has_refresh_token=%s",
        saved.id,
        saved.email,
        bool(saved.refresh_token),
    )

    # Redirect back to frontend
    return RedirectResponse(url="/success.html", status_code=302)
