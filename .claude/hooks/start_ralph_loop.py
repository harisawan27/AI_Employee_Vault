"""
Start Ralph Loop — Activates the persistence loop for a given task.

Usage:
    python .claude/hooks/start_ralph_loop.py \
        --prompt "Process all files in /Needs_Action, move each to /Done when complete" \
        --task-file "EMAIL_19c35066af4d79f9.md" \
        --max-iterations 10
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parents[2]
STATE_FILE = VAULT_ROOT / ".claude" / "ralph_state.json"


def main():
    parser = argparse.ArgumentParser(description="Start a Ralph Wiggum persistence loop")
    parser.add_argument(
        "--prompt", required=True,
        help="The task prompt Claude should keep working on"
    )
    parser.add_argument(
        "--task-file", required=False, default="",
        help="Filename to watch for in /Done/ (e.g. EMAIL_abc123.md)"
    )
    parser.add_argument(
        "--max-iterations", type=int, default=10,
        help="Max loop iterations before forced exit (default: 10)"
    )

    args = parser.parse_args()

    # Check for already-active loop
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
        if existing.get("active"):
            print(f"WARNING: A loop is already active for task: {existing.get('task_file', '?')}")
            print("Clear it first by running: python .claude/hooks/start_ralph_loop.py --clear")
            sys.exit(1)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    if args.prompt == "--clear":
        state = {"active": False}
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        print("Loop state cleared.")
        sys.exit(0)

    state = {
        "active": True,
        "task_file": args.task_file,
        "prompt": args.prompt,
        "max_iterations": args.max_iterations,
        "current_iteration": 0,
        "started_at": datetime.now().isoformat()
    }

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    print("Ralph Wiggum loop ACTIVATED")
    print(f"  Task file : {args.task_file or '(none — prompt-only mode)'}")
    print(f"  Max iters : {args.max_iterations}")
    print(f"  Prompt    : {args.prompt[:80]}{'...' if len(args.prompt) > 80 else ''}")
    print()
    print("Now give Claude this prompt:")
    print(f'  "{args.prompt}"')
    print()
    print("Claude will keep working until the task file is in /Done/ (or max iterations hit).")


if __name__ == "__main__":
    # Handle --clear as a special case
    if "--clear" in sys.argv:
        state = {"active": False}
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        print("Loop state cleared.")
        sys.exit(0)

    main()
