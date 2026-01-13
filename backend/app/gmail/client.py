from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"


@dataclass
class MessageSummary:
    id: str
    thread_id: str
    snippet: str | None
    from_email: str | None
    subject: str | None
    date: str | None


def _header_value(headers: List[Dict[str, Any]], name: str) -> Optional[str]:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value")
    return None


def build_gmail_query(
    *,
    from_email: Optional[str] = None,
    after_date: Optional[date] = None,
    context: Optional[str] = None,
    context_field: str = "subject",
) -> str:
    parts: List[str] = []

    if from_email:
        parts.append(f"from:{from_email}")

    if after_date:
        # Gmail search commonly accepts after:YYYY/MM/DD
        parts.append(f"after:{after_date.strftime('%Y/%m/%d')}")

    if context:
        ctx = context.strip()
        if ":" in ctx:
            # allow advanced Gmail search syntax directly
            parts.append(ctx)
        else:
            if context_field == "any":
                parts.append(ctx)
            else:
                # default: subject search
                parts.append(f"subject:({ctx})")

    return " ".join(parts)


async def list_messages(access_token: str, *, q: str, max_results: int = 10) -> List[Dict[str, Any]]:
    url = f"{GMAIL_API_BASE}/users/me/messages"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"q": q, "maxResults": max_results}

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("messages", [])


async def get_message_metadata(access_token: str, message_id: str) -> Dict[str, Any]:
    url = f"{GMAIL_API_BASE}/users/me/messages/{message_id}"
    headers = {"Authorization": f"Bearer {access_token}"}

    params = {
        "format": "metadata",
        "metadataHeaders": ["From", "Subject", "Date"],
    }

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()


async def get_profile_email(access_token: str) -> Optional[str]:
    url = f"{GMAIL_API_BASE}/users/me/profile"
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data.get("emailAddress")


def to_summary(message: Dict[str, Any]) -> MessageSummary:
    payload = message.get("payload", {})
    headers = payload.get("headers", [])

    return MessageSummary(
        id=message.get("id"),
        thread_id=message.get("threadId"),
        snippet=message.get("snippet"),
        from_email=_header_value(headers, "From"),
        subject=_header_value(headers, "Subject"),
        date=_header_value(headers, "Date"),
    )
