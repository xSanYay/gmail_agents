from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.routes_auth import router as auth_router
from app.api.routes_gmail import router as gmail_router
from app.core.config import get_settings
from app.core.logging import RequestIdMiddleware, configure_logging
from app.db.session import init_db

settings = get_settings()
configure_logging(settings.log_level)

logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)

# Middleware
app.add_middleware(RequestIdMiddleware)
allowed_hosts = settings.allowed_hosts_list
if not allowed_hosts and settings.app_env == "dev":
    allowed_hosts = ["*"]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"] ,
)

# Routers
app.include_router(auth_router)
app.include_router(gmail_router)


@app.on_event("startup")
def _startup() -> None:
    init_db()
    logger.info("startup db_initialized")


@app.get("/health")
def health():
    return {"ok": True}


# Serve frontend static files
project_root = Path(__file__).resolve().parents[2]
frontend_dir_setting = Path(settings.frontend_dir)
frontend_dir = (
    frontend_dir_setting
    if frontend_dir_setting.is_absolute()
    else (project_root / frontend_dir_setting).resolve()
)

if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
    logger.info("frontend mounted path=%s", str(frontend_dir))
else:
    logger.warning("frontend not mounted missing_path=%s", str(frontend_dir))
