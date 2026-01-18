from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, JSON, Column


class GmailAccountToken(SQLModel, table=True):
    __tablename__ = "gmail_account_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)

    email: Optional[str] = Field(default=None, index=True, unique=True)

    access_token: str
    refresh_token: Optional[str] = None
    token_type: Optional[str] = "Bearer"
    scope: Optional[str] = None

    expires_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())

class Agent(SQLModel, table=True):
    __tablename__ = "agents"

    id: Optional[int] = Field(default=None, primary_key=True)

    name: Optional[str] = Field(default=None, index=True, unique=True)

    settings: dict = Field(default_factory=dict, sa_column=Column(JSON))
    enabled: Optional[bool] = Field(default=False)
    
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    updated_at: datetime = Field(default_factory=lambda: datetime.utcnow())
