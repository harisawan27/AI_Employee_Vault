"""
WEBXES Tech — Inbox router

List and view Needs_Action items with filtering and pagination.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.auth import verify_token
from api.utils.file_parser import list_vault_files, parse_frontmatter, get_file_id, validate_vault_path
from config import NEEDS_ACTION

router = APIRouter(prefix="/api/inbox", tags=["inbox"])


@router.get("")
def list_inbox(
    type: Optional[str] = Query(None, description="Filter by type (email, task, briefing)"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: str = Depends(verify_token),
):
    """List Needs_Action items with optional filters."""
    items = list_vault_files(NEEDS_ACTION)

    # Apply filters
    if type:
        items = [i for i in items if i["metadata"].get("type", "").lower() == type.lower()]
    if priority:
        items = [i for i in items if i["metadata"].get("priority", "").lower() == priority.lower()]

    # Pagination
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page

    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page if total > 0 else 0,
    }


@router.get("/{item_id}")
def get_inbox_item(item_id: str, user: str = Depends(verify_token)):
    """Get full content of a Needs_Action item."""
    # Find the file
    items = list_vault_files(NEEDS_ACTION)
    match = next((i for i in items if i["id"] == item_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Item not found")

    path = validate_vault_path(match["path"])
    metadata, content = parse_frontmatter(path)

    return {
        "id": item_id,
        "filename": match["filename"],
        "path": match["path"],
        "domain": match["domain"],
        "metadata": metadata,
        "content": content,
        "modified": match["modified"],
    }
