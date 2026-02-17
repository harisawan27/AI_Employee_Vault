"""
WEBXES Tech — Audit log router

Query audit.jsonl with filters and get summaries.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from api.auth import verify_token

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from audit_logger import query_events, get_summary

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("")
def list_audit_events(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None, description="ISO date, e.g. 2026-02-01"),
    end_date: Optional[str] = Query(None, description="ISO date, e.g. 2026-02-28"),
    search: Optional[str] = Query(None, description="Search in action/details"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    user: str = Depends(verify_token),
):
    """Query audit events with filters."""
    events = query_events(category=category, start_date=start_date, end_date=end_date)

    # Additional filters not in audit_logger
    if status:
        events = [e for e in events if e.get("status") == status]
    if search:
        search_lower = search.lower()
        events = [
            e for e in events
            if search_lower in e.get("action", "").lower()
            or search_lower in str(e.get("details", "")).lower()
        ]

    # Reverse chronological
    events.reverse()

    total = len(events)
    start = (page - 1) * per_page
    end = start + per_page

    return {
        "events": events[start:end],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page if total > 0 else 0,
    }


@router.get("/summary")
def audit_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    user: str = Depends(verify_token),
):
    """Get aggregated audit summary."""
    return get_summary(start_date=start_date, end_date=end_date)
