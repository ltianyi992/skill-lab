#!/usr/bin/env python3
"""
PreToolUse Hook for Skill Lab

This hook runs BEFORE Read|Glob tool execution.
It detects if the project has matching experimental skills and uses
HARD permission control to ensure Claude asks about linking first.

Uses permissionDecision: "deny" to block tool execution until skill linking is addressed.
"""

import json
import sys
import os
from pathlib import Path


def get_state_file() -> Path:
    """Get the session state file path."""
    return Path.home() / ".claude" / "skill-lab-pretool-state.json"


def load_state() -> dict:
    """Load the session state."""
    state_file = get_state_file()
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_state(state: dict):
    """Save the session state."""
    state_file = get_state_file()
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2), encoding='utf-8')


def get_project_extensions(project_path: Path, max_files: int = 200) -> dict:
    """Scan project for file extensions without reading contents."""

    ignored_dirs = {
        '.git', '.svn', '.hg', 'node_modules', '__pycache__',
        '.venv', 'venv', '.idea', '.vscode', '.claude',
        'dist', 'build', 'target', 'out', '.next', '.nuxt', '.cache'
    }

    ignored_extensions = {
        '.exe', '.dll', '.so', '.dylib',
        '.jpg', '.jpeg', '.png', '.gif', '.ico', '.svg',
        '.mp3', '.mp4', '.wav', '.avi',
        '.zip', '.tar', '.gz', '.rar',
        '.lock', '.log'
    }

    extension_counts = {}
    total_files = 0

    try:
        for file in project_path.rglob("*"):
            if total_files >= max_files:
                break

            if not file.is_file():
                continue

            skip = False
            for part in file.parts:
                if part in ignored_dirs or part.startswith('.'):
                    skip = True
                    break
            if skip:
                continue

            ext = file.suffix.lower()
            if ext and ext not in ignored_extensions:
                extension_counts[ext] = extension_counts.get(ext, 0) + 1
                total_files += 1

    except PermissionError:
        pass

    return {
        "extensions": sorted(extension_counts.keys(),
                           key=lambda x: extension_counts[x],
                           reverse=True),
        "extension_counts": extension_counts,
        "total_files": total_files
    }


def get_experimental_skills(experimental_path: Path) -> list:
    """List skills in the experimental folder."""

    skills = []

    if not experimental_path.exists():
        return skills

    for item in experimental_path.iterdir():
        if not item.is_dir():
            continue
        if item.name.startswith('.') or item.name in {'__pycache__', 'node_modules', '.venv'}:
            continue

        skill_md = item / "SKILL.md"
        if not skill_md.exists():
            continue

        try:
            content = skill_md.read_text(encoding='utf-8')
            import re

            frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
            if frontmatter_match:
                frontmatter = frontmatter_match.group(1)
                name_match = re.search(r'^name:\s*["\']?([^"\'\n]+)', frontmatter, re.MULTILINE)
                desc_match = re.search(r'^description:\s*["\']?([^"\'\n]+)', frontmatter, re.MULTILINE)

                skills.append({
                    "name": name_match.group(1).strip() if name_match else item.name,
                    "description": desc_match.group(1).strip() if desc_match else "",
                    "path": str(item)
                })
        except Exception:
            skills.append({
                "name": item.name,
                "description": "",
                "path": str(item)
            })

    return skills


def check_project_linked(project_path: Path, experimental_path: Path) -> bool:
    """Check if the project is already linked to experimental."""

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


def simple_skill_match(extensions: list, skills: list) -> list:
    """Simple matching between file extensions and skill names/descriptions."""

    matches = []

    # Extension to keyword mapping
    ext_keywords = {
        '.pdf': ['pdf'],
        '.doc': ['doc', 'word', 'document'],
        '.docx': ['doc', 'word', 'document'],
        '.xls': ['excel', 'spreadsheet'],
        '.xlsx': ['excel', 'spreadsheet'],
        '.ppt': ['powerpoint', 'presentation'],
        '.pptx': ['powerpoint', 'presentation'],
        '.py': ['python', 'script'],
        '.js': ['javascript', 'node', 'frontend'],
        '.ts': ['typescript', 'node', 'frontend'],
        '.jsx': ['react', 'frontend'],
        '.tsx': ['react', 'typescript', 'frontend'],
        '.vue': ['vue', 'frontend'],
        '.sql': ['sql', 'database', 'query'],
        '.json': ['json', 'config'],
        '.yaml': ['yaml', 'config', 'ci'],
        '.yml': ['yaml', 'config', 'ci'],
        '.md': ['markdown', 'doc'],
        '.csv': ['csv', 'data'],
    }

    for skill in skills:
        skill_name = skill['name'].lower()
        skill_desc = skill.get('description', '').lower()
        skill_text = f"{skill_name} {skill_desc}"

        matched_exts = []
        for ext in extensions:
            keywords = ext_keywords.get(ext, [ext.replace('.', '')])
            for keyword in keywords:
                if keyword in skill_text:
                    matched_exts.append(ext)
                    break

        if matched_exts:
            matches.append({
                "skill": skill['name'],
                "matched_extensions": list(set(matched_exts)),
                "description": skill.get('description', '')
            })

    return matches


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
    stable_path = home / "Desktop" / "skills-stable"

    # Check if skill-lab is set up
    if not experimental_path.exists() or not stable_path.exists():
        # Skill lab not initialized, allow tool to proceed
        sys.exit(0)

    # Load state to check if we've already prompted for this project in this session
    state = load_state()
    project_key = str(project_path)

    # Check if already prompted for this project
    prompted_projects = state.get("prompted_projects", {})
    if project_key in prompted_projects:
        # Already prompted, allow tool to proceed
        sys.exit(0)

    # Check if project is already linked
    is_linked = check_project_linked(project_path, experimental_path)

    if is_linked:
        # Already linked, save state for PostToolUse to remind about unlinking
        state["linked_project"] = project_key
        state["session_id"] = session_id
        save_state(state)
        sys.exit(0)

    # Get experimental skills
    experimental_skills = get_experimental_skills(experimental_path)

    if not experimental_skills:
        # No experimental skills available, allow tool to proceed
        sys.exit(0)

    # Get project extensions
    project_data = get_project_extensions(project_path)

    if not project_data["extensions"]:
        # No relevant files found, allow tool to proceed
        sys.exit(0)

    # Check for matches
    matches = simple_skill_match(project_data["extensions"], experimental_skills)

    if not matches:
        # No matches, allow tool to proceed
        prompted_projects[project_key] = {"matched": False, "session_id": session_id}
        state["prompted_projects"] = prompted_projects
        save_state(state)
        sys.exit(0)

    # Found matches! Mark as prompted and DENY the tool to force Claude to ask user
    prompted_projects[project_key] = {"matched": True, "session_id": session_id}
    state["prompted_projects"] = prompted_projects
    save_state(state)

    # Build match description
    match_lines = []
    for m in matches[:3]:  # Top 3 matches
        exts = ", ".join(m["matched_extensions"][:3])
        match_lines.append(f"- {m['skill']}: matches {exts}")
    matches_text = "\n".join(match_lines)

    # HARD DENY - This blocks the tool execution and forces Claude to address this first
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"""[Skill Lab - Action Required]

Detected matching experimental skills for this project:

{matches_text}

REQUIRED ACTION:
Ask the user: "I found experimental skills that match your project. Would you like to link them using /skill-lab:link?"

- If user agrees: Run /skill-lab:link first
- If user declines: Note their preference and proceed normally

This prompt will only appear once per project per session."""
        }
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
