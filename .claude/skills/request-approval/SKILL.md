---
name: request-approval
description: Create a formatted approval request file in /Pending_Approval/ for actions that require CEO sign-off. Supports email, payment, and social media domains. Use when an action exceeds the AI's autonomy level per Company Handbook.
user-invocable: true
argument-hint: <domain:email|payments|social_media> <action description>
---

# Request Approval — WEBXES Tech AI Employee

Create a properly formatted approval request for CEO review.

## Workflow

1. **Parse arguments** from `$ARGUMENTS`:
   - Extract domain (email, payments, social_media)
   - Extract action details (what, who, amount, reason)
2. **Determine domain** — if not specified, infer from action type
3. **Write approval file** to `/Pending_Approval/<domain>/`
4. **Log** the request creation

## Approval File Format

Filename: `<ACTION>_<TARGET>_<DATE>.md` (per handbook Section 6)

```markdown
---
type: <domain>
action_type: <domain>
action: <brief action description>
target: <recipient/vendor/platform>
amount: <dollar amount if financial, otherwise omit>
reason: <why this action is needed>
generated: <ISO timestamp>
expires: <24 hours from now, ISO timestamp>
status: pending_approval
---

## Approval Request — <Action Title>

**Domain:** <email | payments | social_media>
**Action:** <what will happen if approved>
**Target:** <who/what is affected>
**Amount:** <if applicable>
**Reason:** <business justification>

**Generated:** <date and time>
**Expires:** <24 hours from generation>

---

### Details

<Full details of the proposed action, including any draft content, transaction details, etc.>

---

### Instructions for CEO
- **To approve:** Move this file to `/Approved/<domain>/`
- **To reject:** Move this file to `/Rejected/<domain>/`
- Edit the file before moving to modify the action
- This request **expires in 24 hours** if not acted upon
```

## Domain Routing

| Domain | Folder | Examples |
|--------|--------|----------|
| `email` | `/Pending_Approval/email/` | New client emails, bulk sends, forwarding |
| `payments` | `/Pending_Approval/payments/` | Payments >$50, new payees, subscription changes |
| `social_media` | `/Pending_Approval/social_media/` | AI-generated posts, DMs |

## After Writing

Confirm to user:
- Approval file path
- Domain and action summary
- 24-hour expiry reminder
- Instructions: approve by moving to `/Approved/<domain>/`, reject by moving to `/Rejected/<domain>/`
