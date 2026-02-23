import base64
import os
import re
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from pathlib import Path
from base_watcher import BaseWatcher
from datetime import datetime
from dotenv import load_dotenv

# ── Automated/marketing sender filter ────────────────────────────────────────

# Domains that only send automated emails — never need a reply
AUTOMATED_DOMAINS = {
    'linkedin.com', 'coursera.org', 'udemy.com', 'udemy-email.com',
    'medium.com', 'producthunt.com', 'happyscribe.co',
    'mailchimp.com', 'sendgrid.net', 'sendgrid.com',
    'amazonses.com', 'canva.com', 'figma.com', 'notion.so',
    'twitter.com', 'facebook.com', 'instagram.com', 'youtube.com',
    'hubspot.com', 'mailgun.org', 'klaviyo.com',
}

# Sender address keywords that indicate automated mail
AUTOMATED_KEYWORDS = [
    'noreply', 'no-reply', 'donotreply', 'do-not-reply',
    'notifications@', 'notification@', 'alerts@', 'alert@',
    'newsletter@', 'digest@', 'mailer@', 'mailer-daemon',
    'jobs-listings@', 'jobs@linkedin', 'info@linkedin',
    'updates@', 'support@coursera', 'team@producthunt',
]


def is_automated_email(headers: dict) -> bool:
    """Return True if this email is automated/marketing and should be skipped."""
    from_addr = headers.get('From', '').lower()

    # Check sender address for no-reply patterns
    for kw in AUTOMATED_KEYWORDS:
        if kw in from_addr:
            return True

    # Check sender domain against blocked list
    m = re.search(r'@([\w\-.]+)', from_addr)
    if m:
        domain = m.group(1)
        for blocked in AUTOMATED_DOMAINS:
            if domain == blocked or domain.endswith('.' + blocked):
                return True

    # List-Unsubscribe header is the definitive marker for bulk/marketing mail
    if any(k.lower() == 'list-unsubscribe' for k in headers):
        return True

    return False


# ── Email body extraction ─────────────────────────────────────────────────────

def _decode_b64(data: str) -> str:
    try:
        return base64.urlsafe_b64decode(data + '==').decode('utf-8', errors='ignore')
    except Exception:
        return ''


def get_email_body(msg: dict) -> str:
    """Extract readable plain text from the Gmail message payload."""
    payload = msg.get('payload', {})

    # Simple (non-multipart) message
    body_data = payload.get('body', {}).get('data', '')
    if body_data:
        return _decode_b64(body_data)[:3000]

    # Multipart — prefer text/plain, fall back to text/html
    def extract_from_parts(parts):
        plain = html = ''
        for part in parts:
            mime = part.get('mimeType', '')
            data = part.get('body', {}).get('data', '')
            if mime == 'text/plain' and data:
                plain += _decode_b64(data)
            elif mime == 'text/html' and data:
                html += _decode_b64(data)
            # Recurse into nested multipart
            sub_parts = part.get('parts', [])
            if sub_parts:
                sp, sh = extract_from_parts(sub_parts)
                plain += sp
                html += sh
        return plain, html

    plain, html = extract_from_parts(payload.get('parts', []))
    if plain:
        return plain[:3000]
    if html:
        # Strip HTML tags for readability
        text = re.sub(r'<[^>]+>', ' ', html)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:3000]

    # Last resort: snippet
    return msg.get('snippet', '')


# ── Watcher ───────────────────────────────────────────────────────────────────

class GmailWatcher(BaseWatcher):
    def __init__(self, vault_path: str, credentials_path: str):
        super().__init__(vault_path, check_interval=30)
        self.creds = Credentials.from_authorized_user_file(credentials_path)
        self.service = build('gmail', 'v1', credentials=self.creds)
        self.processed_ids = set()

    def check_for_updates(self) -> list:
        # Added newer_than:1d to ignore old unread spam!
        results = self.service.users().messages().list(
            userId='me', q='is:unread newer_than:1d'
        ).execute()
        messages = results.get('messages', [])
        return [m for m in messages if m['id'] not in self.processed_ids]

    def create_action_file(self, message) -> Path | None:
        msg = self.service.users().messages().get(
            userId='me', id=message['id'], format='full'
        ).execute()

        headers = {h['name']: h['value'] for h in msg['payload']['headers']}

        # ── Filter automated/marketing emails ──────────────────────────────
        if is_automated_email(headers):
            sender = headers.get('From', 'unknown')
            subject = headers.get('Subject', '')
            print(f"[SKIP] Automated email from {sender} — "{subject}"")
            self.processed_ids.add(message['id'])
            return None

        # ── Extract full body ──────────────────────────────────────────────
        body = get_email_body(msg)

        content = f'''---
type: email
from: {headers.get('From', 'Unknown')}
subject: {headers.get('Subject', 'No Subject')}
received: {datetime.now().isoformat()}
priority: high
status: pending
---

## Email Content
{body}

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
'''
        filepath = self.needs_action / f'EMAIL_{message["id"]}.md'
        filepath.write_text(content, encoding='utf-8')
        self.processed_ids.add(message['id'])
        return filepath

if __name__ == "__main__":
    load_dotenv()
    vault_path = os.environ.get("VAULT_PATH", "/opt/ai_employee_vault")
    token_path = os.path.join(vault_path, "token.json")

    print("Starting WEBXES Gmail Watcher Loop...")
    watcher = GmailWatcher(vault_path=vault_path, credentials_path=token_path)

    while True:
        try:
            updates = watcher.check_for_updates()
            if updates:
                print(f"Found {len(updates)} new emails! Processing...")
                for msg in updates:
                    filepath = watcher.create_action_file(msg)
                    if filepath:
                        print(f"Created action file: {filepath}")
        except Exception as e:
            print(f"Error checking emails: {e}")

        time.sleep(30)
