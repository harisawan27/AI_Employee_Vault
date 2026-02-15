#!/usr/bin/env bash
# WEBXES Tech — Setup HTTPS for Odoo via Nginx + Certbot
# Usage: sudo bash cloud_setup/setup_odoo_https.sh your-domain.com

set -euo pipefail

if [ $# -eq 0 ]; then
    echo "Usage: sudo bash setup_odoo_https.sh <domain>"
    echo "Example: sudo bash setup_odoo_https.sh odoo.webxes.com"
    exit 1
fi

DOMAIN="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Setting up HTTPS for Odoo at ${DOMAIN} ==="

# 1. Create Nginx config from template
echo "[1/4] Configuring Nginx..."
sed "s/DOMAIN_PLACEHOLDER/${DOMAIN}/g" "${SCRIPT_DIR}/nginx_odoo.conf" > /etc/nginx/sites-available/odoo

# 2. Enable the site
ln -sf /etc/nginx/sites-available/odoo /etc/nginx/sites-enabled/odoo

# Remove default site if it exists
rm -f /etc/nginx/sites-enabled/default

# 3. Get SSL certificate (temporarily allow HTTP for validation)
echo "[2/4] Obtaining SSL certificate..."
# First, create a temporary HTTP-only config for cert validation
cat > /etc/nginx/sites-available/odoo-temp << EOF
server {
    listen 80;
    server_name ${DOMAIN};
    location / {
        return 200 'OK';
    }
}
EOF
ln -sf /etc/nginx/sites-available/odoo-temp /etc/nginx/sites-enabled/odoo
nginx -t && systemctl reload nginx

certbot --nginx -d "${DOMAIN}" --non-interactive --agree-tos --email admin@webxes.com

# 4. Restore full Nginx config with SSL
echo "[3/4] Applying full Nginx config with SSL..."
sed "s/DOMAIN_PLACEHOLDER/${DOMAIN}/g" "${SCRIPT_DIR}/nginx_odoo.conf" > /etc/nginx/sites-available/odoo
rm -f /etc/nginx/sites-available/odoo-temp

nginx -t && systemctl reload nginx

# 5. Setup auto-renewal
echo "[4/4] Configuring certificate auto-renewal..."
systemctl enable certbot.timer
systemctl start certbot.timer

echo ""
echo "=== HTTPS Setup Complete ==="
echo "Odoo is now available at: https://${DOMAIN}"
echo "Certificate auto-renewal is enabled via certbot.timer"
