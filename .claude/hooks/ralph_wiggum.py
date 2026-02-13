"""
Ralph Wiggum Stop Hook — Keeps Claude working until the task is done.

This script runs every time Claude tries to exit. It checks whether the
assigned task file has been moved to /Done/. If not, it blocks the exit
so Claude continues working.

Reads hook input from stdin, writes decision to stdout.
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Resolve paths relative to the vault root (project dir)
VAULT_ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parents[2]))
STATE_FILE = VAULT_ROOT / ".claude" / "ralph_state.json"
DONE_DIR = VAULT_ROOT / "Done"
LOG_FILE = VAULT_ROOT / "Logs" / "ralph_loop.log"


def log(message: str):
    """Append a timestamped line to the loop log."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


def read_state() -> dict:
    """Read the current loop state. Returns inactive state if missing/corrupt."""
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"active": False}


def write_state(state: dict):
    """Persist loop state to disk."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def clear_state():
    """Reset state to inactive."""
    write_state({"active": False})


def task_in_done(task_file: str) -> bool:
    """Check if the task file exists anywhere under /Done/."""
    if not DONE_DIR.exists():
        return False
    # Check top-level and subdirectories
    for path in DONE_DIR.rglob(task_file):
        return True
    return False


def main():
    # Read hook input from stdin
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        hook_input = {}

    # Note: stop_hook_active is True when Claude was previously blocked by this
    # hook and is trying to stop again. We do NOT exit early on this flag —
    # we rely on max_iterations as our safety cap instead. This allows the loop
    # to keep blocking across multiple iterations until the task is truly done.
    is_reentry = hook_input.get("stop_hook_active", False)

    state = read_state()

    # No active task — let Claude exit normally
    if not state.get("active"):
        sys.exit(0)

    task_file = state.get("task_file", "")
    prompt = state.get("prompt", "")
    max_iterations = state.get("max_iterations", 10)
    current_iteration = state.get("current_iteration", 0)

    # Check if the task file has reached /Done/
    if task_in_done(task_file):
        log(f"Task complete: {task_file} found in /Done/ after {current_iteration} iteration(s)")
        clear_state()
        sys.exit(0)

    # Increment iteration
    current_iteration += 1
    state["current_iteration"] = current_iteration
    write_state(state)

    # Hit the safety cap — allow exit
    if current_iteration > max_iterations:
        log(f"MAX ITERATIONS ({max_iterations}) reached for task: {task_file}. Forcing exit.")
        clear_state()
        # Output a warning but still allow exit
        sys.exit(0)

    # Block the exit — Claude needs to keep working
    remaining = max_iterations - current_iteration
    reason = (
        f"Task not done yet (iteration {current_iteration}/{max_iterations}). "
        f"File '{task_file}' has NOT been moved to /Done/. "
        f"Please continue working. Original prompt: {prompt}"
    )

    reentry_note = " (re-entry)" if is_reentry else ""
    log(f"Blocking exit — iteration {current_iteration}/{max_iterations} — {task_file}{reentry_note}")

    # Output the block decision as JSON to stdout
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


if __name__ == "__main__":
    main()
