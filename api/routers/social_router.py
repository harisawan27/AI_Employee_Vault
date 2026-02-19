"""
WEBXES Tech — Social Media Generation Router

POST /api/social/generate
Accepts a natural language message (e.g. "LinkedIn post about web design"),
calls Gemini API to generate the post, writes it to Pending_Approval/social_media/,
and returns the draft for immediate display on the dashboard.
"""

import hashlib
import os
import re
from datetime import datetime, timedelta

from google import genai
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import verify_token
from api.utils.file_parser import rebuild_file, get_file_id

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config import PENDING_APPROVAL
from audit_logger import audit_log

router = APIRouter(prefix="/api/social", tags=["social"])

SUPPORTED_PLATFORMS = ["linkedin", "facebook", "instagram", "twitter"]

SYSTEM_PROMPT = """You are the social media content writer for WEBXES Tech, a digital agency.
Write engaging, professional social media posts.
Rules:
- Match the tone and length to the platform (LinkedIn = professional/longer, Twitter = concise/punchy, Instagram = visual/hashtag-heavy, Facebook = conversational)
- Include relevant hashtags
- Keep the WEBXES Tech brand voice: innovative, approachable, expert
- Do NOT include any metadata, frontmatter, or instructions — output ONLY the post text
- For LinkedIn: 150-300 words. For Twitter: under 280 characters. For Instagram: 100-200 words with hashtags. For Facebook: 100-250 words.
"""


class GenerateRequest(BaseModel):
    message: str


class GenerateResponse(BaseModel):
    id: str
    platform: str
    content: str
    filename: str
    status: str = "pending_approval"


def _detect_platform(message: str) -> str:
    """Detect platform from the user's message."""
    msg_lower = message.lower()
    for platform in SUPPORTED_PLATFORMS:
        if platform in msg_lower:
            return platform
    # Aliases
    if "tweet" in msg_lower or "x.com" in msg_lower:
        return "twitter"
    if "ig " in msg_lower or "insta " in msg_lower:
        return "instagram"
    if "fb " in msg_lower:
        return "facebook"
    # Default to LinkedIn
    return "linkedin"


def _extract_topic(message: str, platform: str) -> str:
    """Extract the topic from the user's message by stripping platform references."""
    topic = message
    for word in SUPPORTED_PLATFORMS + ["post", "about", "write", "create", "make", "generate", "a", "an", "for", "on", "tweet", "ig", "insta", "fb"]:
        topic = re.sub(rf"\b{word}\b", "", topic, flags=re.IGNORECASE)
    topic = re.sub(r"\s+", " ", topic).strip()
    return topic if topic else message


@router.post("/generate", response_model=GenerateResponse)
def generate_social_post(body: GenerateRequest, user: str = Depends(verify_token)):
    """Generate a social media post using Gemini API and save to Pending_Approval."""
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    platform = _detect_platform(message)
    topic = _extract_topic(message, platform)

    # Call Gemini API
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Gemini API key not configured. Set GEMINI_API_KEY in .env")

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=f"{SYSTEM_PROMPT}\n\nWrite a {platform} post about: {topic}",
        )
        post_content = response.text.strip()
    except Exception as e:
        audit_log("social_media", "generate_failed", {"platform": platform, "topic": topic}, status="error", error=str(e))
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

    # Build approval file
    now = datetime.now()
    expires = now + timedelta(hours=24)
    file_hash = hashlib.md5(f"{platform}_{topic}_{now.isoformat()}".encode()).hexdigest()[:12]
    filename = f"SOCIAL_{platform.upper()}_{file_hash}.md"

    metadata = {
        "type": "social_media",
        "action_type": "social_media",
        "platform": platform,
        "topic": topic,
        "generated": now.isoformat(),
        "expires": expires.isoformat(),
        "generated_by": "ceo_dashboard",
        "status": "pending_approval",
    }

    body_text = f"""## {platform.title()} Post — Pending Approval

**Platform:** {platform}
**Topic:** {topic}
**Generated:** {now.strftime('%Y-%m-%d %H:%M')}
**Expires:** 24 hours from generation

---

{post_content}

---

## Instructions for CEO
- **To approve:** Click Approve on the dashboard
- **To reject:** Click Reject on the dashboard
- **To edit:** Modify post content before approving
"""

    file_content = rebuild_file(metadata, body_text)

    # Write to Pending_Approval/social_media/
    dest_dir = PENDING_APPROVAL / "social_media"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename
    dest_path.write_text(file_content, encoding="utf-8")

    audit_log("social_media", "generated", {
        "platform": platform,
        "topic": topic,
        "file": filename,
        "source": "ceo_dashboard",
    })

    return GenerateResponse(
        id=get_file_id(dest_path),
        platform=platform,
        content=post_content,
        filename=filename,
    )
