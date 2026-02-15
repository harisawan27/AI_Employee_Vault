"""
WEBXES Tech — Cloud Health Monitor

Checks systemd services and Docker containers every 5 minutes.
Logs to health.jsonl and creates alert signals when services are down.

Usage:
    python cloud_setup/health_monitor.py          # Run monitoring loop
    python cloud_setup/health_monitor.py --once    # Check once and exit
"""

import argparse
import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Add vault root to path
VAULT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VAULT_ROOT))

from config import VAULT_PATH, LOGS, SIGNALS, ensure_dirs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS / "health_monitor.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("health_monitor")

HEALTH_FILE = LOGS / "health.jsonl"
CHECK_INTERVAL = 300  # 5 minutes

SYSTEMD_SERVICES = [
    # "webxes-gmail-watcher",  # Disabled: Gmail runs locally only
    "webxes-orchestrator",
    "webxes-cloud-agent",
    "webxes-sync",
]

DOCKER_CONTAINERS = [
    "odoo_fte_web",
    "odoo_fte_db",
]


def check_systemd(service: str) -> dict:
    """Check if a systemd service is active."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service],
            capture_output=True, text=True, timeout=10
        )
        status = result.stdout.strip()
        return {"service": service, "type": "systemd", "status": status, "healthy": status == "active"}
    except Exception as e:
        return {"service": service, "type": "systemd", "status": "error", "healthy": False, "error": str(e)}


def check_docker(container: str) -> dict:
    """Check if a Docker container is running."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Status}}", container],
            capture_output=True, text=True, timeout=10
        )
        status = result.stdout.strip()
        return {"container": container, "type": "docker", "status": status, "healthy": status == "running"}
    except Exception as e:
        return {"container": container, "type": "docker", "status": "error", "healthy": False, "error": str(e)}


def run_health_check() -> dict:
    """Run all health checks and return results."""
    now = datetime.now()
    results = {
        "timestamp": now.isoformat(),
        "services": [],
        "containers": [],
        "all_healthy": True,
    }

    for svc in SYSTEMD_SERVICES:
        check = check_systemd(svc)
        results["services"].append(check)
        if not check["healthy"]:
            results["all_healthy"] = False

    for ctr in DOCKER_CONTAINERS:
        check = check_docker(ctr)
        results["containers"].append(check)
        if not check["healthy"]:
            results["all_healthy"] = False

    # Log to health.jsonl
    HEALTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HEALTH_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(results) + "\n")

    # Create alert signal if something is down
    if not results["all_healthy"]:
        unhealthy = []
        for s in results["services"]:
            if not s["healthy"]:
                unhealthy.append(s.get("service", "unknown"))
        for c in results["containers"]:
            if not c["healthy"]:
                unhealthy.append(c.get("container", "unknown"))

        signal_file = SIGNALS / f"health_alert_{now.strftime('%Y%m%d_%H%M%S')}.json"
        signal_data = {
            "type": "health_alert",
            "timestamp": now.isoformat(),
            "unhealthy": unhealthy,
            "details": results,
        }
        SIGNALS.mkdir(parents=True, exist_ok=True)
        signal_file.write_text(json.dumps(signal_data, indent=2), encoding="utf-8")
        log.warning(f"Health alert: {unhealthy}")

    return results


def main():
    parser = argparse.ArgumentParser(description="WEBXES Tech Health Monitor")
    parser.add_argument("--once", action="store_true", help="Check once and exit")
    args = parser.parse_args()

    ensure_dirs()

    if args.once:
        results = run_health_check()
        healthy = "ALL HEALTHY" if results["all_healthy"] else "ISSUES DETECTED"
        log.info(f"Health check: {healthy}")
        print(json.dumps(results, indent=2))
        return

    log.info("=== WEBXES Tech Health Monitor Starting ===")
    log.info(f"Checking every {CHECK_INTERVAL}s")

    try:
        while True:
            results = run_health_check()
            status = "OK" if results["all_healthy"] else "ALERT"
            log.info(f"Health check: {status}")
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        log.info("Health Monitor stopped.")


if __name__ == "__main__":
    main()
