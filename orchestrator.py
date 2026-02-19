import argparse
import json
import logging
import sys
import time
import os
from datetime import datetime
from pathlib import Path

import schedule
import anthropic
from dotenv import load_dotenv

# Load Environment and Config
load_dotenv('/opt/ai_employee_vault/.env')
from config import VAULT_PATH, NEEDS_ACTION, PLANS, LOGS, PENDING_APPROVAL

# Setup Anthropic Client
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Logging Setup
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

# --- EMAIL PROCESSING LOGIC ---

def process_email_tasks():
    """Watch Needs_Action for emails and draft replies using Claude."""
    # Look for files starting with EMAIL_
    email_files = list(NEEDS_ACTION.glob("EMAIL_*.md"))
    
    if not email_files:
        return

    handbook_path = VAULT_PATH / "Company_Handbook.md"
    handbook_content = handbook_path.read_text() if handbook_path.exists() else "No handbook available."

    for file in email_files:
        try:
            log.info(f"Processing Email: {file.name}")
            email_content = file.read_text()

            prompt = f"""
            You are the WEBXES AI Employee. Use the Company Handbook to write a professional reply.
            
            HANDBOOK:
            {handbook_content}
            
            EMAIL TO REPLY TO:
            {email_content}
            
            Provide your response in this EXACT format:
            ---
            to: [Sender Email]
            subject: Re: [Original Subject]
            ---
            ## Draft Reply
            
            [Your professional response here]
            """

            # Call Claude API
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            reply_text = response.content[0].text
            
            # Save to Pending_Approval for Dashboard
            output_path = PENDING_APPROVAL / f"DRAFT_{file.name}"
            output_path.write_text(reply_text, encoding="utf-8")
            
            # Archive the original
            done_dir = VAULT_PATH / "Done"
            done_dir.mkdir(exist_ok=True)
            file.rename(done_dir / file.name)
            
            log.info(f"Successfully drafted reply for {file.name}")

        except Exception as e:
            log.error(f"Failed to process {file.name}: {e}")

# --- ORIGINAL SCHEDULED TASKS ---

def trigger_ceo_briefing():
    log.info("--- CEO Briefing trigger started ---")
    # ... (Keep your original Odoo logic here if needed, 
    # but for brevity we are focusing on the AI brain)
    log.info("CEO Briefing logic executed.")

def main():
    parser = argparse.ArgumentParser(description="WEBXES Tech Smart Orchestrator")
    parser.add_argument("--now", action="store_true", help="Trigger CEO Briefing immediately")
    args = parser.parse_args()

    if args.now:
        log.info("Manual trigger via --now flag")
        trigger_ceo_briefing()
        return

    # Schedule: Original Routines
    schedule.every().monday.at("08:00").do(trigger_ceo_briefing)
    
    # NEW: Check for emails every 20 seconds
    schedule.every(20).seconds.do(process_email_tasks)

    log.info("Smart Orchestrator Started")
    log.info("Monitoring Needs_Action for emails...")
    log.info("Scheduled: CEO Briefing (Mon 8AM)")

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Orchestrator stopped by user")

if __name__ == "__main__":
    main()
