"""
WEBXES Tech — Vault file parser utilities

Parses markdown files with YAML frontmatter, extracts editable content,
and validates file paths against directory traversal.
"""

import re
from pathlib import Path

from config import VAULT_PATH


def validate_vault_path(path_str: str) -> Path:
    """Validate that a path is within the vault. Returns resolved Path.

    Raises ValueError on directory traversal attempts.
    """
    # Resolve relative to vault
    candidate = (VAULT_PATH / path_str).resolve()
    vault_resolved = VAULT_PATH.resolve()
    if not str(candidate).startswith(str(vault_resolved)):
        raise ValueError(f"Path traversal blocked: {path_str}")
    return candidate


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    """Parse a markdown file with YAML-style frontmatter.

    Returns (metadata_dict, content_body).
    Frontmatter is delimited by --- lines at the top.
    """
    text = path.read_text(encoding="utf-8")

    if not text.startswith("---"):
        return {}, text

    # Find closing ---
    end_match = re.search(r"\n---\s*\n", text[3:])
    if not end_match:
        return {}, text

    front_end = end_match.end() + 3
    front_text = text[3:front_end - 4].strip()
    body = text[front_end:].strip()

    # Parse simple key: value frontmatter
    metadata = {}
    for line in front_text.split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            metadata[key.strip()] = value.strip()

    return metadata, body


def extract_editable_content(content: str, action_type: str = "") -> str:
    """Extract the main editable draft body from content.

    Strips metadata sections and instructions, returning just the draft text.
    """
    lines = content.split("\n")
    in_draft = False
    draft_lines = []

    for line in lines:
        # Common draft markers
        if any(marker in line.lower() for marker in ["## draft", "## content", "## body", "## message"]):
            in_draft = True
            continue
        if in_draft and line.startswith("## "):
            break  # Next section
        if in_draft:
            draft_lines.append(line)

    if draft_lines:
        return "\n".join(draft_lines).strip()

    # No draft section found — return full content
    return content


def rebuild_file(metadata: dict, content: str) -> str:
    """Rebuild a markdown file from metadata and content body."""
    if not metadata:
        return content

    front_lines = ["---"]
    for key, value in metadata.items():
        front_lines.append(f"{key}: {value}")
    front_lines.append("---")
    front_lines.append("")

    return "\n".join(front_lines) + content


def get_file_id(path: Path) -> str:
    """Generate a URL-safe ID from a vault-relative file path."""
    try:
        rel = path.resolve().relative_to(VAULT_PATH.resolve())
        return str(rel).replace("\\", "/").replace("/", "__").replace(" ", "_")
    except ValueError:
        return path.stem


def id_to_path(file_id: str) -> Path:
    """Convert a file ID back to a vault path."""
    rel_path = file_id.replace("__", "/").replace("_", " ")
    return VAULT_PATH / rel_path


def list_vault_files(directory: Path, pattern: str = "*.md") -> list[dict]:
    """List markdown files in a vault directory with metadata."""
    if not directory.exists():
        return []

    files = []
    for f in sorted(directory.rglob(pattern), key=lambda p: p.stat().st_mtime, reverse=True):
        metadata, body = parse_frontmatter(f)
        rel_path = f.relative_to(VAULT_PATH)
        # Determine subdomain from path
        parts = rel_path.parts
        domain = parts[1] if len(parts) > 2 else "general"

        files.append({
            "id": get_file_id(f),
            "filename": f.name,
            "path": str(rel_path).replace("\\", "/"),
            "domain": domain,
            "metadata": metadata,
            "preview": body[:200] if body else "",
            "modified": f.stat().st_mtime,
        })
    return files
