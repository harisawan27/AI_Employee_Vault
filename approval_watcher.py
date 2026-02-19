import os
import time
import base64
import re
from email.message import EmailMessage
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("approval_watcher")

VAULT_PATH = Path("/opt/ai_employee_vault")
APPROVED_DIR = VAULT_PATH / "Approved"
DONE_DIR = VAULT_PATH / "Done"
TOKEN_PATH = VAULT_PATH / "token.json"

def send_email(creds, recipient, subject, body):
    try:
        service = build('gmail', 'v1', credentials=creds)
        message = EmailMessage()
        message.set_content(body)
        message['To'] = recipient
        message['Subject'] = subject
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId="me", body={'raw': encoded_message}).execute()
        return True
    except Exception as e:
        logger.error(f'GMAIL ERROR: {e}')
        return False

def process_approvals():
    if not TOKEN_PATH.exists():
        return

    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH))
    
    # Search all subfolders in Approved
    for file_path in APPROVED_DIR.rglob("*.md"):
        if file_path.is_dir(): continue
        
        logger.info(f"Parsing approved file: {file_path.name}")
        content = file_path.read_text()
        
        # 1. Extract Recipient (Handles **To:** Name <email@com> or plain email)
        to_match = re.search(r"(?i)\*\*To:\*\*\s*.*?<(.+?)>", content) or re.search(r"(?i)to:\s*(.+)", content)
        # 2. Extract Subject
        sub_match = re.search(r"(?i)\*\*Subject:\*\*\s*(.*)", content) or re.search(r"(?i)subject:\s*(.*)", content)
        
        to_email = to_match.group(1).strip() if to_match else ""
        subject = sub_match.group(1).strip() if sub_match else "Re: Inquiry"

        # 3. Extract CLEAN Body
        # We split by '---' and find the block that contains the actual message
        parts = content.split("---")
        clean_body = ""
        
        if len(parts) >= 3:
            # The actual message is usually in the 3rd section (between the 2nd and 3rd ---)
            raw_body = parts[2].strip()
            # Remove any lingering Markdown headers from the body block
            clean_body = re.sub(r"(?i)# Draft Reply.*?\n", "", raw_body)
            clean_body = re.sub(r"(?i)\*\*To:\*\*.*?\n", "", clean_body)
            clean_body = re.sub(r"(?i)\*\*Subject:\*\*.*?\n", "", clean_body)
            clean_body = re.sub(r"(?i)\*\*Generated:\*\*.*?\n", "", clean_body)
            clean_body = clean_body.strip()
        
        # If the split logic fails, fallback to simple header removal
        if not clean_body or len(clean_body) < 10:
            clean_body = content.split("# Draft Reply")[-1].split("---")[0].strip()

        if to_email and clean_body:
            logger.info(f"Shipping email to {to_email}...")
            if send_email(creds, to_email, subject, clean_body):
                # Ensure Done directory exists
                DONE_DIR.mkdir(parents=True, exist_ok=True)
                dest_path = DONE_DIR / file_path.name
                file_path.rename(dest_path)
                logger.info(f"SUCCESS: {file_path.name} moved to Done/")
        else:
            logger.warning(f"SKIP: Missing data in {file_path.name}")

if __name__ == "__main__":
    logger.info("WEBXES AI Approval Watcher - V5 Ready")
    while True:
        process_approvals()
        time.sleep(10)
