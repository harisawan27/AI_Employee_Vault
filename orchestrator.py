"""
WEBXES Tech — CEO Briefing Orchestrator

Central scheduler that triggers routines on schedule.
Currently: Monday 8:00 AM CEO Briefing.

Usage:
    python orchestrator.py          # Run scheduler (waits for Monday 8 AM)
    python orchestrator.py --now    # Trigger CEO Briefing immediately
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import schedule
from dotenv import load_dotenv

VAULT_ROOT = Path(__file__).resolve().parent
load_dotenv(VAULT_ROOT / ".env")

# Paths
NEEDS_ACTION = VAULT_ROOT / "Needs_Action"
PLANS = VAULT_ROOT / "Plans"
LOGS = VAULT_ROOT / "Logs"
RALPH_STATE = VAULT_ROOT / ".claude" / "ralph_state.json"

from audit_logger import audit_log

# Logging
LOGS.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS / "orchestrator.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("orchestrator")


def trigger_ceo_briefing():
    """Fetch revenue data from Odoo and create a CEO Briefing task file."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    task_filename = f"CEO_BRIEFING_{today_str}.md"
    task_path = NEEDS_ACTION / task_filename
    briefing_output = f"Plans/CEO_Briefing_{today_str}.md"

    log.info("--- CEO Briefing trigger started ---")

    # Step 1: Fetch revenue data from Odoo
    try:
        sys.path.insert(0, str(VAULT_ROOT / "Odoo_FTE"))
        from odoo_briefing_mcp import get_weekly_revenue
        revenue = get_weekly_revenue()
        log.info(f"Revenue data fetched: {revenue}")
    except ConnectionError as e:
        log.error(f"Odoo unreachable: {e}")
        log.info("Creating task file with placeholder data (Odoo offline)")
        revenue = {
            "period": "N/A (Odoo offline)",
            "total_revenue": 0,
            "transaction_count": 0,
        }
    except Exception as e:
        log.error(f"Unexpected error fetching revenue: {e}")
        revenue = {
            "period": "N/A (error)",
            "total_revenue": 0,
            "transaction_count": 0,
        }

    # Step 2: Format revenue for display
    total_fmt = f"${revenue['total_revenue']:,.2f}"
    generated_ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # Step 3: Create task file in Needs_Action/
    task_content = f"""---
type: ceo_briefing
generated: {generated_ts}
status: pending
---

# CEO Briefing Request

Generate the Monday Morning CEO Briefing for WEBXES Tech.

## Raw Revenue Data
- Period: {revenue['period']}
- Total Revenue: {total_fmt}
- Transaction Count: {revenue['transaction_count']}

## Instructions
1. Write a professional CEO Briefing in Markdown
2. Save it to: {briefing_output}
3. Include: revenue summary, trend context, key highlights, action items
4. Move THIS file to Done/ when complete
"""

    NEEDS_ACTION.mkdir(exist_ok=True)
    task_path.write_text(task_content, encoding="utf-8")
    log.info(f"Task file created: {task_path}")

    # Step 4: Activate Ralph Wiggum loop
    prompt = (
        f"Read the CEO Briefing task file at Needs_Action/{task_filename}, "
        f"generate a beautiful professional Markdown briefing report, "
        f"save it to {briefing_output}, then move the task file to Done/"
    )

    ralph_state = {
        "active": True,
        "task_file": task_filename,
        "prompt": prompt,
        "max_iterations": 5,
        "current_iteration": 0,
        "started_at": datetime.now().isoformat(),
    }

    RALPH_STATE.parent.mkdir(parents=True, exist_ok=True)
    with open(RALPH_STATE, "w", encoding="utf-8") as f:
        json.dump(ralph_state, f, indent=2)
    log.info("Ralph Wiggum loop ACTIVATED")

    # Step 5: Print the prompt for the user
    print()
    print("=" * 60)
    print("  CEO BRIEFING TASK READY")
    print("=" * 60)
    print()
    print("Give Claude this prompt:")
    print()
    print(f'  "{prompt}"')
    print()
    print(f"Task file : Needs_Action/{task_filename}")
    print(f"Output    : {briefing_output}")
    print(f"Ralph     : active (max 5 iterations)")
    print("=" * 60)

    audit_log("orchestrator", "ceo_briefing_triggered",
              {"task_file": task_filename, "revenue": revenue})
    log.info("--- CEO Briefing trigger complete ---")


def trigger_weekly_audit():
    """Create a weekly audit task file for the accounting-audit skill."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    task_filename = f"WEEKLY_AUDIT_{today_str}.md"
    task_path = NEEDS_ACTION / task_filename

    log.info("--- Weekly Audit trigger started ---")

    task_content = f"""---
type: weekly_audit
generated: {datetime.now().isoformat()}
status: pending
---

# Weekly Audit Request

Generate the Weekly Accounting & AI Activity Audit for WEBXES Tech.

## Instructions
1. Run the `/accounting-audit` skill
2. Pull Odoo data (invoices, bills, payments, P&L)
3. Read audit.jsonl for AI activity summary
4. Write report to Plans/Weekly_Audit_{today_str}.md
5. Move THIS file to Done/ when complete
"""

    NEEDS_ACTION.mkdir(exist_ok=True)
    task_path.write_text(task_content, encoding="utf-8")
    audit_log("orchestrator", "weekly_audit_triggered", {"task_file": task_filename})
    log.info(f"Weekly audit task file created: {task_path}")

    # Activate Ralph Wiggum loop
    prompt = (
        f"Read the Weekly Audit task at Needs_Action/{task_filename}, "
        f"run the /accounting-audit skill, then move the task file to Done/"
    )
    ralph_state = {
        "active": True,
        "task_file": task_filename,
        "prompt": prompt,
        "max_iterations": 5,
        "current_iteration": 0,
        "started_at": datetime.now().isoformat(),
    }
    RALPH_STATE.parent.mkdir(parents=True, exist_ok=True)
    with open(RALPH_STATE, "w", encoding="utf-8") as f:
        json.dump(ralph_state, f, indent=2)

    log.info("Ralph Wiggum loop ACTIVATED for weekly audit")
    log.info("--- Weekly Audit trigger complete ---")


def main():
    parser = argparse.ArgumentParser(description="WEBXES Tech Orchestrator")
    parser.add_argument(
        "--now", action="store_true",
        help="Trigger CEO Briefing immediately (skip scheduler)",
    )
    parser.add_argument(
        "--audit", action="store_true",
        help="Trigger Weekly Audit immediately (skip scheduler)",
    )
    args = parser.parse_args()

    if args.now:
        log.info("Manual trigger via --now flag")
        trigger_ceo_briefing()
        return

    if args.audit:
        log.info("Manual audit trigger via --audit flag")
        trigger_weekly_audit()
        return

    # Schedule: Monday at 8:00 AM — CEO Briefing
    schedule.every().monday.at("08:00").do(trigger_ceo_briefing)
    # Schedule: Friday at 5:00 PM — Weekly Audit
    schedule.every().friday.at("17:00").do(trigger_weekly_audit)
    log.info("Orchestrator started")
    log.info("  CEO Briefing  : Monday 8:00 AM")
    log.info("  Weekly Audit  : Friday 5:00 PM")
    log.info("Press Ctrl+C to stop")

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        log.info("Orchestrator stopped by user")


if __name__ == "__main__":
    main()
