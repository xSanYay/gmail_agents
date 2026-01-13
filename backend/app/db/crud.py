from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Session, desc, select

from app.db.models import GmailAccountToken


def get_latest_account(session: Session) -> Optional[GmailAccountToken]:
    statement = select(GmailAccountToken).order_by(desc(GmailAccountToken.updated_at)).limit(1)
    return session.exec(statement).first()


def get_account_by_email(session: Session, email: str) -> Optional[GmailAccountToken]:
    statement = select(GmailAccountToken).where(GmailAccountToken.email == email)
    return session.exec(statement).first()


def get_account_by_id(session: Session, account_id: int) -> Optional[GmailAccountToken]:
    return session.get(GmailAccountToken, account_id)


def upsert_account_token(session: Session, token: GmailAccountToken) -> GmailAccountToken:
    now = datetime.utcnow()
    existing = None
    if token.email:
        existing = get_account_by_email(session, token.email)

    if existing:
        existing.access_token = token.access_token
        if token.refresh_token:
            existing.refresh_token = token.refresh_token
        existing.token_type = token.token_type
        existing.scope = token.scope
        existing.expires_at = token.expires_at
        existing.updated_at = now
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    token.created_at = token.created_at or now
    token.updated_at = now
    session.add(token)
    session.commit()
    session.refresh(token)
    return token


def update_tokens(
    session: Session,
    account: GmailAccountToken,
    *,
    access_token: str,
    expires_at,
    refresh_token: Optional[str] = None,
    scope: Optional[str] = None,
    token_type: Optional[str] = None,
) -> GmailAccountToken:
    account.access_token = access_token
    account.expires_at = expires_at
    if refresh_token:
        account.refresh_token = refresh_token
    if scope is not None:
        account.scope = scope
    if token_type is not None:
        account.token_type = token_type
    account.updated_at = datetime.utcnow()
    session.add(account)
    session.commit()
    session.refresh(account)
    return account
