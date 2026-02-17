"""
WEBXES Tech — WebSocket manager for real-time vault events

Watches Pending_Approval/, Needs_Action/, Approved/, Rejected/ for changes
and broadcasts events to connected WebSocket clients.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError, jwt

from api.auth import JWT_SECRET, JWT_ALGORITHM
from config import PENDING_APPROVAL, NEEDS_ACTION, APPROVED, REJECTED

logger = logging.getLogger("websocket_manager")
router = APIRouter(tags=["websocket"])

# Watcher task handle
_watcher_task: Optional[asyncio.Task] = None


class ConnectionManager:
    """Manage WebSocket connections and broadcast events."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, event: dict):
        """Send event to all connected clients."""
        message = json.dumps(event)
        disconnected = []
        for conn in self.active_connections:
            try:
                await conn.send_text(message)
            except Exception:
                disconnected.append(conn)
        for conn in disconnected:
            self.active_connections.remove(conn)


manager = ConnectionManager()

# Map watched directories to event types
WATCH_DIRS = {
    str(PENDING_APPROVAL): "approval_added",
    str(NEEDS_ACTION): "task_added",
    str(APPROVED): "approval_approved",
    str(REJECTED): "approval_rejected",
}


async def watch_vault_folders():
    """Watch vault folders for changes using polling (cross-platform)."""
    # Track known files and their mtimes
    known_files: dict[str, float] = {}

    # Initial scan
    for dir_path in WATCH_DIRS:
        p = Path(dir_path)
        if p.exists():
            for f in p.rglob("*.md"):
                known_files[str(f)] = f.stat().st_mtime

    while True:
        await asyncio.sleep(2)  # Poll every 2 seconds

        current_files: dict[str, float] = {}
        for dir_path, event_type in WATCH_DIRS.items():
            p = Path(dir_path)
            if not p.exists():
                continue

            for f in p.rglob("*.md"):
                fstr = str(f)
                mtime = f.stat().st_mtime
                current_files[fstr] = mtime

                if fstr not in known_files:
                    # New file
                    await manager.broadcast({
                        "type": event_type,
                        "file": f.name,
                        "path": str(f.relative_to(p.parent)),
                        "action": "created",
                    })
                elif known_files[fstr] != mtime:
                    # Modified file
                    await manager.broadcast({
                        "type": event_type,
                        "file": f.name,
                        "path": str(f.relative_to(p.parent)),
                        "action": "modified",
                    })

        # Check for deleted files
        for fstr in known_files:
            if fstr not in current_files:
                # Determine which watch dir it was in
                for dir_path, event_type in WATCH_DIRS.items():
                    if fstr.startswith(dir_path):
                        fname = Path(fstr).name
                        await manager.broadcast({
                            "type": event_type,
                            "file": fname,
                            "action": "removed",
                        })
                        break

        known_files = current_files


async def start_watcher():
    """Start the vault folder watcher as a background task."""
    global _watcher_task
    _watcher_task = asyncio.create_task(watch_vault_folders())
    logger.info("Vault folder watcher started")


async def stop_watcher():
    """Stop the vault folder watcher."""
    global _watcher_task
    if _watcher_task:
        _watcher_task.cancel()
        try:
            await _watcher_task
        except asyncio.CancelledError:
            pass
        logger.info("Vault folder watcher stopped")


def _verify_ws_token(token: str) -> bool:
    """Verify JWT token for WebSocket connections."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub") is not None
    except JWTError:
        return False


@router.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query("")):
    """WebSocket endpoint for real-time vault events."""
    if not _verify_ws_token(token):
        await websocket.close(code=4001, reason="Invalid token")
        return

    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, handle pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
