from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


def _split_csv(value: str | None) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "dev"
    app_name: str = "gmail_agents"
    log_level: str = "INFO"

    database_url: str = "sqlite:///./app.db"

    # OAuth / Google
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/callback"
    google_scopes: str = "https://www.googleapis.com/auth/gmail.readonly"

    google_auth_url: str = "https://accounts.google.com/o/oauth2/v2/auth"
    google_token_url: str = "https://oauth2.googleapis.com/token"

    # Security
    oauth_state_secret: str = "change-me"

    # Hosting / CORS
    allowed_hosts: str = "localhost,127.0.0.1,mako-gorgeous-unicorn.ngrok-free.app"
    cors_allow_origins: str = "http://localhost:8000,http://127.0.0.1:8000"

    frontend_dir: str = "../frontend"

    @property
    def allowed_hosts_list(self) -> List[str]:
        return _split_csv(self.allowed_hosts)

    @property
    def cors_allow_origins_list(self) -> List[str]:
        return _split_csv(self.cors_allow_origins)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
