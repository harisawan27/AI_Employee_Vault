#!/usr/bin/env bash
# WEBXES Tech — Install systemd services on cloud VM
# Run as root: sudo bash cloud_setup/install_services.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# NOTE: gmail-watcher is NOT included by default.
# Gmail OAuth requires a browser for initial login, which cloud VMs don't have.
# Gmail watcher should run locally. Cloud processes emails via git sync only.
# To enable it, manually copy token.json to the cloud and uncomment below.
SERVICES=(
    # webxes-gmail-watcher   # Disabled: requires OAuth token (run locally instead)
    webxes-orchestrator
    webxes-cloud-agent
    webxes-sync
    webxes-health-monitor
    webxes-api
)

echo "=== Installing WEBXES Tech systemd services ==="

# Ensure log directory exists
mkdir -p /opt/ai_employee_vault/Logs

for svc in "${SERVICES[@]}"; do
    echo "Installing ${svc}.service..."
    cp "${SCRIPT_DIR}/${svc}.service" /etc/systemd/system/
done

echo "Reloading systemd daemon..."
systemctl daemon-reload

for svc in "${SERVICES[@]}"; do
    echo "Enabling and starting ${svc}..."
    systemctl enable "$svc"
    systemctl start "$svc"
done

echo ""
echo "=== All services installed ==="
echo ""
echo "Check status:"
for svc in "${SERVICES[@]}"; do
    echo "  systemctl status ${svc}"
done
echo ""
echo "Or check all at once:"
echo "  systemctl status webxes-*"
