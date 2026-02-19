import os
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from pathlib import Path
from base_watcher import BaseWatcher
from datetime import datetime
from dotenv import load_dotenv

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

    def create_action_file(self, message) -> Path:
        msg = self.service.users().messages().get(
            userId='me', id=message['id']
        ).execute()

        headers = {h['name']: h['value'] for h in msg['payload']['headers']}

        content = f'''---
type: email
from: {headers.get('From', 'Unknown')}
subject: {headers.get('Subject', 'No Subject')}
received: {datetime.now().isoformat()}
priority: high
status: pending
---

## Email Content
{msg.get('snippet', '')}

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
                    print(f"Created action file: {filepath}")
        except Exception as e:
            print(f"Error checking emails: {e}")

        time.sleep(30)
