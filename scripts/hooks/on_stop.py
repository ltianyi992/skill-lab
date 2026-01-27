#!/usr/bin/env python3
"""
Stop Hook for Skill Lab

This hook runs when Claude finishes responding.
It checks if the project is linked to experimental skills and outputs
a reminder signal for Claude to display to the user.

Output is JSON that Claude will interpret to generate a user-friendly
reminder in the user's language.
"""

import json
import sys
import os
from pathlib import Path


def main():
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        hook_input = {}

    home = Path.home()
    state_file = home / ".claude" / "skill-lab-session-state.json"

    # Check if there's session state indicating experimental usage
    if not state_file.exists():
        # No state, nothing to remind
        return

    try:
        state = json.loads(state_file.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, IOError):
        return

    # Check if project is linked
    if not state.get("project_linked", False):
        return

    project_path = Path(state.get("project_path", ""))

    # Verify the link still exists
    local_skills = project_path / ".claude" / "skills"
    if not local_skills.exists():
        # Link was removed, clean up state
        try:
            state_file.unlink()
        except Exception:
            pass
        return

    # Check if this is a first-time reminder in this session
    first_time_file = home / ".claude" / "skill-lab-reminder-shown.txt"
    first_time = not first_time_file.exists()

    if first_time:
        # Mark that we've shown the detailed reminder
        try:
            first_time_file.write_text(hook_input.get("session_id", "shown"))
        except Exception:
            pass

    # Output reminder signal for Claude
    # Claude will generate the actual message in the user's language
    output = {
        "experimental_note": True,
        "first_time": first_time,
        "project_path": str(project_path)
    }

    print(json.dumps(output))


if __name__ == "__main__":
    main()
