---
name: update-dashboard
description: Refresh Dashboard.md with the current state of the vault. Scans /Needs_Action, /Pending_Approval, /Done, and /Logs to build an accurate real-time status view. Use when the dashboard is stale or after processing inbox items.
user-invocable: true
---

# Update Dashboard — WEBXES Tech

Refresh `Dashboard.md` with the current vault state.

## Process

1. **Scan `/Needs_Action/`** — Count and list pending items by type
2. **Scan `/Pending_Approval/`** — List items awaiting CEO decision with expiry times
3. **Scan `/Done/`** — Get the 10 most recent completed items (by file modification time)
4. **Read current `Dashboard.md`** to preserve structure
5. **Update each section** with fresh data

## Sections to Update

### System Status
Check which components are deployed:
- AI Employee: Running / Stopped
- Gmail Watcher: Check if `gmail_watcher.log` has recent entries
- Orchestrator: Check if `orchestrator.log` has recent entries

### Pending Actions
List all files in `/Needs_Action/` with:
- Type (from frontmatter or filename prefix)
- Source (from/sender if available)
- Summary (first line of content)
- Priority (from frontmatter, default: normal)
- Created date

### Awaiting Approval
List all files in `/Pending_Approval/` (including subdirectories) with:
- Action type
- Target
- Amount (if financial)
- Expiry time

### Recent Activity
List the 10 most recently modified files in `/Done/` with:
- Timestamp (modification time)
- Action summary (from filename or frontmatter)
- Result: Success

### Financial Summary
If a `CEO_Briefing` file exists in `/Plans/`, pull latest revenue figures.

## Rules

- **Single-writer rule**: Only the local agent updates Dashboard.md
- Preserve the YAML frontmatter, update `last_updated` and `updated_by`
- Keep the exact Markdown table structure — only change cell values
- If a section has no data, show the "no items" placeholder row
