# WEBXES Tech — AI Employee Vault

Personal AI Employee built on Claude Code, using an Obsidian vault as its central nervous system. Implements the Perception → Reasoning → Action pipeline for autonomous business operations.

**Tier:** Gold (10/12 deliverables complete at Silver; Gold adds social media, Odoo MCP, audit, resilience)

## Quick Start

```bash
# 1. Install Python dependencies
python -m pip install python-dotenv schedule watchdog playwright Pillow mcp

# 2. Install Playwright browsers
python -m playwright install chromium

# 3. Start Odoo (Docker required)
docker compose -f Odoo_FTE/docker-compose.yml up -d

# 4. Configure environment
#    Edit .env with your credentials (Gmail, Odoo, session paths)

# 5. Start watchers (each in its own terminal)
python run_gmail_watcher.py
python run_filesystem_watcher.py
python approval_watcher.py

# 6. Start orchestrator (scheduler)
python orchestrator.py
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
├── Needs_Action/           # Inbox — unprocessed tasks
├── Pending_Approval/       # Human-in-the-loop approval queue
│   ├── email/
│   ├── payments/
│   └── social_media/
├── Approved/               # CEO-approved actions (auto-executed)
├── Rejected/               # CEO-rejected actions
├── Done/                   # Completed items archive
├── Plans/                  # Generated reports (briefings, audits, summaries)
├── Logs/                   # audit.jsonl + watcher logs
├── Odoo_FTE/               # Odoo Docker + MCP server
├── Company_Handbook.md     # Autonomy rules, brand voice, contacts
├── Dashboard.md            # Real-time vault status
├── orchestrator.py         # Scheduler (CEO Briefing Mon 8AM, Audit Fri 5PM)
├── approval_watcher.py     # Monitors Approved/Rejected, executes actions
├── gmail_watcher.py        # Gmail polling → Needs_Action
├── filesystem_watcher.py   # File drop watcher → Needs_Action
├── linkedin_poster.py      # LinkedIn Playwright automation
├── social_media_poster.py  # FB/IG/Twitter Playwright automation
├── retry_handler.py        # @retry decorator + CircuitBreaker
└── audit_logger.py         # Structured JSON Lines audit trail
```

## Key Features

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
