from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.db import crud
from app.db.models import GmailAccountToken
from app.db.session import get_session
from app.gmail import client as gmail_client
from app.gmail import oauth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gmail", tags=["gmail"])


def _needs_refresh(account: GmailAccountToken) -> bool:
    if not account.expires_at:
        return False
    return datetime.utcnow() >= (account.expires_at - timedelta(seconds=60))


async def _get_valid_access_token(session: Session, account: GmailAccountToken) -> str:
    if not _needs_refresh(account):
        return account.access_token

    if not account.refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token stored; re-auth required")

    logger.info("token_refresh start account_id=%s email=%s", account.id, account.email)
    try:
        refreshed = await oauth.refresh_access_token(account.refresh_token)
    except Exception as e:
        logger.exception("token_refresh failed")
        raise HTTPException(status_code=502, detail="Token refresh failed") from e

    new_access_token = refreshed.get("access_token")
    expires_at = oauth.compute_expires_at(refreshed.get("expires_in"))

    if not new_access_token:
        raise HTTPException(status_code=502, detail="Refresh response missing access_token")

    crud.update_tokens(
        session,
        account,
        access_token=new_access_token,
        expires_at=expires_at,
        scope=refreshed.get("scope", account.scope),
        token_type=refreshed.get("token_type", account.token_type),
    )
    return new_access_token


@router.get("/accounts")
def list_accounts(session: Session = Depends(get_session)):
    # Minimal: list last connected account
    latest = crud.get_latest_account(session)
    if not latest:
        return {"accounts": []}
    return {
        "accounts": [
            {
                "id": latest.id,
                "email": latest.email,
                "scope": latest.scope,
                "expires_at": latest.expires_at,
                "updated_at": latest.updated_at,
            }
        ]
    }


@router.get("/messages")
async def fetch_messages(
    from_email: Optional[str] = Query(default=None, alias="from"),
    date_after: Optional[date] = Query(default=None, alias="date"),
    context: Optional[str] = Query(default=None),
    context_field: str = Query(default="subject", pattern="^(subject|any)$"),
    max_results: int = Query(default=10, ge=1, le=50),
    account_id: Optional[int] = Query(default=None),
    email: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
):
    account = None
    if account_id is not None:
        account = crud.get_account_by_id(session, account_id)
    elif email is not None:
        account = crud.get_account_by_email(session, email)
    else:
        account = crud.get_latest_account(session)

    if not account:
        raise HTTPException(status_code=404, detail="No connected Gmail account found")

    access_token = await _get_valid_access_token(session, account)

    q = gmail_client.build_gmail_query(
        from_email=from_email,
        after_date=date_after,
        context=context,
        context_field=context_field,
    )

    logger.info(
        "gmail_fetch account_id=%s email=%s q=%s max_results=%s",
        account.id,
        account.email,
        q,
        max_results,
    )

    try:
        msgs = await gmail_client.list_messages(access_token, q=q, max_results=max_results)
        summaries = []
        for m in msgs:
            full = await gmail_client.get_message_metadata(access_token, m["id"])
            summaries.append(gmail_client.to_summary(full).__dict__)
        return {"query": q, "messages": summaries}
    except Exception as e:
        logger.exception("gmail_fetch failed")
        raise HTTPException(status_code=502, detail="Gmail fetch failed") from e
