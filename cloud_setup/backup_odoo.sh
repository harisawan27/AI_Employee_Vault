#!/usr/bin/env bash
# WEBXES Tech — Odoo Database Backup
# Daily pg_dump with 30-day rotation.
#
# Usage:
#   bash cloud_setup/backup_odoo.sh              # Run backup now
#   bash cloud_setup/backup_odoo.sh --install    # Install daily cron job

set -euo pipefail

BACKUP_DIR="/opt/ai_employee_vault/backups/odoo"
RETENTION_DAYS=30
DB_CONTAINER="odoo_fte_db"
DB_NAME="odoo_fte"
DB_USER="odoo"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

if [ "${1:-}" = "--install" ]; then
    echo "Installing daily backup cron job..."
    SCRIPT_PATH="$(realpath "$0")"
    # Run at 2 AM daily
    (crontab -l 2>/dev/null || true; echo "0 2 * * * bash ${SCRIPT_PATH} >> /opt/ai_employee_vault/Logs/backup.log 2>&1") | sort -u | crontab -
    echo "Cron job installed: daily at 2 AM"
    echo "Logs: /opt/ai_employee_vault/Logs/backup.log"
    exit 0
fi

echo "[$(date)] Starting Odoo backup..."

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Dump the database
BACKUP_FILE="${BACKUP_DIR}/odoo_${TIMESTAMP}.sql.gz"
docker exec "${DB_CONTAINER}" pg_dump -U "${DB_USER}" "${DB_NAME}" | gzip > "${BACKUP_FILE}"

if [ -f "${BACKUP_FILE}" ]; then
    SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "[$(date)] Backup created: ${BACKUP_FILE} (${SIZE})"
else
    echo "[$(date)] ERROR: Backup failed!"
    exit 1
fi

# Rotate old backups (delete older than RETENTION_DAYS)
DELETED=$(find "${BACKUP_DIR}" -name "odoo_*.sql.gz" -mtime +${RETENTION_DAYS} -print -delete | wc -l)
if [ "${DELETED}" -gt 0 ]; then
    echo "[$(date)] Cleaned up ${DELETED} backup(s) older than ${RETENTION_DAYS} days"
fi

# Summary
TOTAL=$(ls -1 "${BACKUP_DIR}"/odoo_*.sql.gz 2>/dev/null | wc -l)
echo "[$(date)] Backup complete. Total backups: ${TOTAL}"
