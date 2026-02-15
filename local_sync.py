"""
WEBXES Tech — Local Sync

Pulls changes from GitHub, processes Updates/ from cloud, and merges
draft content into the local workflow.

Usage:
    python local_sync.py          # Pull and process updates
    python local_sync.py --watch  # Continuous sync loop (every 60s)
"""

import argparse
import json
import logging
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from config import (
    VAULT_PATH, UPDATES, SIGNALS, NEEDS_ACTION, DONE, LOGS,
    IS_LOCAL, ensure_dirs,
)
from audit_logger import audit_log

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS / "local_sync.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("local_sync")

GIT_BRANCH = "main"
SYNC_INTERVAL = 60


def git_pull() -> bool:
    """Pull latest changes from remote."""
    try:
        result = subprocess.run(
            ["git", "pull", "--rebase", "origin", GIT_BRANCH],
            cwd=str(VAULT_PATH), capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            if "conflict" in result.stderr.lower():
                log.warning("Rebase conflict, aborting and trying merge...")
                subprocess.run(["git", "rebase", "--abort"],
                               cwd=str(VAULT_PATH), capture_output=True, timeout=10)
                result = subprocess.run(
                    ["git", "pull", "--no-rebase", "origin", GIT_BRANCH],
                    cwd=str(VAULT_PATH), capture_output=True, text=True, timeout=60
                )
                if result.returncode != 0:
                    log.error(f"Pull failed: {result.stderr}")
                    return False
            else:
                log.warning(f"Pull issue: {result.stderr}")
        log.info(f"Pull: {result.stdout.strip() or 'up to date'}")
        return True
    except Exception as e:
        log.error(f"Git pull error: {e}")
        return False


def process_updates():
    """Process draft files from Updates/ directory (created by cloud agent)."""
    if not UPDATES.exists():
        return 0

    processed = 0
    for filepath in UPDATES.glob("EMAIL_DRAFT_*.md"):
        try:
            log.info(f"Processing cloud draft: {filepath.name}")

            # Move draft to Needs_Action for Claude Code to refine
            dest = NEEDS_ACTION / filepath.name
            shutil.move(str(filepath), str(dest))
            log.info(f"Moved draft to Needs_Action/: {filepath.name}")

            audit_log("local_sync", "draft_received", {
                "file": filepath.name,
                "source": "cloud_agent",
            })
            processed += 1

        except Exception as e:
            log.error(f"Error processing {filepath.name}: {e}")

    # Process any other update files (non-email)
    for filepath in UPDATES.glob("*.md"):
        try:
            dest = NEEDS_ACTION / filepath.name
            shutil.move(str(filepath), str(dest))
            log.info(f"Moved update to Needs_Action/: {filepath.name}")
            processed += 1
        except Exception as e:
            log.error(f"Error processing {filepath.name}: {e}")

    return processed


def process_signals():
    """Read and process signal files from cloud."""
    if not SIGNALS.exists():
        return

    for filepath in SIGNALS.glob("*.json"):
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            signal_type = data.get("type", "unknown")

            if signal_type == "health_alert":
                unhealthy = data.get("unhealthy", [])
                log.warning(f"Cloud health alert: {unhealthy}")
                # Create a notification in Needs_Action
                alert_file = NEEDS_ACTION / f"CLOUD_ALERT_{datetime.now():%Y%m%d_%H%M%S}.md"
                alert_content = f"""---
type: cloud_alert
generated: {datetime.now().isoformat()}
priority: high
status: pending
---

# Cloud Health Alert

The following services are unhealthy on the cloud VM:

{chr(10).join(f'- **{s}**' for s in unhealthy)}

## Suggested Actions
- [ ] SSH into cloud VM and check logs
- [ ] Restart affected services: `sudo systemctl restart <service>`
- [ ] Check Docker containers: `docker ps`
"""
                alert_file.write_text(alert_content, encoding="utf-8")

            elif signal_type == "new_draft":
                log.info(f"New draft signal: {data.get('details', {}).get('draft_file', 'unknown')}")

            # Archive processed signal
            archive_dir = SIGNALS / "processed"
            archive_dir.mkdir(exist_ok=True)
            shutil.move(str(filepath), str(archive_dir / filepath.name))

        except Exception as e:
            log.error(f"Error processing signal {filepath.name}: {e}")


def sync_once():
    """Perform one sync cycle."""
    log.info("--- Sync cycle ---")

    # Pull from remote
    if git_pull():
        # Process updates from cloud
        count = process_updates()
        if count:
            log.info(f"Processed {count} update(s) from cloud")

        # Process signals
        process_signals()
    else:
        log.warning("Pull failed, skipping update processing")


def main():
    parser = argparse.ArgumentParser(description="WEBXES Tech Local Sync")
    parser.add_argument("--watch", action="store_true", help="Continuous sync loop")
    args = parser.parse_args()

    ensure_dirs()

    if args.watch:
        log.info("=== WEBXES Tech Local Sync (watch mode) ===")
        log.info(f"Syncing every {SYNC_INTERVAL}s")
        try:
            while True:
                sync_once()
                time.sleep(SYNC_INTERVAL)
        except KeyboardInterrupt:
            log.info("Local Sync stopped.")
    else:
        sync_once()
        log.info("Sync complete.")


if __name__ == "__main__":
    main()
