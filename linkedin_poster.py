# linkedin_poster.py - LinkedIn Auto-Poster using Playwright
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger('LinkedInPoster')

VAULT_PATH = Path(os.getenv('VAULT_PATH', r'F:\AI_Employee_Vault'))
SESSION_PATH = Path(os.getenv('LINKEDIN_SESSION_PATH',
                               r'C:\Users\lenovo\.config\webxes\linkedin_session'))
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'


class LinkedInPoster:
    """Automates LinkedIn posting via Playwright with persistent browser session."""

    def __init__(self):
        self.session_path = SESSION_PATH
        self.session_path.mkdir(parents=True, exist_ok=True)
        self.cookies_file = self.session_path / 'cookies.json'
        self.browser = None
        self.context = None
        self.page = None

    def _ensure_playwright(self):
        """Lazy-import playwright to avoid import errors when not posting."""
        from playwright.sync_api import sync_playwright
        self._playwright = sync_playwright().start()

    def login(self, headless: bool = False):
        """Launch browser with saved session. First run requires manual login."""
        self._ensure_playwright()
        self.browser = self._playwright.chromium.launch(headless=headless)

        if self.cookies_file.exists():
            logger.info('Loading saved LinkedIn session...')
            self.context = self.browser.new_context()
            cookies = json.loads(self.cookies_file.read_text())
            self.context.add_cookies(cookies)
        else:
            logger.info('No saved session. Manual login required.')
            self.context = self.browser.new_context()

        self.page = self.context.new_page()
        self.page.goto('https://www.linkedin.com/feed/')
        self.page.wait_for_load_state('networkidle')

        # Check if we're logged in
        if '/login' in self.page.url or '/checkpoint' in self.page.url:
            logger.info('Please log in manually in the browser window...')
            # Wait for user to complete login (up to 5 minutes)
            self.page.wait_for_url('**/feed/**', timeout=300000)
            logger.info('Login detected. Saving session cookies...')
            self._save_cookies()

        logger.info('LinkedIn session active.')

    def _save_cookies(self):
        """Save browser cookies for session persistence."""
        cookies = self.context.cookies()
        self.cookies_file.write_text(json.dumps(cookies, indent=2))
        logger.info(f'Cookies saved to {self.cookies_file}')

    def create_post(self, text: str) -> bool:
        """Create a LinkedIn post with the given text.

        Returns True if post was created (or would be in DRY_RUN), False on error.
        """
        if DRY_RUN:
            logger.info(f'[DRY_RUN] Would post to LinkedIn:\n{text[:200]}...')
            self._log_action('dry_run_post', text)
            return True

        if not self.page:
            logger.error('Not logged in. Call login() first.')
            return False

        try:
            # Click "Start a post" button
            self.page.click('button:has-text("Start a post")')
            self.page.wait_for_selector('.ql-editor', timeout=10000)

            # Type the post content
            editor = self.page.locator('.ql-editor')
            editor.fill(text)

            # Click Post button
            self.page.click('button:has-text("Post"):not([disabled])')
            self.page.wait_for_timeout(3000)

            logger.info('LinkedIn post published successfully.')
            self._save_cookies()
            self._log_action('posted', text)
            return True

        except Exception as e:
            logger.error(f'Failed to create LinkedIn post: {e}')
            self._log_action('post_failed', text, str(e))
            return False

    def _log_action(self, action: str, text: str, error: str = ''):
        """Log posting action to vault."""
        now = datetime.now()
        log_file = VAULT_PATH / 'Logs' / 'linkedin_poster.log'
        log_file.parent.mkdir(exist_ok=True)
        entry = f'[{now.isoformat()}] {action}: {text[:100]}...'
        if error:
            entry += f' ERROR: {error}'
        entry += '\n'
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(entry)

    def close(self):
        """Clean up browser resources."""
        if self.browser:
            self._save_cookies()
            self.browser.close()
        if hasattr(self, '_playwright'):
            self._playwright.stop()


def post_from_approved_file(filepath: Path) -> bool:
    """Read an approved social media file and post its content."""
    content = filepath.read_text(encoding='utf-8')

    # Extract post text (everything after the frontmatter)
    parts = content.split('---', 2)
    if len(parts) >= 3:
        post_text = parts[2].strip()
    else:
        post_text = content.strip()

    poster = LinkedInPoster()
    try:
        poster.login(headless=True)
        return poster.create_post(post_text)
    finally:
        poster.close()
