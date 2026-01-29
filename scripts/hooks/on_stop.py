#!/usr/bin/env python3
"""
PostToolUse Hook for Skill Lab

This hook runs AFTER Edit|Write|Bash tool execution.
It checks if the project is linked to experimental skills and uses
HARD decision control to remind user about unlinking.

Uses decision: "block" to force Claude to display the reminder.
"""

import json
import sys
import os
from pathlib import Path
import time


def get_state_file() -> Path:
    """Get the session state file path."""
    return Path.home() / ".claude" / "skill-lab-pretool-state.json"


def get_reminder_file() -> Path:
    """Get the reminder tracking file path."""
    return Path.home() / ".claude" / "skill-lab-reminder-state.json"


def load_state() -> dict:
    """Load the session state."""
    state_file = get_state_file()
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def load_reminder_state() -> dict:
    """Load the reminder state."""
    reminder_file = get_reminder_file()
    if reminder_file.exists():
        try:
            return json.loads(reminder_file.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_reminder_state(state: dict):
    """Save the reminder state."""
    reminder_file = get_reminder_file()
    reminder_file.parent.mkdir(parents=True, exist_ok=True)
    reminder_file.write_text(json.dumps(state, indent=2), encoding='utf-8')


def check_project_linked(project_path: Path, experimental_path: Path) -> bool:
    """Check if the project is linked to experimental."""

    local_skills = project_path / ".claude" / "skills"

    if not local_skills.exists():
        return False

    try:
        if local_skills.is_symlink():
            target = local_skills.resolve()
            return str(target) == str(experimental_path.resolve())

        # Windows junction check
        import platform
        if platform.system() == "Windows":
            import ctypes
            FILE_ATTRIBUTE_REPARSE_POINT = 0x400
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(local_skills))
            if attrs != -1 and (attrs & FILE_ATTRIBUTE_REPARSE_POINT):
                return True
    except Exception:
        pass

    return False


def main():
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        hook_input = {}

    cwd = hook_input.get("cwd", os.getcwd())
    project_path = Path(cwd)
    session_id = hook_input.get("session_id", "unknown")
    tool_name = hook_input.get("tool_name", "")

    home = Path.home()
    experimental_path = home / "Desktop" / "skills-experimental"

    # Check if project is linked to experimental
    is_linked = check_project_linked(project_path, experimental_path)

    if not is_linked:
        # Not linked, no need to remind
        sys.exit(0)

    # Load reminder state to control frequency
    reminder_state = load_reminder_state()
    project_key = str(project_path)

    # Check reminder frequency - only remind once per session per project
    # Or if significant time has passed (e.g., 10 minutes)
    current_time = time.time()
    last_reminder = reminder_state.get(project_key, {})
    last_time = last_reminder.get("timestamp", 0)
    last_session = last_reminder.get("session_id", "")

    # Skip if already reminded in this session
    if last_session == session_id:
        sys.exit(0)

    # Skip if reminded within last 10 minutes (600 seconds)
    if current_time - last_time < 600:
        sys.exit(0)

    # Update reminder state
    reminder_state[project_key] = {
        "timestamp": current_time,
        "session_id": session_id
    }
    save_reminder_state(reminder_state)

    # HARD BLOCK - Force Claude to display this reminder
    output = {
        "decision": "block",
        "reason": f"""[Skill Lab - Reminder]

This project is currently linked to the EXPERIMENTAL skills environment.

Project: {project_path}
Link: .claude/skills -> skills-experimental

If you have finished experimenting, you may want to:
1. Keep the link if you're still testing
2. Run /skill-lab:unlink to disconnect from experimental
3. Run /skill-lab:sync if you want to promote changes to stable

Ask the user: "You're using experimental skills. Would you like to keep the link, unlink, or sync changes to stable?"

This reminder appears once per session."""
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
