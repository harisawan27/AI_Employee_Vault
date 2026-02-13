---
name: accounting-audit
description: Generate a Weekly Accounting & AI Activity Audit for WEBXES Tech. Pulls financial data from Odoo (invoices, bills, payments, P&L) and reads the audit log for AI activity. Writes a comprehensive report to /Plans/Weekly_Audit_<DATE>.md. Use weekly on Fridays or on-demand.
user-invocable: true
argument-hint: [date range, e.g. "last 7 days" or "2026-02-01 to 2026-02-14"]
---

# Weekly Accounting & AI Activity Audit — WEBXES Tech

Generate a comprehensive weekly audit combining financial data from Odoo and AI activity from the audit log.

## Workflow

1. **Determine date range** — Default to last 7 days. Override with `$ARGUMENTS` if provided.
2. **Pull Odoo financial data** using MCP tools:
   - `get_invoices` — customer invoices for the period
   - `get_bills` — vendor bills for the period
   - `get_payments` — payments for the period
   - `get_profit_and_loss` — P&L for the period
   - `get_balance_sheet` — current balance sheet snapshot
3. **Read AI activity** from `Logs/audit.jsonl`:
   - Count events by category (email, social_media, approval, orchestrator)
   - Count by status (success, error, warning)
   - List notable errors or warnings
4. **Read approval activity** from `Done/` folder:
   - Count approved vs. rejected items
5. **Write report** to `Plans/Weekly_Audit_<DATE>.md`

## Report Format

```markdown
---
type: weekly_audit
generated: <ISO timestamp>
period: <start_date> to <end_date>
---

# Weekly Audit — WEBXES Tech

**Period:** <date range>
**Generated:** <timestamp>

---

## Financial Summary

### Revenue (Customer Invoices)
| Invoice | Customer | Amount | Date |
|---------|----------|--------|------|
| ...     | ...      | ...    | ...  |

**Total Revenue:** $X,XXX.XX
**Invoice Count:** X

### Expenses (Vendor Bills)
| Bill | Vendor | Amount | Date |
|------|--------|--------|------|
| ...  | ...    | ...    | ...  |

**Total Expenses:** $X,XXX.XX

### Payments
| Payment | Partner | Amount | Type | Date |
|---------|---------|--------|------|------|
| ...     | ...     | ...    | ...  | ...  |

### Profit & Loss
- **Total Income:** $X,XXX.XX
- **Total Expenses:** $X,XXX.XX
- **Net Profit:** $X,XXX.XX

### Balance Sheet (as of today)
- **Total Assets:** $X,XXX.XX
- **Total Liabilities:** $X,XXX.XX
- **Total Equity:** $X,XXX.XX

---

## AI Activity Summary

### Events by Category
| Category | Success | Error | Total |
|----------|---------|-------|-------|
| ...      | ...     | ...   | ...   |

### Approval Workflow
- Approved: X
- Rejected: Y
- Expired: Z

### Notable Errors
- <list any errors from the period>

---

## Recommendations
- <AI-generated recommendations based on financial and activity data>
```

## Error Handling

- If Odoo is unreachable, note "Odoo offline" in the financial section and continue with AI activity data
- If audit.jsonl is empty or missing, note "No AI activity recorded" in that section
- Always produce a report even with partial data

## After Writing

Confirm to the user:
- The report file path
- Key financial metrics (revenue, expenses, net profit)
- AI activity summary (total events, error count)
- Any recommendations or concerns
