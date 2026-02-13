"""
WEBXES Tech — Audit Logger

JSON Lines audit trail at Logs/audit.jsonl.

Usage:
    from audit_logger import audit_log, query_events, get_summary
    audit_log("email", "send", {"to": "ceo@example.com"}, "success")
"""

import json
import os
from datetime import datetime
from pathlib import Path

VAULT_PATH = Path(os.getenv("VAULT_PATH", r"F:\AI_Employee_Vault"))
AUDIT_FILE = VAULT_PATH / "Logs" / "audit.jsonl"


def audit_log(category: str, action: str, details: dict = None,
              status: str = "success", error: str = ""):
    """Append a structured audit event to Logs/audit.jsonl."""
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now().isoformat(),
        "category": category,
        "action": action,
        "details": details or {},
        "status": status,
    }
    if error:
        event["error"] = error
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def _load_events() -> list[dict]:
    """Read all events from the audit file."""
    if not AUDIT_FILE.exists():
        return []
    events = []
    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def query_events(category: str = None, start_date: str = None,
                 end_date: str = None) -> list[dict]:
    """Filter audit events by category and/or date range.

    Args:
        category: Filter by event category (e.g., "email", "social_media").
        start_date: ISO date string — include events on or after this date.
        end_date: ISO date string — include events on or before this date.
    """
    events = _load_events()
    filtered = []
    for ev in events:
        if category and ev.get("category") != category:
            continue
        ts = ev.get("timestamp", "")
        if start_date and ts < start_date:
            continue
        if end_date and ts > end_date + "T23:59:59":
            continue
        filtered.append(ev)
    return filtered


def get_summary(start_date: str = None, end_date: str = None) -> dict:
    """Return counts grouped by category and status.

    Returns:
        {
            "total": int,
            "by_category": {"email": 5, "social_media": 3, ...},
            "by_status": {"success": 7, "error": 1, ...},
            "by_category_status": {"email:success": 4, "email:error": 1, ...}
        }
    """
    events = query_events(start_date=start_date, end_date=end_date)
    summary = {
        "total": len(events),
        "by_category": {},
        "by_status": {},
        "by_category_status": {},
    }
    for ev in events:
        cat = ev.get("category", "unknown")
        st = ev.get("status", "unknown")
        summary["by_category"][cat] = summary["by_category"].get(cat, 0) + 1
        summary["by_status"][st] = summary["by_status"].get(st, 0) + 1
        key = f"{cat}:{st}"
        summary["by_category_status"][key] = summary["by_category_status"].get(key, 0) + 1
    return summary
