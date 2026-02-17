"""
WEBXES Tech — SaaS Dashboard API

FastAPI entry point. Mounts all routers, configures CORS,
and launches the vault folder watcher for WebSocket events.

Run:
    python -m uvicorn api.main:app --reload --port 5000
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure vault root is on path for config imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth import router as auth_router
from api.routers.dashboard_router import router as dashboard_router
from api.routers.inbox_router import router as inbox_router
from api.routers.approval_router import router as approval_router
from api.routers.audit_router import router as audit_router
from api.routers.settings_router import router as settings_router
from api.websocket_manager import router as ws_router, start_watcher, stop_watcher


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start vault watcher on startup, stop on shutdown."""
    await start_watcher()
    yield
    await stop_watcher()


app = FastAPI(
    title="WEBXES Tech Dashboard API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(inbox_router)
app.include_router(approval_router)
app.include_router(audit_router)
app.include_router(settings_router)
app.include_router(ws_router)


@app.get("/api/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "webxes-dashboard-api"}
