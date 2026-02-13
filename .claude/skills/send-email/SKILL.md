---
name: send-email
description: Draft and send emails via Gmail MCP with approval guardrails per Company Handbook. Checks recipient against Known Contacts to determine if approval is needed. Use when the CEO asks to send an email or when an email action needs processing.
user-invocable: true
argument-hint: <to:recipient> <subject:line> [body or instructions]
---

# Send Email — WEBXES Tech AI Employee

Draft and send emails via Gmail MCP, respecting Company Handbook approval rules.

## Workflow

1. **Read Company Handbook** (`Company_Handbook.md`) — refresh email rules (Section 4.2)
2. **Parse arguments** from `$ARGUMENTS`:
   - Extract recipient (to:), subject (subject:), and body/instructions
   - If arguments are natural language, extract intent
3. **Check recipient** against Known Contacts in handbook Section 5
4. **Apply autonomy level:**
   - **Known contact** → NOTIFY: Draft and send, then log
   - **New contact** → APPROVE: Write approval file, do NOT send
   - **Bulk email (3+ recipients)** → APPROVE: Always
   - **Email with attachments > 5MB** → APPROVE: Always
5. **Execute or route** based on autonomy level

## For NOTIFY Level (Known Contacts)

Use the Gmail MCP tools to:
1. Draft the email with professional signature
2. If `DRY_RUN=true` in `.env`, log the draft but do NOT send
3. If `DRY_RUN=false`, send via Gmail MCP `send_email` tool
4. Log the action to `/Logs/`
5. Note in Dashboard

## For APPROVE Level (New Contacts / Bulk)

Write approval file to `/Pending_Approval/email/EMAIL_<RECIPIENT>_<DATE>.md`:

```markdown
---
type: email
action_type: email
to: <recipient email>
subject: <subject line>
generated: <ISO timestamp>
expires: <24 hours from now, ISO timestamp>
status: pending_approval
---

## Email — Pending Approval

**To:** <recipient>
**Subject:** <subject>
**Generated:** <date and time>

---

<full email body here>

---

## Instructions for CEO
- **To approve:** Move this file to `/Approved/email/`
- **To reject:** Move this file to `/Rejected/email/`
- **To edit:** Modify the email content above before approving
```

## Email Formatting Rules

- Professional signature block (per handbook Section 2.2)
- Clear, actionable subject line
- Address client by name when known
- No slang or emojis (per handbook Section 2.1)

## Professional Signature

```
Best regards,

WEBXES Tech
Digital Agency
```

## Safety

- **Never** send without checking autonomy level first
- **Never** include sensitive data (passwords, account numbers) in email body
- If `DRY_RUN=true`, log everything but send nothing
- Rate limit: Max 20 emails/hour (per handbook Section 10)

## After Processing

Report to user:
- What was done (sent or routed to approval)
- Recipient and subject
- Autonomy level applied and why
