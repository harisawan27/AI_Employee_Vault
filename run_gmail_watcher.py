# run_gmail_watcher.py - Entry point for the Gmail Watcher
# Handles OAuth flow, token refresh, and starts the watcher loop.

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from gmail_watcher import GmailWatcher

# Load environment variables
load_dotenv()

# Configuration from .env
VAULT_PATH = os.getenv('VAULT_PATH', r'F:\AI_Employee_Vault')
CREDENTIALS_PATH = os.getenv('GMAIL_CREDENTIALS_PATH')
TOKEN_PATH = os.getenv('GMAIL_TOKEN_PATH')

# Gmail API scope - read-only for Bronze tier
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(VAULT_PATH) / 'Logs' / 'gmail_watcher.log')
    ]
)
logger = logging.getLogger('GmailWatcherRunner')


def authenticate() -> str:
    """Handle OAuth flow and return path to valid token file.

    First run:  Opens browser for Google sign-in, saves token.json.
    Later runs: Loads existing token, refreshes if expired.
    """
    creds = None

    # Check for existing token
    if TOKEN_PATH and Path(TOKEN_PATH).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # If no valid creds, run the OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info('Token expired, refreshing...')
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH or not Path(CREDENTIALS_PATH).exists():
                logger.error(
                    f'credentials.json not found at: {CREDENTIALS_PATH}\n'
                    'Download it from Google Cloud Console → APIs & Services → Credentials'
                )
                sys.exit(1)

            logger.info('No token found. Opening browser for Google sign-in...')
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the token for future runs
        token_path = Path(TOKEN_PATH)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())
        logger.info(f'Token saved to {TOKEN_PATH}')

    return TOKEN_PATH


def main():
    logger.info('=== WEBXES Tech Gmail Watcher Starting ===')
    logger.info(f'Vault: {VAULT_PATH}')
    logger.info(f'DRY_RUN: {os.getenv("DRY_RUN", "true")}')

    # Ensure Needs_Action folder exists
    needs_action = Path(VAULT_PATH) / 'Needs_Action'
    needs_action.mkdir(exist_ok=True)

    # Authenticate (first run opens browser, later runs use saved token)
    token_path = authenticate()
    logger.info('Authentication successful.')

    # Start the watcher
    watcher = GmailWatcher(
        vault_path=VAULT_PATH,
        credentials_path=token_path
    )

    logger.info('Gmail Watcher is now running. Polling every 120 seconds.')
    logger.info('Press Ctrl+C to stop.')

    try:
        watcher.run()
    except KeyboardInterrupt:
        logger.info('Gmail Watcher stopped by user.')
    except Exception as e:
        logger.error(f'Fatal error: {e}', exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
