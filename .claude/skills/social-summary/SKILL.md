---
name: social-summary
description: Scrape engagement metrics from social platforms and query the audit log to produce a Social Media Summary report. Writes output to /Plans/Social_Summary_<DATE>.md. Use weekly or on-demand to review social media performance.
user-invocable: true
argument-hint: [date range, e.g. "last 7 days" or "2026-02-01 to 2026-02-14"]
---

# Social Media Summary — WEBXES Tech

Generate a social media performance summary from engagement data and audit logs.

## Workflow

1. **Query audit log** — Read `Logs/audit.jsonl` for all `social_media` category events in the requested date range
2. **Tally posts** — Count posts by platform (LinkedIn, Facebook, Instagram, Twitter), status (posted, dry_run, failed)
3. **Check engagement** — If platforms are accessible, note any available engagement hints from audit details
4. **Compile report** — Write a formatted Markdown summary

## Report Contents

The summary report should include:

### Posting Activity
- Total posts per platform (posted vs. dry_run vs. failed)
- Approval turnaround: how many were approved, rejected, expired

### Engagement Snapshot
- Any engagement data available from audit log details
- Note which platforms need manual engagement checks

### Recommendations
- Platform with best activity
- Suggested posting frequency adjustments
- Content themes that performed well (based on topics in audit details)

## Output

Write to `Plans/Social_Summary_<DATE>.md`:

```markdown
---
type: social_summary
generated: <ISO timestamp>
period: <start_date> to <end_date>
---

# Social Media Summary — WEBXES Tech

**Period:** <date range>
**Generated:** <timestamp>

## Posting Activity

| Platform   | Posted | Dry Run | Failed | Total |
|------------|--------|---------|--------|-------|
| LinkedIn   | ...    | ...     | ...    | ...   |
| Facebook   | ...    | ...     | ...    | ...   |
| Instagram  | ...    | ...     | ...    | ...   |
| Twitter    | ...    | ...     | ...    | ...   |

## Approval Workflow

- Approved: X
- Rejected: Y
- Expired: Z

## Engagement Snapshot

<available metrics or "Manual check required">

## Recommendations

<AI-generated recommendations based on data>
```

## Data Sources

- `Logs/audit.jsonl` — primary structured data (use `audit_logger.query_events()`)
- `Done/` folder — completed approval files for context
- Platform analytics — note as "manual check" if not scraped

## After Writing

Confirm to the user:
- The report file path
- Summary of key findings (1-2 sentences)
- Any platforms that need manual engagement review
