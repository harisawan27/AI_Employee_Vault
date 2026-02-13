---
name: process-inbox
description: Triage and process items in /Needs_Action. Reads each pending file, classifies it by type (email, task, briefing request), and takes action per Company Handbook autonomy rules. Use this when the inbox needs processing or when a watcher drops new files.
user-invocable: true
argument-hint: [optional: specific filename]
---

# Process Inbox — WEBXES Tech AI Employee

Triage all pending items in `/Needs_Action/` following Company Handbook rules.

## Workflow

1. **Read Company Handbook** (`Company_Handbook.md`) to refresh autonomy rules
2. **List all files** in `/Needs_Action/`
3. **For each file**, read it and classify:
   - `type: email` → Email triage flow
   - `type: ceo_briefing` → Invoke `/ceo-briefing` skill
   - `type: approval_request` → Route to `/Pending_Approval/`
   - `type: file_drop` → Summarize and log
   - Unknown type → Flag for CEO review
4. **Apply autonomy level** from the handbook:
   - **AUTO**: Execute immediately, log to `/Logs/`
   - **NOTIFY**: Execute, then note in Dashboard
   - **APPROVE**: Write approval file to `/Pending_Approval/<domain>/`, do NOT execute
5. **Move processed files** to `/Done/` (only after action is complete or approval file is written)
6. **Log** every action taken to `/Logs/`

## Email Triage Rules

When processing an email file:
- Check sender against Known Contacts in `Company_Handbook.md`
- **Known contact** → Draft reply (NOTIFY level), save draft in the email file
- **New contact** → Write approval file to `/Pending_Approval/email/` (APPROVE level)
- Flag any email older than 24 hours as overdue

## File Naming

Processed files keep their original name when moved to `/Done/`.
Approval files follow: `<ACTION>_<TARGET>_<DATE>.md`

## Safety

- Never delete files — only move them
- Never send emails or make payments without approval workflow
- If `DRY_RUN=true` in `.env`, log intended actions but do NOT execute external calls
- When in doubt: **ask, don't act**

## After Processing

Summarize what was done:
- How many items processed
- Actions taken (with autonomy level)
- Items routed to approval
- Any errors or flags for CEO
