"""
WEBXES Tech — Settings router

View and toggle config settings (DRY_RUN, etc).
"""

import os
from pathlib import Path

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.auth import verify_token
from config import VAULT_PATH, WORK_ZONE, IS_CLOUD, DRY_RUN

router = APIRouter(prefix="/api/settings", tags=["settings"])


class DryRunUpdate(BaseModel):
    enabled: bool


def _get_env_path() -> Path:
    return VAULT_PATH / ".env"


@router.get("")
def get_settings(user: str = Depends(verify_token)):
    """Get current configuration."""
    return {
        "dry_run": DRY_RUN,
        "vault_path": str(VAULT_PATH),
        "work_zone": WORK_ZONE,
        "is_cloud": IS_CLOUD,
    }


@router.put("/dry-run")
def toggle_dry_run(body: DryRunUpdate, user: str = Depends(verify_token)):
    """Toggle DRY_RUN in .env file."""
    env_path = _get_env_path()
    if not env_path.exists():
        return {"error": ".env file not found"}

    content = env_path.read_text(encoding="utf-8")
    new_value = "true" if body.enabled else "false"

    if "DRY_RUN=" in content:
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("DRY_RUN="):
                lines[i] = f"DRY_RUN={new_value}"
                break
        content = "\n".join(lines)
    else:
        content += f"\nDRY_RUN={new_value}\n"

    env_path.write_text(content, encoding="utf-8")

    # Update runtime
    os.environ["DRY_RUN"] = new_value

    return {"dry_run": body.enabled, "status": "updated"}
