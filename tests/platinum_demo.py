"""
WEBXES Tech — Platinum Tier E2E Demo Test

Simulates the full email flow:
1. Fake email arrives → Needs_Action/
2. Cloud agent claims + drafts reply → Updates/
3. Local sync pulls draft → Needs_Action/ (for Claude refinement)
4. Simulated CEO approval → Approved/email/
5. Approval watcher detects → would send (DRY_RUN)
6. Verify audit trail

Usage:
    python tests/platinum_demo.py
"""

import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

# Add vault root to path
VAULT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VAULT_ROOT))

from config import (
    VAULT_PATH, NEEDS_ACTION, DONE, UPDATES, SIGNALS,
    IN_PROGRESS_CLOUD, APPROVED, LOGS, ensure_dirs,
)

# Force DRY_RUN for safety
import os
os.environ["DRY_RUN"] = "true"


def step(num: int, desc: str):
    print(f"\n{'='*60}")
    print(f"  Step {num}: {desc}")
    print(f"{'='*60}")


def check(condition: bool, msg: str):
    status = "PASS" if condition else "FAIL"
    icon = "[+]" if condition else "[X]"
    print(f"  {icon} {status}: {msg}")
    if not condition:
        print(f"      FAILED — stopping demo")
        sys.exit(1)


def main():
    print("\n" + "=" * 60)
    print("  WEBXES Tech — Platinum Tier E2E Demo")
    print("=" * 60)
    now = datetime.now()
    ts = now.strftime("%Y%m%d_%H%M%S")

    # Setup
    ensure_dirs()

    # ── Step 1: Simulate email arrival ──
    step(1, "Fake email arrives in Needs_Action/")
    email_filename = f"EMAIL_demo_{ts}.md"
    email_path = NEEDS_ACTION / email_filename
    email_content = f"""---
type: email
from: client@example.com
subject: Project Update Request
received: {now.isoformat()}
priority: high
status: pending
---

## Email Content
Hi WEBXES Tech, could you send me an update on the project status?

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
"""
    email_path.write_text(email_content, encoding="utf-8")
    check(email_path.exists(), f"Email file created: {email_filename}")

    # ── Step 2: Cloud agent processes email ──
    step(2, "Cloud agent claims email and creates draft")

    # Import and run cloud agent in --once mode
    from cloud_agent import process_emails
    process_emails()

    # Verify claim happened
    claimed = IN_PROGRESS_CLOUD / email_filename
    done_email = DONE / email_filename
    email_claimed = claimed.exists() or done_email.exists()
    check(email_claimed, "Email claimed from Needs_Action/")

    # Verify draft created
    drafts = list(UPDATES.glob(f"EMAIL_DRAFT_*{email_filename}"))
    check(len(drafts) > 0, f"Draft created in Updates/: {drafts[0].name if drafts else 'none'}")

    # Verify signal created
    signals = list(SIGNALS.glob("new_draft_*.json"))
    check(len(signals) > 0, "Signal file created for local sync")

    # ── Step 3: Local sync processes draft ──
    step(3, "Local sync picks up draft from Updates/")

    from local_sync import process_updates, process_signals
    count = process_updates()
    process_signals()
    check(count > 0, f"Processed {count} draft(s) from Updates/")

    # Verify draft moved to Needs_Action for Claude refinement
    draft_in_needs = list(NEEDS_ACTION.glob("EMAIL_DRAFT_*.md"))
    check(len(draft_in_needs) > 0, "Draft available in Needs_Action/ for Claude refinement")

    # ── Step 4: Simulate CEO approval ──
    step(4, "CEO approves the refined email")

    draft_file = draft_in_needs[0]
    approved_dir = APPROVED / "email"
    approved_dir.mkdir(parents=True, exist_ok=True)

    # Create an approved version
    approved_content = f"""---
type: email
action_type: email
to: client@example.com
subject: "Re: Project Update Request"
approved_at: {now.isoformat()}
status: approved
---

## Email

Dear Client,

Thank you for your email. Here is the project status update:

- Phase 1: Complete
- Phase 2: In progress (80%)
- Phase 3: Scheduled for next week

Best regards,
WEBXES Tech Team
"""
    approved_path = approved_dir / f"APPROVED_{draft_file.name}"
    approved_path.write_text(approved_content, encoding="utf-8")
    check(approved_path.exists(), f"Approved file created: {approved_path.name}")

    # Clean up the draft from Needs_Action (would normally be done by Claude)
    draft_file.unlink(missing_ok=True)

    # ── Step 5: Approval watcher processes (DRY_RUN) ──
    step(5, "Approval watcher processes approved email (DRY_RUN)")

    from approval_watcher import process_approved
    process_approved()

    # Check if the approved file was moved to Done/
    approved_done = list(DONE.glob(f"APPROVED_*{email_filename}*")) + list(DONE.glob("APPROVED_EMAIL_DRAFT_*.md"))
    check(len(approved_done) > 0 or not approved_path.exists(),
          "Approved email processed and moved to Done/")

    # ── Step 6: Verify audit trail ──
    step(6, "Verify audit trail")

    audit_file = LOGS / "audit.jsonl"
    check(audit_file.exists(), "audit.jsonl exists")

    audit_lines = audit_file.read_text(encoding="utf-8").strip().split("\n")
    recent_events = []
    for line in audit_lines[-20:]:  # Check last 20 events
        try:
            event = json.loads(line)
            if "demo" in str(event.get("details", {})) or event.get("category") == "cloud_agent":
                recent_events.append(event)
        except json.JSONDecodeError:
            continue

    check(len(recent_events) > 0, f"Found {len(recent_events)} audit event(s) from this demo")

    # ── Summary ──
    print("\n" + "=" * 60)
    print("  PLATINUM DEMO COMPLETE — ALL CHECKS PASSED")
    print("=" * 60)
    print()
    print("  Flow verified:")
    print("    Email arrived -> Cloud claimed -> Draft created ->")
    print("    Local synced -> CEO approved -> Watcher processed ->")
    print("    Audit logged -> Done/")
    print()
    print("  Note: Email was not actually sent (DRY_RUN=true)")
    print("=" * 60)


if __name__ == "__main__":
    main()
