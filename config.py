"""
WEBXES Tech — Central Configuration

Detects work zone (cloud vs local) and provides all vault paths.
Cloud detection: presence of /etc/webxes_cloud_marker file.

Usage:
    from config import VAULT_PATH, IS_CLOUD, IS_LOCAL, WORK_ZONE
"""

import os
import platform
from pathlib import Path

from dotenv import load_dotenv

# Detect cloud vs local
_CLOUD_MARKER = Path("/etc/webxes_cloud_marker")
IS_CLOUD = _CLOUD_MARKER.exists()
IS_LOCAL = not IS_CLOUD
WORK_ZONE = "cloud" if IS_CLOUD else "local"

# Determine vault path
if IS_CLOUD:
    _default_vault = "/opt/ai_employee_vault"
else:
    _default_vault = r"F:\AI_Employee_Vault" if platform.system() == "Windows" else str(Path.home() / "AI_Employee_Vault")

# Load .env from vault root
_env_path = Path(os.getenv("VAULT_PATH", _default_vault)) / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

VAULT_PATH = Path(os.getenv("VAULT_PATH", _default_vault))

# Standard subdirectories
NEEDS_ACTION = VAULT_PATH / "Needs_Action"
PENDING_APPROVAL = VAULT_PATH / "Pending_Approval"
APPROVED = VAULT_PATH / "Approved"
REJECTED = VAULT_PATH / "Rejected"
DONE = VAULT_PATH / "Done"
PLANS = VAULT_PATH / "Plans"
LOGS = VAULT_PATH / "Logs"
INBOX = VAULT_PATH / "Inbox"
IN_PROGRESS = VAULT_PATH / "In_Progress"
UPDATES = VAULT_PATH / "Updates"
SIGNALS = VAULT_PATH / "Signals"

# Work-zone claim directories
IN_PROGRESS_CLOUD = IN_PROGRESS / "cloud"
IN_PROGRESS_LOCAL = IN_PROGRESS / "local"

# Credentials (None on cloud — no browser sessions there)
GMAIL_CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH") if IS_LOCAL else None
GMAIL_TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH") if IS_LOCAL else None
LINKEDIN_SESSION_PATH = os.getenv("LINKEDIN_SESSION_PATH") if IS_LOCAL else None
FACEBOOK_SESSION_PATH = os.getenv("FACEBOOK_SESSION_PATH") if IS_LOCAL else None
INSTAGRAM_SESSION_PATH = os.getenv("INSTAGRAM_SESSION_PATH") if IS_LOCAL else None
TWITTER_SESSION_PATH = os.getenv("TWITTER_SESSION_PATH") if IS_LOCAL else None

# Odoo (available on both zones)
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "odoo_fte")
ODOO_USER = os.getenv("ODOO_USER", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")

# Safety
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"


def ensure_dirs():
    """Create all standard vault directories if they don't exist."""
    for d in [NEEDS_ACTION, PENDING_APPROVAL, APPROVED, REJECTED, DONE,
              PLANS, LOGS, INBOX, IN_PROGRESS_CLOUD, IN_PROGRESS_LOCAL,
              UPDATES, SIGNALS]:
        d.mkdir(parents=True, exist_ok=True)
