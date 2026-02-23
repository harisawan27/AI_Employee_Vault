"""
WEBXES Tech — Cloud Agent

Runs on cloud VM. Polls Needs_Action/ for emails, claims them via move to
In_Progress/cloud/, creates AI-generated draft replies in Updates/, and signals
for local sync.

Usage:
    python cloud_agent.py          # Run polling loop
    python cloud_agent.py --once   # Process once and exit
"""

import argparse
import logging
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

from config import (
    VAULT_PATH, NEEDS_ACTION, IN_PROGRESS_CLOUD, UPDATES, SIGNALS,
    DONE, IS_CLOUD, IS_LOCAL, WORK_ZONE, ensure_dirs,
)
from audit_logger import audit_log

# Logging
LOGS = VAULT_PATH / "Logs"
LOGS.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS / "cloud_agent.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("cloud_agent")

POLL_INTERVAL = 60  # seconds

# ── Automated sender filter (second line of defence after gmail_watcher) ──────

AUTOMATED_DOMAINS = {
    'linkedin.com', 'coursera.org', 'udemy.com', 'udemy-email.com',
    'medium.com', 'producthunt.com', 'happyscribe.co',
    'mailchimp.com', 'sendgrid.net', 'sendgrid.com',
    'amazonses.com', 'canva.com', 'figma.com', 'notion.so',
    'twitter.com', 'facebook.com', 'instagram.com', 'youtube.com',
    'hubspot.com', 'mailgun.org', 'klaviyo.com',
}

AUTOMATED_KEYWORDS = [
    'noreply', 'no-reply', 'donotreply', 'do-not-reply',
    'notifications@', 'notification@', 'alerts@', 'alert@',
    'newsletter@', 'digest@', 'mailer@', 'mailer-daemon',
    'jobs-listings@', 'jobs@linkedin', 'info@linkedin',
    'updates@', 'support@coursera', 'team@producthunt',
]


def is_automated_sender(sender: str) -> bool:
    """Return True if the sender is automated/marketing — no reply needed."""
    sender_lower = sender.lower()
    for kw in AUTOMATED_KEYWORDS:
        if kw in sender_lower:
            return True
    m = re.search(r'@([\w\-.]+)', sender_lower)
    if m:
        domain = m.group(1)
        for blocked in AUTOMATED_DOMAINS:
            if domain == blocked or domain.endswith('.' + blocked):
                return True
    return False


# ── Draft generation ──────────────────────────────────────────────────────────

def _structured_skeleton(sender: str, subject: str, email_body: str) -> str:
    """Clean structured draft for VM / fallback — no AI, but complete and readable."""
    sender_name = sender.split('<')[0].strip()
    first_name = sender_name.split()[0] if sender_name else "there"
    preview = email_body.strip()[:800] if email_body else "(no content)"
    return (
        f"Dear {first_name},\n\n"
        f"Thank you for reaching out to WEBXES Tech regarding \"{subject}\".\n\n"
        f"[Please write your reply here based on their message below]\n\n"
        f"Best regards,\nWEBXES Tech Team\n\n"
        f"--- Their message ---\n{preview}"
    )


def _generate_with_claude_cli(sender: str, subject: str, email_body: str) -> str:
    """Use local Claude Code CLI (claude -p) to write a full professional reply."""
    sender_name = sender.split('<')[0].strip()
    first_name = sender_name.split()[0] if sender_name else "there"
    body_preview = email_body.strip()[:1500] if email_body else "(no body)"

    prompt = (
        "You are the AI assistant for WEBXES Tech, a digital marketing agency. "
        "Write a complete, professional, ready-to-send email reply body.\n\n"
        f"Sender: {sender}\n"
        f"Subject: {subject}\n"
        f"Their message:\n{body_preview}\n\n"
        "Requirements:\n"
        f"- Address them by first name: {first_name}\n"
        "- Directly acknowledge what they wrote\n"
        "- Warm, professional, concise (2-4 short paragraphs)\n"
        "- Represent WEBXES Tech as a competent digital agency\n"
        "- End with: Best regards,\\nWEBXES Tech Team\n"
        "- Write ONLY the email body — no subject line, no placeholders, no markdown"
    )

    try:
        result = subprocess.run(
            ['claude', '-p', prompt],
            capture_output=True, text=True, timeout=90,
            env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
        )
        if result.returncode == 0 and result.stdout.strip():
            log.info("Draft generated via Claude Code CLI")
            return result.stdout.strip()
        log.warning(f"claude -p failed (rc={result.returncode}): {result.stderr[:200]}")
    except FileNotFoundError:
        log.warning("claude CLI not found — falling back to skeleton")
    except subprocess.TimeoutExpired:
        log.warning("claude -p timed out — falling back to skeleton")
    except Exception as e:
        log.warning(f"claude -p error: {e}")

    return _structured_skeleton(sender, subject, email_body)


def generate_draft_body(sender: str, subject: str, email_body: str) -> str:
    """Generate draft: Claude CLI locally, structured skeleton on cloud VM."""
    if IS_LOCAL:
        return _generate_with_claude_cli(sender, subject, email_body)
    # On cloud VM — no Claude Code installed, use clean skeleton
    return _structured_skeleton(sender, subject, email_body)


# ── Core pipeline ─────────────────────────────────────────────────────────────

def parse_frontmatter(filepath: Path) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    text = filepath.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    meta = {}
    for line in parts[1].strip().split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip()
    return meta


def claim_file(filepath: Path) -> Path:
    """Move a file to In_Progress/cloud/ to claim it (prevents double-work)."""
    dest = IN_PROGRESS_CLOUD / filepath.name
    filepath.rename(dest)
    log.info(f"Claimed: {filepath.name} -> In_Progress/cloud/")
    return dest


def extract_email_body(original_content: str) -> str:
    """Pull the ## Email Content section out of the action file."""
    if "## Email Content" in original_content:
        body = original_content.split("## Email Content", 1)[1]
        if "## Suggested Actions" in body:
            body = body.split("## Suggested Actions")[0]
        return body.strip()
    return ""


def create_draft(meta: dict, original_content: str, source_filename: str) -> Path:
    """Create an AI-generated draft reply in Updates/."""
    now = datetime.now()
    sender = meta.get("from", "Unknown Sender")
    subject = meta.get("subject", "No Subject")

    email_body = extract_email_body(original_content)

    # Generate real content via Gemini
    log.info(f"Generating AI draft for: {subject[:60]}")
    draft_body = generate_draft_body(sender, subject, email_body)

    draft_filename = f"EMAIL_DRAFT_{now.strftime('%Y%m%d_%H%M%S')}_{source_filename}"
    draft_path = UPDATES / draft_filename

    draft_content = f"""---
type: email_draft
original_file: {source_filename}
from: {sender}
subject: Re: {subject}
generated: {now.isoformat()}
generated_by: cloud_agent_gemini
status: pending_approval
---

# Draft Reply

**To:** {sender}
**Subject:** Re: {subject}
**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S')}

---

{draft_body}

---

## Original Message
> {email_body[:500] if email_body else '(no content extracted)'}

## Notes
- AI-generated draft — review before sending
- Original file: {source_filename}
"""

    draft_path.write_text(draft_content, encoding="utf-8")
    log.info(f"Draft created: {draft_filename}")
    return draft_path


def create_signal(signal_type: str, details: dict):
    """Create a signal file for local sync to pick up."""
    now = datetime.now()
    filename = f"{signal_type}_{now.strftime('%Y%m%d_%H%M%S')}.json"
    signal_path = SIGNALS / filename

    import json
    signal_data = {
        "type": signal_type,
        "timestamp": now.isoformat(),
        "zone": WORK_ZONE,
        "details": details,
    }
    signal_path.write_text(json.dumps(signal_data, indent=2), encoding="utf-8")
    log.info(f"Signal created: {filename}")


def process_emails():
    """Scan Needs_Action/ for email files and process them."""
    if not NEEDS_ACTION.exists():
        return

    email_files = list(NEEDS_ACTION.glob("EMAIL_*.md"))
    if not email_files:
        return

    log.info(f"Found {len(email_files)} email(s) to process")

    for filepath in email_files:
        try:
            meta = parse_frontmatter(filepath)
            content = filepath.read_text(encoding="utf-8")
            sender = meta.get("from", "")

            # ── Second-line filter: skip automated senders ─────────────────
            if is_automated_sender(sender):
                log.info(f"Skipping automated email from: {sender}")
                # Move to Done without drafting
                DONE.mkdir(exist_ok=True)
                filepath.rename(DONE / filepath.name)
                audit_log("cloud_agent", "email_skipped_automated", {
                    "file": filepath.name, "sender": sender,
                })
                continue

            # Claim the file
            claimed = claim_file(filepath)

            # Create AI-generated draft
            draft_path = create_draft(meta, content, filepath.name)

            # Signal local
            create_signal("new_draft", {
                "draft_file": draft_path.name,
                "original_file": filepath.name,
                "sender": sender,
                "subject": meta.get("subject", "unknown"),
            })

            # Move original to Done/
            done_path = DONE / claimed.name
            DONE.mkdir(exist_ok=True)
            claimed.rename(done_path)
            log.info(f"Original moved to Done/: {claimed.name}")

            audit_log("cloud_agent", "email_drafted", {
                "original": filepath.name,
                "draft": draft_path.name,
                "sender": sender,
            })

        except Exception as e:
            log.error(f"Error processing {filepath.name}: {e}")
            audit_log("cloud_agent", "process_error",
                      {"file": filepath.name}, status="error", error=str(e))


def run_loop():
    """Main polling loop."""
    log.info("=== WEBXES Tech Cloud Agent Starting ===")
    log.info(f"Zone: {WORK_ZONE}")
    log.info(f"Vault: {VAULT_PATH}")
    log.info(f"Polling every {POLL_INTERVAL}s")

    ensure_dirs()

    try:
        while True:
            process_emails()
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        log.info("Cloud Agent stopped by user.")


def main():
    parser = argparse.ArgumentParser(description="WEBXES Tech Cloud Agent")
    parser.add_argument("--once", action="store_true", help="Process once and exit")
    args = parser.parse_args()

    ensure_dirs()

    if args.once:
        process_emails()
    else:
        run_loop()


if __name__ == "__main__":
    main()
