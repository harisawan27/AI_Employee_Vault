"""
WEBXES Tech — Dashboard stats router

GET /api/dashboard/stats — overview stats, timeline, service health.
"""

import json
from datetime import datetime, date
from pathlib import Path

from fastapi import APIRouter, Depends

from api.auth import verify_token
from config import NEEDS_ACTION, PENDING_APPROVAL, DONE, LOGS

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _count_files(directory: Path) -> int:
    """Count markdown files in a directory recursively."""
    if not directory.exists():
        return 0
    return sum(1 for _ in directory.rglob("*.md"))


def _count_today(directory: Path) -> int:
    """Count files modified today."""
    if not directory.exists():
        return 0
    today = date.today().isoformat()
    count = 0
    for f in directory.rglob("*.md"):
        mtime = datetime.fromtimestamp(f.stat().st_mtime).date().isoformat()
        if mtime == today:
            count += 1
    return count


def _recent_audit_events(n: int = 20) -> list[dict]:
    """Read last N events from audit.jsonl."""
    audit_file = LOGS / "audit.jsonl"
    if not audit_file.exists():
        return []
    events = []
    with open(audit_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events[-n:]


def _service_health() -> list[dict]:
    """Check log file recency as a proxy for service health."""
    log_files = {
        "gmail_watcher": LOGS / "gmail_watcher.log",
        "orchestrator": LOGS / "orchestrator.log",
        "cloud_agent": LOGS / "cloud_agent.log",
        "health_monitor": LOGS / "health_monitor.log",
        "approval_watcher": LOGS / "approval_watcher.log",
    }
    services = []
    now = datetime.now().timestamp()
    for name, log_path in log_files.items():
        if log_path.exists():
            age_minutes = (now - log_path.stat().st_mtime) / 60
            services.append({
                "name": name,
                "status": "active" if age_minutes < 15 else "stale",
                "last_update_minutes_ago": round(age_minutes, 1),
            })
        else:
            services.append({
                "name": name,
                "status": "not_found",
                "last_update_minutes_ago": None,
            })
    return services


@router.get("/stats")
def dashboard_stats(user: str = Depends(verify_token)):
    """Get dashboard overview stats."""
    return {
        "pending_tasks": _count_files(NEEDS_ACTION),
        "approvals_waiting": _count_files(PENDING_APPROVAL),
        "done_today": _count_today(DONE),
        "timeline": _recent_audit_events(20),
        "services": _service_health(),
    }
