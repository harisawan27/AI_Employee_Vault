# WEBXES Tech AI Employee — Architecture

## Dual-Zone Cloud Architecture (Platinum)

```
CLOUD VM (Oracle Cloud Free Tier - 24/7)          LOCAL WINDOWS (on-demand)
┌──────────────────────────────────────┐    ┌──────────────────────────────────┐
│  gmail_watcher.py (systemd)          │    │  Claude Code (AI reasoning)      │
│  orchestrator.py  (systemd)          │    │  approval_watcher.py (sends)     │
│  cloud_agent.py   (systemd)          │    │  local_sync.py (git pull)        │
│  git_sync_cloud.py (systemd)         │    │  Social media posters            │
│  health_monitor.py (systemd)         │    │  (LinkedIn/FB/IG/Twitter)        │
│  Odoo Docker (Nginx + HTTPS)         │    │  start_local_ai.bat              │
│                                      │    │                                  │
│  Creates: template drafts            │    │  Refines: AI-powered responses   │
│  Zone: In_Progress/cloud/            │    │  Zone: In_Progress/local/        │
│  Output: Updates/ + Signals/         │    │  Executes: email send, social    │
└──────────────┬───────────────────────┘    └───────────────┬──────────────────┘
               │                                            │
               │          ┌─────────────────┐               │
               └──────────┤   GitHub Repo   ├───────────────┘
                          │   (vault sync)  │
                          └─────────────────┘
                          Cloud pushes every 5 min
                          Local pulls on startup
```

### Sync Protocol
1. Cloud: `git pull --rebase && git add . && git commit && git push` (every 5 min)
2. Local: `git pull --rebase` on startup + `local_sync.py` processes Updates/
3. Conflict resolution: rebase preferred, falls back to merge
4. Only markdown/state files sync — secrets never leave their zone

### Claim-by-Move Rule
- Cloud agent moves email from `Needs_Action/` → `In_Progress/cloud/` to claim it
- Local agent would move to `In_Progress/local/` — prevents double-work
- After processing, files move to `Done/`

### Security Boundaries
- Cloud: No browser sessions, no social media cookies, DRY_RUN=true always
- Local: Has credentials, can send emails, post to social media
- Secrets: `.env` never committed, credentials outside vault

---

## System Diagram (Full)

```
┌─────────────────────────────────────────────────────────────────┐
│                        PERCEPTION LAYER                         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ Gmail Watcher │  │ Filesystem Watch │  │   Orchestrator   │  │
│  │ (polling)     │  │ (watchdog)       │  │ (schedule)       │  │
│  └──────┬───────┘  └────────┬─────────┘  └────────┬─────────┘  │
│         │                   │                      │            │
│         └───────────────────┼──────────────────────┘            │
│                             ▼                                   │
│                    ┌────────────────┐                            │
│                    │  Needs_Action/ │                            │
│                    └────────┬───────┘                            │
└─────────────────────────────┼───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        REASONING LAYER                          │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Claude Code + Agent Skills (10)               │ │
│  │                                                            │ │
│  │  /process-inbox    /ceo-briefing     /update-dashboard     │ │
│  │  /linkedin-post    /send-email       /request-approval     │ │
│  │  /reason-and-plan  /social-post      /social-summary       │ │
│  │  /accounting-audit                                         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────┐  ┌─────────────────────────────────────┐ │
│  │ Ralph Wiggum Loop│  │  Company Handbook (autonomy rules)  │ │
│  │ (hooks)          │  │  AUTO / APPROVE / DENY levels       │ │
│  └──────────────────┘  └─────────────────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ACTION LAYER                            │
│                                                                 │
│  ┌───────────────────┐  ┌─────────────────────────────────┐    │
│  │ Approval Workflow  │  │      Direct Execution           │    │
│  │                    │  │                                  │    │
│  │ Pending_Approval/  │  │  Gmail MCP (send email)         │    │
│  │   ├── email/       │  │  LinkedIn Poster (Playwright)   │    │
│  │   ├── payments/    │  │  Social Media Poster (FB/IG/TW) │    │
│  │   └── social_media/│  │  Odoo MCP (invoices, P&L, etc.) │    │
│  │                    │  │                                  │    │
│  │  CEO: Approve/     │  └─────────────────────────────────┘    │
│  │       Reject       │                                         │
│  └────────┬──────────┘                                          │
│           ▼                                                     │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │   Approved/    │  │   Rejected/    │  │      Done/       │  │
│  └────────────────┘  └────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE                             │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │  retry_handler   │  │  audit_logger    │  │  Dashboard   │  │
│  │  @retry + CB     │  │  audit.jsonl     │  │  Dashboard.md│  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### Cloud Services (Platinum)

| Component | File | Purpose |
|-----------|------|---------|
| Cloud Agent | `cloud_agent.py` | Polls Needs_Action/, claims emails, creates template drafts in Updates/ |
| Git Sync | `cloud_setup/git_sync_cloud.py` | Auto git pull/commit/push every 5 min |
| Health Monitor | `cloud_setup/health_monitor.py` | Checks systemd + Docker every 5 min, alerts via Signals/ |
| Local Sync | `local_sync.py` | Pulls from GitHub, processes Updates/ and Signals/ |
| Config | `config.py` | Central config: IS_CLOUD/IS_LOCAL detection, all paths |

### Watchers (Perception)

| Component | File | Trigger | Output |
|-----------|------|---------|--------|
| Gmail Watcher | `gmail_watcher.py` | Polls Gmail every 60s | Drops `.md` files into `Needs_Action/` |
| Filesystem Watcher | `filesystem_watcher.py` | Watchdog on `Inbox/` folder | Moves files to `Needs_Action/` |
| Orchestrator | `orchestrator.py` | Schedule (Mon 8AM, Fri 5PM) | Creates task files in `Needs_Action/` |

### Agent Skills (Reasoning)

Claude Code reads task files from `Needs_Action/`, applies Company Handbook rules, and executes the appropriate skill. Skills are defined as `SKILL.md` files in `.claude/skills/`.

The **Ralph Wiggum Loop** (`.claude/hooks/ralph_wiggum.py`) enables autonomous iteration: after each Claude Code response, it checks `ralph_state.json` and re-prompts if a task is still active.

### Execution (Action)

| Component | File | Purpose |
|-----------|------|---------|
| Approval Watcher | `approval_watcher.py` | Polls Approved/Rejected folders, executes actions |
| LinkedIn Poster | `linkedin_poster.py` | Playwright automation for LinkedIn |
| Social Media Poster | `social_media_poster.py` | Playwright automation for Facebook, Instagram, Twitter |
| Gmail MCP | `@gongrzhe/server-gmail-autoauth-mcp` | Email send/read via MCP |
| Odoo MCP | `Odoo_FTE/odoo_mcp_server.py` | ERP data access via MCP (7 tools) |

### Infrastructure

| Component | File | Purpose |
|-----------|------|---------|
| Retry Handler | `retry_handler.py` | `@retry` decorator (exponential backoff + jitter), `CircuitBreaker` class |
| Audit Logger | `audit_logger.py` | JSON Lines audit trail (`Logs/audit.jsonl`), queryable by category/date |
| Dashboard | `Dashboard.md` | Real-time vault status (updated by `/update-dashboard` skill) |

## Data Flows

### Cloud Email Flow (Platinum)
```
Gmail → Gmail Watcher (cloud) → Needs_Action/EMAIL_*.md
  → Cloud Agent claims: move to In_Progress/cloud/
  → Template draft created: Updates/EMAIL_DRAFT_*.md
  → Signal created: Signals/new_draft_*.json
  → Git sync pushes to GitHub
  → Local sync pulls + moves draft to Needs_Action/
  → Claude Code refines draft
  → CEO approves → Approved/email/
  → Approval Watcher sends via Gmail MCP → Done/
```

### Email Flow
```
Gmail → Gmail Watcher → Needs_Action/ → /process-inbox
  → Known contact? AUTO: reply directly via Gmail MCP
  → Unknown?       APPROVE: → Pending_Approval/email/ → CEO approves → Approved/email/
                              → Approval Watcher → Gmail MCP → Done/
```

### Social Media Flow
```
CEO request → /social-post <platform> <topic>
  → Generate content → Pending_Approval/social_media/ (with platform: field)
  → CEO approves → Approved/social_media/
  → Approval Watcher reads platform from frontmatter
    → linkedin: LinkedInPoster
    → facebook/instagram/twitter: SocialMediaPoster
  → Done/
```

### Weekly Audit Flow
```
Friday 5PM → Orchestrator → WEEKLY_AUDIT task in Needs_Action/
  → Ralph Wiggum Loop → /accounting-audit skill
    → Odoo MCP: invoices, bills, payments, P&L, balance sheet
    → audit.jsonl: AI activity summary
  → Plans/Weekly_Audit_<DATE>.md
```

## Error Recovery

### Retry Handler (`@retry`)
- Exponential backoff: delay = min(base_delay * 2^attempt, max_delay)
- Random jitter: 0 to 50% of calculated delay
- Default: 3 retries, 1s base delay, 60s max delay
- Catches configurable exception types

### Circuit Breaker
- **CLOSED** → normal operation, counts failures
- **OPEN** → after 5 failures, blocks all calls for 300s, raises `ConnectionError`
- **HALF_OPEN** → after recovery timeout, allows one test call
- Success in HALF_OPEN → CLOSED; failure → back to OPEN
- Thread-safe with `threading.Lock`

### Active Circuit Breakers
| Name | Used By | Threshold | Recovery |
|------|---------|-----------|----------|
| `odoo` | Odoo MCP Server | 5 failures | 300s |
| `gmail` | Approval Watcher (email send) | 5 failures | 300s |
| `social_media` | Approval Watcher (social post) | 5 failures | 300s |

## Security

- **Credentials outside vault:** Gmail creds at `C:\Users\lenovo\.config\webxes\`
- **DRY_RUN default:** `.env` ships with `DRY_RUN=true` — must explicitly disable
- **Human-in-the-loop:** All AI-generated external actions route through Pending_Approval
- **24-hour expiry:** Unapproved items auto-expire to Rejected
- **Audit trail:** Every action logged with timestamp, category, status, error details
- **No secrets in vault:** `.env` excluded from version control

## Lessons Learned

1. **Python version mismatch:** Windows has Python 3.11 and 3.13 installed. `python` points to 3.13 but `pip` to 3.11. Always use `python -m pip install` to ensure correct target.
2. **Playwright sessions:** Persistent cookie storage avoids re-login. First run must be non-headless for manual login, subsequent runs can be headless.
3. **MCP stdio protocol:** JSON-RPC over stdin/stdout. Must handle `notifications/initialized` (no response required) separately from regular requests.
4. **Frontmatter parsing:** Simple `key: value` parsing is sufficient — no need for a YAML library dependency.
5. **Circuit breaker granularity:** One breaker per external service, not per operation. Shared state correctly reflects service health.
