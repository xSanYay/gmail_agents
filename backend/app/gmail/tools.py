"""
Gmail Tools for LlamaIndex Agent

These are standalone functions that can be wrapped with FunctionTool
and passed to the LLM for tool calling.

Usage:
    from llama_index.core.tools import FunctionTool
    from app.gmail.tools import list_emails, get_email, get_profile

    tools = [
        FunctionTool.from_defaults(fn=list_emails),
        FunctionTool.from_defaults(fn=get_email),
        FunctionTool.from_defaults(fn=get_profile),
    ]
"""

from typing import Optional
from datetime import date


def list_emails(
    access_token: str,
    query: Optional[str] = None,
    from_email: Optional[str] = None,
    max_results: int = 10,
) -> dict:
    """
    List emails from the user's Gmail inbox.

    Args:
        access_token: The user's Gmail OAuth access token.
        query: Optional search query (e.g., "is:unread", "subject:invoice").
        from_email: Optional filter by sender email address.
        max_results: Maximum number of emails to return (default: 10).

    Returns:
        A dict with 'emails' containing a list of email summaries.
    """
    from app.gmail.client import list_messages, get_message_metadata, to_summary, build_gmail_query
    import asyncio

    # Build the Gmail query
    q = build_gmail_query(from_email=from_email, context=query)

    # Run async functions synchronously
    loop = asyncio.new_event_loop()
    try:
        message_ids = loop.run_until_complete(
            list_messages(access_token, q=q, max_results=max_results)
        )

        emails = []
        for msg in message_ids:
            metadata = loop.run_until_complete(
                get_message_metadata(access_token, msg["id"])
            )
            summary = to_summary(metadata)
            emails.append({
                "id": summary.id,
                "from": summary.from_email,
                "subject": summary.subject,
                "snippet": summary.snippet,
                "date": summary.date,
            })
    finally:
        loop.close()

    return {"emails": emails, "count": len(emails)}


def get_email(access_token: str, email_id: str) -> dict:
    """
    Get detailed information about a specific email.

    Args:
        access_token: The user's Gmail OAuth access token.
        email_id: The unique ID of the email to retrieve.

    Returns:
        A dict with email details including from, subject, snippet, and date.
    """
    from app.gmail.client import get_message_metadata, to_summary
    import asyncio

    loop = asyncio.new_event_loop()
    try:
        metadata = loop.run_until_complete(
            get_message_metadata(access_token, email_id)
        )
        summary = to_summary(metadata)
    finally:
        loop.close()

    return {
        "id": summary.id,
        "thread_id": summary.thread_id,
        "from": summary.from_email,
        "subject": summary.subject,
        "snippet": summary.snippet,
        "date": summary.date,
    }
