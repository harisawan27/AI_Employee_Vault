"""
WEBXES Tech — Multi-Platform Social Media Poster

Playwright-based posters for Facebook, Instagram, and Twitter (X).
Follows the same pattern as linkedin_poster.py: cookies, login, DRY_RUN.

Each poster: create_post(text, image_path) + get_engagement_summary()
All wrapped with @retry, logged via audit_log().
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from audit_logger import audit_log
from retry_handler import retry

load_dotenv()

VAULT_PATH = Path(os.getenv("VAULT_PATH", r"F:\AI_Employee_Vault"))
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"

logger = logging.getLogger("SocialMediaPoster")


class BaseSocialPoster(ABC):
    """Base class for Playwright-based social media posters."""

    platform: str = "unknown"

    def __init__(self, session_path: Path):
        self.session_path = session_path
        self.session_path.mkdir(parents=True, exist_ok=True)
        self.cookies_file = self.session_path / "cookies.json"
        self.browser = None
        self.context = None
        self.page = None

    def _ensure_playwright(self):
        from playwright.sync_api import sync_playwright
        self._playwright = sync_playwright().start()

    def _save_cookies(self):
        if self.context:
            cookies = self.context.cookies()
            self.cookies_file.write_text(json.dumps(cookies, indent=2))

    def _load_cookies(self):
        if self.cookies_file.exists():
            return json.loads(self.cookies_file.read_text())
        return None

    def login(self, headless: bool = False):
        """Launch browser with saved session. First run requires manual login."""
        self._ensure_playwright()
        self.browser = self._playwright.chromium.launch(headless=headless)

        cookies = self._load_cookies()
        self.context = self.browser.new_context()
        if cookies:
            logger.info(f"[{self.platform}] Loading saved session...")
            self.context.add_cookies(cookies)
        else:
            logger.info(f"[{self.platform}] No saved session. Manual login required.")

        self.page = self.context.new_page()
        self._navigate_and_verify_login()
        logger.info(f"[{self.platform}] Session active.")

    @abstractmethod
    def _navigate_and_verify_login(self):
        """Navigate to the platform and verify/complete login."""
        ...

    @abstractmethod
    def _do_post(self, text: str, image_path: str = None) -> bool:
        """Platform-specific posting logic. Returns True on success."""
        ...

    @abstractmethod
    def _scrape_engagement(self) -> dict:
        """Scrape recent engagement metrics from the platform."""
        ...

    @retry(max_retries=2, base_delay=2.0)
    def create_post(self, text: str, image_path: str = None) -> bool:
        """Create a post on this platform."""
        if DRY_RUN:
            logger.info(f"[DRY_RUN] Would post to {self.platform}:\n{text[:200]}...")
            audit_log("social_media", "dry_run_post",
                      {"platform": self.platform, "text": text[:200]})
            return True

        if not self.page:
            logger.error(f"[{self.platform}] Not logged in. Call login() first.")
            return False

        try:
            success = self._do_post(text, image_path)
            if success:
                self._save_cookies()
                audit_log("social_media", "posted",
                          {"platform": self.platform, "text": text[:200]})
            return success
        except Exception as e:
            audit_log("social_media", "post_failed",
                      {"platform": self.platform}, status="error", error=str(e))
            raise

    def get_engagement_summary(self) -> dict:
        """Get engagement metrics for recent posts."""
        if DRY_RUN:
            return {"platform": self.platform, "note": "DRY_RUN — no real data"}
        try:
            return self._scrape_engagement()
        except Exception as e:
            logger.error(f"[{self.platform}] Engagement scrape failed: {e}")
            return {"platform": self.platform, "error": str(e)}

    def close(self):
        if self.browser:
            self._save_cookies()
            self.browser.close()
        if hasattr(self, "_playwright"):
            self._playwright.stop()


class FacebookPoster(BaseSocialPoster):
    platform = "facebook"

    def __init__(self):
        session_path = Path(os.getenv(
            "FACEBOOK_SESSION_PATH",
            r"C:\Users\lenovo\.config\webxes\facebook_session"))
        super().__init__(session_path)

    def _navigate_and_verify_login(self):
        self.page.goto("https://www.facebook.com/")
        self.page.wait_for_load_state("networkidle")
        if "/login" in self.page.url:
            logger.info("[facebook] Please log in manually...")
            self.page.wait_for_url("**/facebook.com/**", timeout=300000)
            self._save_cookies()

    def _do_post(self, text: str, image_path: str = None) -> bool:
        self.page.goto("https://www.facebook.com/")
        self.page.wait_for_load_state("networkidle")
        # Click "What's on your mind?" composer
        self.page.click('[aria-label="Create a post"]', timeout=10000)
        self.page.wait_for_timeout(2000)
        composer = self.page.locator('[role="textbox"][contenteditable="true"]')
        composer.fill(text)
        if image_path and Path(image_path).exists():
            self.page.set_input_files('input[type="file"]', image_path)
            self.page.wait_for_timeout(3000)
        self.page.click('[aria-label="Post"]')
        self.page.wait_for_timeout(5000)
        logger.info("[facebook] Post published.")
        return True

    def _scrape_engagement(self) -> dict:
        self.page.goto("https://www.facebook.com/me")
        self.page.wait_for_load_state("networkidle")
        return {"platform": "facebook", "note": "Engagement scrape — check page manually"}


class InstagramPoster(BaseSocialPoster):
    platform = "instagram"

    def __init__(self):
        session_path = Path(os.getenv(
            "INSTAGRAM_SESSION_PATH",
            r"C:\Users\lenovo\.config\webxes\instagram_session"))
        super().__init__(session_path)

    def _navigate_and_verify_login(self):
        self.page.goto("https://www.instagram.com/")
        self.page.wait_for_load_state("networkidle")
        if "/accounts/login" in self.page.url:
            logger.info("[instagram] Please log in manually...")
            self.page.wait_for_url("**/instagram.com/**", timeout=300000)
            self._save_cookies()

    def _generate_image_card(self, text: str) -> str:
        """Generate a simple branded image card with Pillow."""
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (1080, 1080), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 36)
            small_font = ImageFont.truetype("arial.ttf", 24)
        except OSError:
            font = ImageFont.load_default()
            small_font = font

        # Word-wrap text
        lines = []
        words = text.split()
        current_line = ""
        for word in words:
            test = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] > 980:
                lines.append(current_line)
                current_line = word
            else:
                current_line = test
        if current_line:
            lines.append(current_line)

        y = 200
        for line in lines[:12]:
            draw.text((50, y), line, fill="white", font=font)
            y += 50

        draw.text((50, 980), "WEBXES Tech", fill=(100, 200, 255), font=small_font)

        out_path = str(VAULT_PATH / "Logs" / f"ig_card_{datetime.now():%Y%m%d_%H%M%S}.png")
        img.save(out_path)
        return out_path

    def _do_post(self, text: str, image_path: str = None) -> bool:
        if not image_path:
            image_path = self._generate_image_card(text)

        self.page.goto("https://www.instagram.com/")
        self.page.wait_for_load_state("networkidle")
        # Click new post button
        self.page.click('[aria-label="New post"]', timeout=10000)
        self.page.wait_for_timeout(2000)
        self.page.set_input_files('input[type="file"]', image_path)
        self.page.wait_for_timeout(3000)
        # Next through crop/filter screens
        for _ in range(2):
            next_btn = self.page.locator('button:has-text("Next")')
            if next_btn.is_visible():
                next_btn.click()
                self.page.wait_for_timeout(2000)
        # Add caption
        caption_box = self.page.locator('[aria-label="Write a caption..."]')
        if caption_box.is_visible():
            caption_box.fill(text)
        self.page.click('button:has-text("Share")')
        self.page.wait_for_timeout(5000)
        logger.info("[instagram] Post published.")
        return True

    def _scrape_engagement(self) -> dict:
        return {"platform": "instagram", "note": "Engagement scrape — check insights manually"}


class TwitterPoster(BaseSocialPoster):
    platform = "twitter"

    def __init__(self):
        session_path = Path(os.getenv(
            "TWITTER_SESSION_PATH",
            r"C:\Users\lenovo\.config\webxes\twitter_session"))
        super().__init__(session_path)

    def _navigate_and_verify_login(self):
        self.page.goto("https://x.com/home")
        self.page.wait_for_load_state("networkidle")
        if "/login" in self.page.url or "/i/flow/login" in self.page.url:
            logger.info("[twitter] Please log in manually...")
            self.page.wait_for_url("**/home**", timeout=300000)
            self._save_cookies()

    def _do_post(self, text: str, image_path: str = None) -> bool:
        self.page.goto("https://x.com/compose/post")
        self.page.wait_for_load_state("networkidle")
        editor = self.page.locator('[data-testid="tweetTextarea_0"]')
        editor.fill(text)
        if image_path and Path(image_path).exists():
            self.page.set_input_files('input[type="file"]', image_path)
            self.page.wait_for_timeout(3000)
        self.page.click('[data-testid="tweetButton"]')
        self.page.wait_for_timeout(5000)
        logger.info("[twitter] Post published.")
        return True

    def _scrape_engagement(self) -> dict:
        return {"platform": "twitter", "note": "Engagement scrape — check analytics manually"}


POSTER_MAP = {
    "facebook": FacebookPoster,
    "instagram": InstagramPoster,
    "twitter": TwitterPoster,
}


def post_from_approved_file(filepath: Path, platform: str = None) -> bool:
    """Read an approved social media file and post to the specified platform."""
    content = filepath.read_text(encoding="utf-8")

    # Extract platform from frontmatter if not provided
    if not platform:
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                for line in parts[1].split("\n"):
                    if line.strip().startswith("platform:"):
                        platform = line.split(":", 1)[1].strip()
                        break
        if not platform:
            platform = "facebook"  # default

    # Extract post text (after frontmatter)
    parts = content.split("---", 2)
    post_text = parts[2].strip() if len(parts) >= 3 else content.strip()

    # Strip instructions section
    if "## Instructions for CEO" in post_text:
        post_text = post_text.split("## Instructions for CEO")[0].strip()

    poster_cls = POSTER_MAP.get(platform)
    if not poster_cls:
        logger.error(f"Unknown platform: {platform}")
        return False

    poster = poster_cls()
    try:
        poster.login(headless=True)
        return poster.create_post(post_text)
    finally:
        poster.close()
