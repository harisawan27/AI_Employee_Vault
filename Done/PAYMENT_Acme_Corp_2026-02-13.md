---
type: payment
action_type: payment
action: Pay invoice #1234
target: Acme Corp
amount: $250.00
reason: Monthly hosting services
generated: 2026-02-13T16:45:00
expires: 2026-02-14T16:45:00
status: pending_approval
---

## Approval Request — Payment to Acme Corp

**Domain:** payments
**Action:** Pay invoice #1234 for monthly hosting services
**Target:** Acme Corp
**Amount:** $250.00
**Reason:** Recurring monthly hosting — due Feb 15

**Generated:** 2026-02-13 16:45
**Expires:** 2026-02-14 16:45

---

### Details

Invoice #1234 from Acme Corp for February 2026 hosting services.
Standard monthly charge, consistent with previous months.

---

### Instructions for CEO
- **To approve:** Move this file to `/Approved/payments/`
- **To reject:** Move this file to `/Rejected/payments/`
