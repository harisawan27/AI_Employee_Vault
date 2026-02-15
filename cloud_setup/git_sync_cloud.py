"""
WEBXES Tech — Cloud Git Sync

Runs on cloud VM. Every 5 minutes:
1. git pull --rebase (get local changes)
2. git add relevant dirs (Needs_Action, Updates, Signals, Done, Logs, Plans)
3. git commit if changes exist
4. git push

Only syncs markdown/state files. Never syncs .env or credentials.

Usage:
    python cloud_setup/git_sync_cloud.py          # Run sync loop
    python cloud_setup/git_sync_cloud.py --once    # Sync once and exit
"""

import argparse
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VAULT_ROOT))

from config import VAULT_PATH, LOGS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS / "git_sync.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("git_sync_cloud")

SYNC_INTERVAL = int(os.getenv("GIT_SYNC_INTERVAL", "300"))  # 5 minutes
GIT_BRANCH = os.getenv("GIT_BRANCH", "main")

# Directories to sync (relative to vault root)
SYNC_DIRS = [
    "Needs_Action",
    "Done",
    "Plans",
    "Logs",
    "In_Progress",
    "Updates",
    "Signals",
    "Dashboard.md",
]


def run_git(args: list[str], cwd: Path = None) -> tuple[int, str, str]:
    """Run a git command and return (returncode, stdout, stderr)."""
    cmd = ["git"] + args
    result = subprocess.run(
        cmd, cwd=str(cwd or VAULT_PATH),
        capture_output=True, text=True, timeout=60
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def sync():
    """Perform one sync cycle: pull, add, commit, push."""
    now = datetime.now()

    # 1. Pull latest changes
    rc, out, err = run_git(["pull", "--rebase", "origin", GIT_BRANCH])
    if rc != 0:
        # If rebase fails, abort and try merge instead
        if "CONFLICT" in err or "conflict" in err.lower():
            log.warning("Rebase conflict detected, aborting rebase...")
            run_git(["rebase", "--abort"])
            rc, out, err = run_git(["pull", "--no-rebase", "origin", GIT_BRANCH])
            if rc != 0:
                log.error(f"Pull failed: {err}")
                return False
        elif "not a git repository" in err.lower():
            log.error("Not a git repository. Skipping sync.")
            return False
        else:
            log.warning(f"Pull warning: {err}")

    log.info(f"Pull: {out or 'up to date'}")

    # 2. Add sync directories
    has_changes = False
    for item in SYNC_DIRS:
        path = VAULT_PATH / item
        if path.exists():
            rc, _, _ = run_git(["add", str(item)])
            if rc == 0:
                has_changes = True

    # 3. Check if there are staged changes
    rc, diff_out, _ = run_git(["diff", "--cached", "--name-only"])
    if not diff_out:
        log.info("No changes to sync")
        return True

    # 4. Commit
    commit_msg = f"cloud sync: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    rc, out, err = run_git(["commit", "-m", commit_msg])
    if rc != 0:
        log.error(f"Commit failed: {err}")
        return False
    log.info(f"Committed: {commit_msg}")

    # 5. Push
    rc, out, err = run_git(["push", "origin", GIT_BRANCH])
    if rc != 0:
        log.error(f"Push failed: {err}")
        return False
    log.info("Pushed to remote")

    return True


def main():
    parser = argparse.ArgumentParser(description="WEBXES Tech Cloud Git Sync")
    parser.add_argument("--once", action="store_true", help="Sync once and exit")
    args = parser.parse_args()

    LOGS.mkdir(exist_ok=True)

    if args.once:
        success = sync()
        sys.exit(0 if success else 1)

    log.info("=== WEBXES Tech Cloud Git Sync Starting ===")
    log.info(f"Vault: {VAULT_PATH}")
    log.info(f"Branch: {GIT_BRANCH}")
    log.info(f"Interval: {SYNC_INTERVAL}s")

    try:
        while True:
            try:
                sync()
            except Exception as e:
                log.error(f"Sync error: {e}")
            time.sleep(SYNC_INTERVAL)
    except KeyboardInterrupt:
        log.info("Git Sync stopped.")


if __name__ == "__main__":
    main()
