"""
WEBXES Tech — Approval router (MAIN FEATURE)

List, view, edit, approve, and reject pending approvals.
Moves files between Pending_Approval/ → Approved/ or Rejected/.
"""

import shutil
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.auth import verify_token
from api.utils.file_parser import (
    list_vault_files,
    parse_frontmatter,
    rebuild_file,
    validate_vault_path,
)
from config import PENDING_APPROVAL, APPROVED, REJECTED

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from audit_logger import audit_log

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


class ContentUpdate(BaseModel):
    content: str


class ApprovalAction(BaseModel):
    note: Optional[str] = ""


@router.get("")
def list_approvals(
    domain: Optional[str] = Query(None, description="Filter by domain (email, social_media, payments)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user: str = Depends(verify_token),
):
    """List all pending approval items."""
    items = list_vault_files(PENDING_APPROVAL)

    if domain and domain != "all":
        items = [i for i in items if i["domain"] == domain]

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
def get_approval(item_id: str, user: str = Depends(verify_token)):
    """Get full content of a pending approval."""
    items = list_vault_files(PENDING_APPROVAL)
    match = next((i for i in items if i["id"] == item_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Approval item not found")

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


@router.put("/{item_id}/content")
def update_content(item_id: str, body: ContentUpdate, user: str = Depends(verify_token)):
    """Save edited content for a pending approval."""
    items = list_vault_files(PENDING_APPROVAL)
    match = next((i for i in items if i["id"] == item_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Approval item not found")

    path = validate_vault_path(match["path"])
    metadata, _ = parse_frontmatter(path)

    # Update metadata with edit timestamp
    metadata["last_edited"] = datetime.now().isoformat()
    metadata["edited_by"] = "ceo_dashboard"

    new_file = rebuild_file(metadata, body.content)
    path.write_text(new_file, encoding="utf-8")

    audit_log("dashboard", "edit_approval", {
        "file": match["filename"],
        "domain": match["domain"],
    })

    return {"status": "saved", "id": item_id}


@router.post("/{item_id}/approve")
def approve_item(item_id: str, body: ApprovalAction = None, user: str = Depends(verify_token)):
    """Approve an item — moves file from Pending_Approval to Approved."""
    if body is None:
        body = ApprovalAction()

    items = list_vault_files(PENDING_APPROVAL)
    match = next((i for i in items if i["id"] == item_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Approval item not found")

    src = validate_vault_path(match["path"])
    domain = match["domain"]

    # Update metadata
    metadata, content = parse_frontmatter(src)
    metadata["status"] = "approved"
    metadata["approved_at"] = datetime.now().isoformat()
    metadata["approved_by"] = "ceo_dashboard"
    if body.note:
        metadata["approval_note"] = body.note

    new_file = rebuild_file(metadata, content)
    src.write_text(new_file, encoding="utf-8")

    # Move to Approved/<domain>/
    dest_dir = APPROVED / domain
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.move(str(src), str(dest))

    audit_log("dashboard", "approve", {
        "file": match["filename"],
        "domain": domain,
        "note": body.note,
    })

    return {"status": "approved", "id": item_id, "moved_to": str(dest.relative_to(APPROVED.parent))}


@router.post("/{item_id}/reject")
def reject_item(item_id: str, body: ApprovalAction = None, user: str = Depends(verify_token)):
    """Reject an item — moves file from Pending_Approval to Rejected."""
    if body is None:
        body = ApprovalAction()

    items = list_vault_files(PENDING_APPROVAL)
    match = next((i for i in items if i["id"] == item_id), None)
    if not match:
        raise HTTPException(status_code=404, detail="Approval item not found")

    src = validate_vault_path(match["path"])
    domain = match["domain"]

    # Update metadata
    metadata, content = parse_frontmatter(src)
    metadata["status"] = "rejected"
    metadata["rejected_at"] = datetime.now().isoformat()
    metadata["rejected_by"] = "ceo_dashboard"
    if body.note:
        metadata["rejection_note"] = body.note

    new_file = rebuild_file(metadata, content)
    src.write_text(new_file, encoding="utf-8")

    # Move to Rejected/<domain>/
    dest_dir = REJECTED / domain
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.move(str(src), str(dest))

    audit_log("dashboard", "reject", {
        "file": match["filename"],
        "domain": domain,
        "note": body.note,
    })

    return {"status": "rejected", "id": item_id, "moved_to": str(dest.relative_to(REJECTED.parent))}
