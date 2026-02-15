@echo off
REM WEBXES Tech — Local AI Employee Startup
REM Syncs from cloud, checks Odoo, starts approval watcher

echo ============================================
echo   WEBXES Tech - AI Employee Starting...
echo ============================================
echo.

REM 1. Pull latest from GitHub
echo [1/4] Syncing from cloud...
python local_sync.py
if errorlevel 1 (
    echo WARNING: Sync failed, continuing with local state...
)
echo.

REM 2. Check if Odoo Docker is running
echo [2/4] Checking Odoo Docker...
docker ps --filter "name=odoo_fte" --format "{{.Names}}: {{.Status}}" 2>nul
if errorlevel 1 (
    echo Odoo Docker not running. Starting...
    docker compose -f Odoo_FTE/docker-compose.yml up -d
) else (
    echo Odoo containers are running.
)
echo.

REM 3. Start approval watcher in background
echo [3/4] Starting Approval Watcher...
start "ApprovalWatcher" /min python approval_watcher.py
echo Approval Watcher started (minimized).
echo.

REM 4. Ready
echo [4/4] Setup complete!
echo.
echo ============================================
echo   AI Employee is ready!
echo   - Approval Watcher: running
echo   - Local Sync: completed
echo   - Odoo: checked
echo.
echo   Use Claude Code to process inbox:
echo     /process-inbox
echo     /reason-and-plan
echo ============================================
echo.
pause
