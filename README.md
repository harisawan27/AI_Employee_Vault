# WEBXES Tech — AI Employee Vault

Personal AI Employee built on Claude Code, using an Obsidian vault as its central nervous system. Implements the Perception → Reasoning → Action pipeline for autonomous business operations.

**Tier:** Platinum (Cloud 24/7 deployment, Git vault sync, dual-zone architecture)

## Quick Start (Local)

```bash
# 1. Install Python dependencies
python -m pip install -r requirements.txt

# 2. Install Playwright browsers
python -m playwright install chromium

# 3. Start Odoo (Docker required)
docker compose -f Odoo_FTE/docker-compose.yml up -d

# 4. Configure environment
#    Edit .env with your credentials (Gmail, Odoo, session paths)

# 5. One-click startup (syncs from cloud, starts watchers)
start_local_ai.bat

# Or start components individually:
python run_gmail_watcher.py
python run_filesystem_watcher.py
python approval_watcher.py
python orchestrator.py
```

## Cloud Setup (Oracle Cloud Free Tier)

```bash
# 1. Provision the VM (Ubuntu 22.04)
sudo bash cloud_setup/provision_vm.sh

# 2. Clone repo and configure
git clone <your-repo-url> /opt/ai_employee_vault
cp cloud_setup/.env.cloud.template .env
nano .env  # Set Odoo password, etc.

# 3. Start Odoo
docker compose -f cloud_setup/docker-compose.odoo.yml up -d

# 4. Install systemd services (Gmail watcher, orchestrator, cloud agent, sync, health monitor)
sudo bash cloud_setup/install_services.sh

# 5. (Optional) Setup HTTPS for Odoo
sudo bash cloud_setup/setup_odoo_https.sh your-domain.com

# 6. (Optional) Setup daily Odoo backups
bash cloud_setup/backup_odoo.sh --install
```

## 10 Agent Skills

| Skill | Description |
|-------|-------------|
| `/process-inbox` | Triage Needs_Action items per Company Handbook |
| `/ceo-briefing` | Monday Morning CEO Briefing from revenue data |
| `/update-dashboard` | Refresh Dashboard.md with vault state |
| `/linkedin-post` | Generate LinkedIn post, route through approval |
| `/send-email` | Draft/send emails via Gmail MCP with approval guardrails |
| `/request-approval` | Create formatted approval request files |
| `/reason-and-plan` | Full Perception → Reasoning → Action loop |
| `/social-post` | Multi-platform post (LinkedIn, Facebook, Instagram, Twitter) |
| `/social-summary` | Social media performance report from engagement + audit data |
| `/accounting-audit` | Weekly financial audit from Odoo + AI activity from audit log |

## MCP Servers

| Server | Transport | Description |
|--------|-----------|-------------|
| `gmail` | npx stdio | Gmail read/send via `@gongrzhe/server-gmail-autoauth-mcp` |
| `odoo` | Python stdio | Odoo ERP — 7 tools (invoices, bills, payments, P&L, balance sheet, create invoice, weekly revenue) |

## Folder Structure

```
AI_Employee_Vault/
├── .claude/
│   ├── hooks/              # Ralph Wiggum loop hook
│   ├── skills/             # 10 SKILL.md files
│   └── mcp.json            # MCP server config (Gmail + Odoo)
├── cloud_setup/            # Platinum: cloud VM deployment
│   ├── provision_vm.sh     # VM setup script
│   ├── install_services.sh # systemd service installer
│   ├── docker-compose.odoo.yml
│   ├── nginx_odoo.conf     # Reverse proxy config
│   ├── setup_odoo_https.sh # Certbot + Nginx HTTPS
│   ├── backup_odoo.sh      # Daily pg_dump with rotation
│   ├── git_sync_cloud.py   # Auto git commit/push every 5 min
│   ├── health_monitor.py   # systemd + Docker health checks
│   └── webxes-*.service    # 5 systemd unit files
├── tests/
│   └── platinum_demo.py    # E2E demo test
├── Needs_Action/           # Inbox — unprocessed tasks
├── Pending_Approval/       # Human-in-the-loop approval queue
├── Approved/               # CEO-approved actions (auto-executed)
├── Rejected/               # CEO-rejected actions
├── Done/                   # Completed items archive
├── In_Progress/            # Platinum: claim-by-move work zones
│   ├── cloud/              # Files claimed by cloud agent
│   └── local/              # Files claimed by local agent
├── Updates/                # Platinum: cloud drafts for local refinement
├── Signals/                # Platinum: cross-zone notifications
├── Plans/                  # Generated reports
├── Logs/                   # audit.jsonl + watcher logs
├── Odoo_FTE/               # Odoo Docker + MCP server
├── config.py               # Central config: zone detection, paths
├── cloud_agent.py          # Platinum: template draft generator (cloud)
├── local_sync.py           # Platinum: pull + merge cloud updates
├── start_local_ai.bat      # Platinum: Windows one-click startup
├── orchestrator.py         # Scheduler (CEO Briefing + Weekly Audit)
├── approval_watcher.py     # Monitors Approved/Rejected (local only)
├── gmail_watcher.py        # Gmail polling → Needs_Action
├── filesystem_watcher.py   # File drop watcher → Needs_Action
├── linkedin_poster.py      # LinkedIn Playwright automation
├── social_media_poster.py  # FB/IG/Twitter Playwright automation
├── retry_handler.py        # @retry decorator + CircuitBreaker
├── audit_logger.py         # Structured JSON Lines audit trail
└── requirements.txt        # Python dependencies
```

## Key Features

- **Cloud 24/7:** Gmail watcher, orchestrator, and cloud agent run on Oracle Cloud Free Tier VM
- **Dual-Zone Architecture:** Cloud creates drafts, local Claude Code refines and sends
- **Git Vault Sync:** Cloud auto-commits every 5 min → GitHub → local pulls on startup
- **Claim-by-Move:** `In_Progress/cloud/` and `In_Progress/local/` prevent double-work
- **Health Monitoring:** systemd + Docker health checks with alert signals
- **Human-in-the-Loop:** All AI-generated content routes through Pending_Approval before execution
- **Resilience:** Exponential backoff with jitter (`@retry`), circuit breakers for external services
- **Audit Trail:** Every action logged to `Logs/audit.jsonl` — queryable by category, date, status
- **Multi-Platform Social:** LinkedIn, Facebook, Instagram, Twitter via Playwright with persistent sessions
- **Odoo ERP Integration:** Full accounting access (invoices, bills, payments, P&L, balance sheet)
- **Scheduled Automation:** CEO Briefing (Monday 8AM), Weekly Audit (Friday 5PM)
- **Ralph Wiggum Loop:** Autonomous task processing via Claude Code hooks

## Environment Variables

See `.env` for all configuration. Key variables:

| Variable | Purpose |
|----------|---------|
| `VAULT_PATH` | Root path to this vault |
| `DRY_RUN` | `true` to simulate actions without executing |
| `ODOO_URL` / `ODOO_DB` / `ODOO_USER` / `ODOO_PASSWORD` | Odoo connection |
| `GMAIL_CREDENTIALS_PATH` / `GMAIL_TOKEN_PATH` | Gmail API credentials |
| `LINKEDIN_SESSION_PATH` | LinkedIn Playwright session cookies |
| `FACEBOOK_SESSION_PATH` | Facebook Playwright session cookies |
| `INSTAGRAM_SESSION_PATH` | Instagram Playwright session cookies |
| `TWITTER_SESSION_PATH` | Twitter/X Playwright session cookies |
