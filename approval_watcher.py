# approval_watcher.py - Monitors Approved/ and Rejected/ folders
import sys
import time
import json
import logging
import shutil
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from config import VAULT_PATH, DRY_RUN, IS_CLOUD

logger = logging.getLogger('ApprovalWatcher')

# Guard: approval_watcher must only run locally (it sends emails, posts to social media)
if IS_CLOUD:
    print("ERROR: approval_watcher.py must not run on cloud. "
          "Cloud zone handles drafts only. Exiting.")
    sys.exit(1)

DOMAINS = ['email', 'payments', 'social_media']

from audit_logger import audit_log
from retry_handler import CircuitBreaker

gmail_cb = CircuitBreaker("gmail", failure_threshold=5, recovery_timeout=300)
social_cb = CircuitBreaker("social_media", failure_threshold=5, recovery_timeout=300)


def send_email_via_mcp(to: str, subject: str, body: str) -> bool:
    """Send an email using the Gmail MCP server directly."""
    proc = subprocess.Popen(
        'npx @gongrzhe/server-gmail-autoauth-mcp',
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        shell=True
    )

    def mcp_call(msg_id, method, params):
        proc.stdin.write((json.dumps({
            'jsonrpc': '2.0', 'id': msg_id,
            'method': method, 'params': params
        }) + '\n').encode())
        proc.stdin.flush()
        result = [None]
        def read():
            result[0] = proc.stdout.readline().decode()
        t = threading.Thread(target=read)
        t.start()
        t.join(timeout=30)
        return json.loads(result[0]) if result[0] else None

    try:
        # Initialize MCP
        init = mcp_call(1, 'initialize', {
            'protocolVersion': '2024-11-05',
            'capabilities': {},
            'clientInfo': {'name': 'approval_watcher', 'version': '1.0'}
        })
        if not init:
            logger.error('Gmail MCP server failed to initialize')
            return False

        # Send email (to must be array)
        to_list = [to] if isinstance(to, str) else to
        resp = mcp_call(2, 'tools/call', {
            'name': 'send_email',
            'arguments': {'to': to_list, 'subject': subject, 'body': body}
        })
        if resp and 'error' not in str(resp.get('result', {}).get('content', [{}])[0].get('text', '')).lower():
            logger.info(f'Email sent via Gmail MCP to {to}')
            return True
        else:
            logger.error(f'Gmail MCP send failed: {resp}')
            return False
    except Exception as e:
        logger.error(f'Gmail MCP error: {e}')
        return False
    finally:
        proc.terminate()


def extract_email_body(filepath: Path) -> str:
    """Extract the email body from an approved email file."""
    text = filepath.read_text(encoding='utf-8')
    parts = text.split('---')
    if len(parts) >= 3:
        # Body is between the second and third --- (after frontmatter and after header section)
        content = '---'.join(parts[2:])
        # Remove the "Instructions for CEO" section
        if '## Instructions for CEO' in content:
            content = content.split('## Instructions for CEO')[0]
        # Remove "## Email" header line if present
        lines = content.strip().split('\n')
        body_lines = []
        skip_header = True
        for line in lines:
            if skip_header and (line.startswith('## Email') or line.startswith('**To:**') or
                               line.startswith('**Subject:**') or line.startswith('**Generated:**') or
                               line.startswith('**Expires:**') or line.strip() == ''):
                continue
            skip_header = False
            if line.strip() == '---':
                continue
            body_lines.append(line)
        return '\n'.join(body_lines).strip()
    return text


def parse_frontmatter(filepath: Path) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    text = filepath.read_text(encoding='utf-8')
    if not text.startswith('---'):
        return {}
    parts = text.split('---', 2)
    if len(parts) < 3:
        return {}
    meta = {}
    for line in parts[1].strip().split('\n'):
        if ':' in line:
            key, _, val = line.partition(':')
            meta[key.strip()] = val.strip()
    return meta


def execute_approved(filepath: Path, meta: dict):
    """Execute the action described in an approved file."""
    action_type = meta.get('action_type', meta.get('type', 'unknown'))
    platform = meta.get('platform', 'linkedin')

    if DRY_RUN:
        logger.info(f'[DRY_RUN] Would execute {action_type} from {filepath.name}')
        audit_log("approval", "dry_run_execute",
                  {"file": filepath.name, "action_type": action_type})
        return

    if action_type == 'social_media':
        with social_cb:
            if platform == 'linkedin':
                from linkedin_poster import post_from_approved_file
                post_from_approved_file(filepath)
            else:
                from social_media_poster import post_from_approved_file as social_post
                social_post(filepath, platform=platform)
        audit_log("social_media", "posted",
                  {"file": filepath.name, "platform": platform})

    elif action_type == 'email':
        to = meta.get('to', '')
        subject = meta.get('subject', '').strip('"').strip("'")
        body = extract_email_body(filepath)
        if to and body:
            with gmail_cb:
                success = send_email_via_mcp(to, subject, body)
            if success:
                audit_log("email", "sent", {"to": to, "subject": subject})
            else:
                logger.error(f'Failed to send email to {to} from {filepath.name}')
                audit_log("email", "send_failed",
                          {"to": to, "subject": subject}, status="error")
        else:
            logger.error(f'Missing to/body in {filepath.name}')

    elif action_type == 'payment':
        logger.info(f'Payment action approved: {filepath.name}. '
                     'Manual execution required — logged for CEO review.')
        audit_log("payment", "manual_required", {"file": filepath.name})

    else:
        logger.warning(f'Unknown action type "{action_type}" in {filepath.name}')
        audit_log("approval", "unknown_type",
                  {"file": filepath.name, "action_type": action_type}, status="warning")


def process_approved():
    """Check Approved/ subdirectories for new files and execute them."""
    approved_dir = VAULT_PATH / 'Approved'
    done_dir = VAULT_PATH / 'Done'
    done_dir.mkdir(exist_ok=True)

    for domain in DOMAINS:
        domain_dir = approved_dir / domain
        if not domain_dir.exists():
            continue
        for filepath in domain_dir.glob('*.md'):
            logger.info(f'Processing approved: {filepath.name}')
            meta = parse_frontmatter(filepath)
            try:
                execute_approved(filepath, meta)
                # Move to Done
                dest = done_dir / filepath.name
                shutil.move(str(filepath), str(dest))
                logger.info(f'Moved {filepath.name} -> Done/')
                log_action('approved', filepath.name, meta)
            except Exception as e:
                logger.error(f'Error executing {filepath.name}: {e}')
                log_action('error', filepath.name, meta, str(e))
                audit_log("approval", "execute_error",
                          {"file": filepath.name}, status="error", error=str(e))


def process_rejected():
    """Check Rejected/ subdirectories for new files and log them."""
    rejected_dir = VAULT_PATH / 'Rejected'
    done_dir = VAULT_PATH / 'Done'
    done_dir.mkdir(exist_ok=True)

    for domain in DOMAINS:
        domain_dir = rejected_dir / domain
        if not domain_dir.exists():
            continue
        for filepath in domain_dir.glob('*.md'):
            logger.info(f'Processing rejected: {filepath.name}')
            meta = parse_frontmatter(filepath)
            log_action('rejected', filepath.name, meta)
            audit_log("approval", "rejected", {"file": filepath.name,
                      "action_type": meta.get("action_type", "unknown")})
            dest = done_dir / filepath.name
            shutil.move(str(filepath), str(dest))
            logger.info(f'Moved {filepath.name} -> Done/')


def log_action(result: str, filename: str, meta: dict, error: str = ''):
    """Write a log entry for the approval action."""
    now = datetime.now()
    log_file = VAULT_PATH / 'Logs' / 'approval_watcher.log'
    log_file.parent.mkdir(exist_ok=True)
    action_type = meta.get('action_type', meta.get('type', 'unknown'))
    entry = f'[{now.isoformat()}] {result.upper()}: {filename} (type={action_type})'
    if error:
        entry += f' ERROR: {error}'
    entry += '\n'
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(entry)


def check_expired():
    """Move expired approval requests to Rejected/ with reason: expired."""
    pending_dir = VAULT_PATH / 'Pending_Approval'
    rejected_dir = VAULT_PATH / 'Rejected'
    now = datetime.now()

    for domain in DOMAINS:
        domain_dir = pending_dir / domain
        if not domain_dir.exists():
            continue
        for filepath in domain_dir.glob('*.md'):
            meta = parse_frontmatter(filepath)
            expiry = meta.get('expires', '')
            if expiry:
                try:
                    expiry_dt = datetime.fromisoformat(expiry)
                    if now > expiry_dt:
                        logger.info(f'Expired: {filepath.name}')
                        dest = rejected_dir / domain / filepath.name
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(filepath), str(dest))
                except ValueError:
                    pass


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(VAULT_PATH / 'Logs' / 'approval_watcher.log')
        ]
    )

    logger.info('=== WEBXES Tech Approval Watcher Starting ===')
    logger.info(f'Vault: {VAULT_PATH}')
    logger.info(f'DRY_RUN: {DRY_RUN}')

    # Ensure directories exist
    for base in ['Pending_Approval', 'Approved', 'Rejected']:
        for domain in DOMAINS:
            (VAULT_PATH / base / domain).mkdir(parents=True, exist_ok=True)

    logger.info('Approval Watcher is running. Polling every 30 seconds. Ctrl+C to stop.')

    try:
        while True:
            check_expired()
            process_approved()
            process_rejected()
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info('Approval Watcher stopped by user.')


if __name__ == '__main__':
    main()
