#!/usr/bin/env bash
# WEBXES Tech — Oracle Cloud VM Provisioning Script
# Run as root on a fresh Ubuntu 22.04 VM (Oracle Cloud Free Tier E2.1.Micro)
#
# Usage: sudo bash provision_vm.sh

set -euo pipefail

echo "=== WEBXES Tech Cloud VM Provisioning ==="

# 1. System updates
echo "[1/8] Updating system packages..."
apt-get update && apt-get upgrade -y

# 2. Install Python 3, pip, git, and essentials
echo "[2/8] Installing Python, git, and essentials..."
apt-get install -y python3 python3-pip python3-venv git curl ufw

# 3. Install Docker
echo "[3/8] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    usermod -aG docker ubuntu
fi

# 4. Install Docker Compose plugin
echo "[4/8] Installing Docker Compose..."
apt-get install -y docker-compose-plugin || true

# 5. Install Nginx
echo "[5/8] Installing Nginx..."
apt-get install -y nginx
systemctl enable nginx

# 6. Install Certbot for HTTPS
echo "[6/8] Installing Certbot..."
apt-get install -y certbot python3-certbot-nginx

# 7. Firewall setup
echo "[7/8] Configuring firewall..."
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
# Block direct Odoo access from outside (only via Nginx reverse proxy)
ufw deny 8069/tcp
ufw --force enable

# 8. Create cloud marker file (used by config.py to detect cloud environment)
echo "[8/8] Creating cloud marker..."
echo "webxes-cloud-vm" > /etc/webxes_cloud_marker
chmod 644 /etc/webxes_cloud_marker

# Create vault directory
VAULT_DIR="/opt/ai_employee_vault"
mkdir -p "$VAULT_DIR"
chown ubuntu:ubuntu "$VAULT_DIR"

# Create log directory
mkdir -p "$VAULT_DIR/Logs"
chown ubuntu:ubuntu "$VAULT_DIR/Logs"

echo ""
echo "=== Provisioning Complete ==="
echo ""
echo "Next steps:"
echo "  1. Clone your repo:"
echo "     su - ubuntu"
echo "     git clone <your-repo-url> $VAULT_DIR"
echo ""
echo "  2. Install Python dependencies:"
echo "     cd $VAULT_DIR"
echo "     python3 -m pip install -r requirements.txt"
echo ""
echo "  3. Copy and configure .env:"
echo "     cp cloud_setup/.env.cloud.template .env"
echo "     nano .env  # Set Odoo password, domain, etc."
echo ""
echo "  4. Start Odoo:"
echo "     docker compose -f cloud_setup/docker-compose.odoo.yml up -d"
echo ""
echo "  5. Install systemd services:"
echo "     sudo bash cloud_setup/install_services.sh"
echo ""
echo "  6. (Optional) Setup HTTPS for Odoo:"
echo "     sudo bash cloud_setup/setup_odoo_https.sh your-domain.com"
