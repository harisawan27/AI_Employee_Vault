"""
WEBXES Tech — Multi-Domain Approval Watcher

Watches Approved/ for files moved there by the dashboard API.
Routes execution based on domain subdirectory:
  - Approved/email/         → Send via Gmail API
  - Approved/social_media/  → Post via LinkedIn/Facebook/Instagram/Twitter
  - Approved/payments/      → Create invoice via Odoo MCP

Runs locally only (requires browser sessions and credentials).
"""

import base64
import logging
import re
import shutil
import time
from email.message import EmailMessage
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config import (
    APPROVED, DONE, IS_CLOUD, IS_LOCAL,
    GMAIL_TOKEN_PATH, DRY_RUN,
    ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD,
)
from audit_logger import audit_log

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("approval_watcher")

# Domain subdirectories to watch
DOMAIN_DIRS = {
    "email": APPROVED / "email",
    "social_media": APPROVED / "social_media",
    "payments": APPROVED / "payments",
}


# ── Frontmatter Parser ────────────────────────────────────────────────

def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter metadata from file content."""
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    metadata = {}
    for line in parts[1].strip().split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            metadata[key.strip()] = value.strip()
    return metadata


# ── Email Execution ───────────────────────────────────────────────────

def _send_email(creds, recipient: str, subject: str, body: str) -> bool:
    """Send an email via Gmail API."""
    try:
        service = build("gmail", "v1", credentials=creds)
        message = EmailMessage()
        message.set_content(body)
        message["To"] = recipient
        message["Subject"] = subject

        encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": encoded}).execute()
        return True
    except Exception as e:
        logger.error(f"GMAIL ERROR: {e}")
        return False


def process_email(file_path: Path) -> bool:
    """Process an approved email file — extract fields and send."""
    if not GMAIL_TOKEN_PATH or not Path(GMAIL_TOKEN_PATH).exists():
        logger.error("Gmail token not found. Cannot send emails.")
        return False

    creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN_PATH))
    content = file_path.read_text(encoding="utf-8")

    # Extract recipient
    to_match = (
        re.search(r"\*\*To:\*\*\s*.*?<(.+?)>", content)
        or re.search(r"\*\*To:\*\*\s*(\S+@\S+)", content)
    )
    # Extract subject
    sub_match = (
        re.search(r"\*\*Subject:\*\*\s*(.*)", content)
    )

    to_email = to_match.group(1).strip() if to_match else ""
    subject = sub_match.group(1).strip() if sub_match else "Re: Inquiry"

    # Extract body (between --- markers, after headers)
    parts = content.split("---")
    clean_body = ""
    if len(parts) >= 3:
        raw_body = parts[2].strip()
        # Remove metadata lines from body
        clean_body = re.sub(r"\*\*To:\*\*.*?\n", "", raw_body)
        clean_body = re.sub(r"\*\*Subject:\*\*.*?\n", "", clean_body)
        clean_body = re.sub(r"\*\*Generated:\*\*.*?\n", "", clean_body)
        clean_body = re.sub(r"# Draft Reply.*?\n", "", clean_body)
        clean_body = clean_body.strip()

    if not clean_body or len(clean_body) < 10:
        clean_body = content.split("# Draft Reply")[-1].split("---")[0].strip()

    if not to_email or not clean_body:
        logger.warning(f"SKIP email {file_path.name}: missing To or body")
        return False

    if DRY_RUN:
        logger.info(f"[DRY_RUN] Would send email to {to_email}: {subject}")
        audit_log("email", "dry_run_send", {"to": to_email, "subject": subject, "file": file_path.name})
        return True

    logger.info(f"Sending email to {to_email}...")
    if _send_email(creds, to_email, subject, clean_body):
        audit_log("email", "sent", {"to": to_email, "subject": subject, "file": file_path.name})
        return True

    audit_log("email", "send_failed", {"to": to_email, "file": file_path.name}, status="error")
    return False


# ── Social Media Execution ────────────────────────────────────────────

def process_social_media(file_path: Path) -> bool:
    """Process an approved social media post — detect platform and post."""
    content = file_path.read_text(encoding="utf-8")
    metadata = parse_frontmatter(content)
    platform = metadata.get("platform", "").lower()

    # Extract post text (after second --- in content body)
    parts = content.split("---")
    post_text = ""
    # The post text is typically in parts[4] (frontmatter=1,2 | header section=3 | post=4 | instructions=5)
    # Find the section that looks like actual post content (not headers, not instructions)
    for i, part in enumerate(parts):
        stripped = part.strip()
        if stripped and not stripped.startswith("##") and "**Platform:**" not in stripped and "type:" not in stripped and "Instructions for CEO" not in stripped:
            # Check it's not the frontmatter
            if i >= 2 and len(stripped) > 20:
                post_text = stripped
                break

    # Fallback: grab everything after frontmatter, strip metadata and instructions
    if not post_text:
        if len(parts) >= 3:
            body = parts[2]
            for remaining in parts[3:]:
                body += "---" + remaining
        else:
            body = content

        # Remove headers and instruction sections
        if "## Instructions for CEO" in body:
            body = body.split("## Instructions for CEO")[0]
        # Remove metadata lines
        body = re.sub(r"\*\*Platform:\*\*.*?\n", "", body)
        body = re.sub(r"\*\*Topic:\*\*.*?\n", "", body)
        body = re.sub(r"\*\*Generated:\*\*.*?\n", "", body)
        body = re.sub(r"\*\*Expires:\*\*.*?\n", "", body)
        body = re.sub(r"##.*?Post.*?Pending Approval\n", "", body)
        # Remove remaining --- separators
        body = body.replace("---", "").strip()
        post_text = body.strip()

    if not post_text:
        logger.warning(f"SKIP social {file_path.name}: could not extract post text")
        return False

    if not platform:
        logger.warning(f"SKIP social {file_path.name}: no platform in frontmatter")
        return False

    logger.info(f"Posting to {platform}: {post_text[:80]}...")

    if platform == "linkedin":
        from linkedin_poster import post_from_approved_file as linkedin_post
        success = linkedin_post(file_path)
    elif platform in ("facebook", "instagram", "twitter"):
        from social_media_poster import post_from_approved_file as social_post
        success = social_post(file_path, platform)
    else:
        logger.warning(f"Unknown platform: {platform}")
        return False

    if success:
        audit_log("social_media", "posted", {"platform": platform, "file": file_path.name})
    else:
        audit_log("social_media", "post_failed", {"platform": platform, "file": file_path.name}, status="error")

    return success


# ── Payments Execution ────────────────────────────────────────────────

def process_payment(file_path: Path) -> bool:
    """Process an approved payment — create invoice in Odoo."""
    content = file_path.read_text(encoding="utf-8")
    metadata = parse_frontmatter(content)

    vendor = metadata.get("vendor", metadata.get("partner", ""))
    amount = metadata.get("amount", "0")
    description = metadata.get("description", metadata.get("subject", "Payment"))

    if not vendor:
        logger.warning(f"SKIP payment {file_path.name}: no vendor specified")
        return False

    if DRY_RUN:
        logger.info(f"[DRY_RUN] Would create Odoo invoice: {vendor} - {amount}")
        audit_log("payments", "dry_run_invoice", {
            "vendor": vendor, "amount": amount, "file": file_path.name,
        })
        return True

    try:
        import xmlrpc.client
        common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
        uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
        models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

        # Search for partner
        partner_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            "res.partner", "search",
            [[["name", "ilike", vendor]]],
            {"limit": 1},
        )
        partner_id = partner_ids[0] if partner_ids else False

        if not partner_id:
            logger.warning(f"Odoo partner not found: {vendor}")
            audit_log("payments", "partner_not_found", {"vendor": vendor, "file": file_path.name}, status="error")
            return False

        # Create invoice
        invoice_id = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            "account.move", "create",
            [{
                "partner_id": partner_id,
                "move_type": "out_invoice",
                "invoice_line_ids": [(0, 0, {
                    "name": description,
                    "price_unit": float(amount),
                    "quantity": 1,
                })],
            }],
        )

        logger.info(f"Odoo invoice created: ID {invoice_id} for {vendor}")
        audit_log("payments", "invoice_created", {
            "vendor": vendor, "amount": amount, "invoice_id": invoice_id, "file": file_path.name,
        })
        return True

    except Exception as e:
        logger.error(f"Odoo payment failed: {e}")
        audit_log("payments", "invoice_failed", {
            "vendor": vendor, "amount": amount, "file": file_path.name,
        }, status="error", error=str(e))
        return False


# ── Main Loop ─────────────────────────────────────────────────────────

PROCESSORS = {
    "email": process_email,
    "social_media": process_social_media,
    "payments": process_payment,
}


def process_approvals():
    """Scan all domain subdirectories under Approved/ and execute."""
    for domain, domain_dir in DOMAIN_DIRS.items():
        if not domain_dir.exists():
            continue

        for file_path in sorted(domain_dir.glob("*.md")):
            logger.info(f"[{domain}] Processing: {file_path.name}")

            processor = PROCESSORS.get(domain)
            if not processor:
                logger.warning(f"No processor for domain: {domain}")
                continue

            try:
                success = processor(file_path)
            except Exception as e:
                logger.error(f"[{domain}] Error processing {file_path.name}: {e}")
                audit_log(domain, "execution_error", {"file": file_path.name}, status="error", error=str(e))
                continue

            if success:
                # Move to Done/<domain>/
                done_dir = DONE / domain
                done_dir.mkdir(parents=True, exist_ok=True)
                dest = done_dir / file_path.name
                shutil.move(str(file_path), str(dest))
                logger.info(f"[{domain}] SUCCESS: {file_path.name} → Done/{domain}/")
            else:
                logger.warning(f"[{domain}] FAILED: {file_path.name} (kept in Approved for retry)")

    # Also handle legacy files in Approved/ root (not in subfolders)
    if APPROVED.exists():
        for file_path in sorted(APPROVED.glob("*.md")):
            if file_path.is_dir():
                continue
            logger.info(f"[legacy] Processing root file: {file_path.name}")
            # Try email by default for legacy files
            success = process_email(file_path)
            if success:
                DONE.mkdir(parents=True, exist_ok=True)
                shutil.move(str(file_path), str(DONE / file_path.name))
                logger.info(f"[legacy] SUCCESS: {file_path.name} → Done/")


if __name__ == "__main__":
    if IS_CLOUD:
        logger.error("Approval watcher must run LOCALLY (requires browser sessions & credentials).")
        logger.error("Exiting.")
        exit(1)

    logger.info("WEBXES AI Approval Watcher — Multi-Domain V2 Ready")
    logger.info(f"Watching: {', '.join(str(d) for d in DOMAIN_DIRS.values())}")

    # Ensure directories exist
    for d in DOMAIN_DIRS.values():
        d.mkdir(parents=True, exist_ok=True)

    while True:
        process_approvals()
        time.sleep(10)
