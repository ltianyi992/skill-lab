#!/usr/bin/env python3
"""
SessionStart Hook for Skill Lab

This hook runs when a Claude Code session starts.
It detects the project context and checks for relevant experimental skills.

Output is JSON that Claude will interpret to decide whether to suggest
linking the project to experimental skills.
"""

import json
import sys
import os
from pathlib import Path


def get_project_extensions(project_path: Path, max_files: int = 500) -> dict:
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

            # Skip ignored directories
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

        # Parse frontmatter for name and description
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

    # Check if it's a link pointing to experimental
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

    home = Path.home()
    experimental_path = home / "Desktop" / "skills-experimental"
    stable_path = home / "Desktop" / "skills-stable"

    # Check if skill-lab is set up
    if not experimental_path.exists() or not stable_path.exists():
        # Skill lab not initialized, output nothing
        print(json.dumps({
            "skill_lab_status": "not_initialized"
        }))
        return

    # Check if project is already linked
    is_linked = check_project_linked(project_path, experimental_path)

    # Get project info
    project_data = get_project_extensions(project_path)

    # Get experimental skills
    experimental_skills = get_experimental_skills(experimental_path)

    # If linked, set flag for stop hook to potentially remind about unlinking
    if is_linked:
        # Write state file for stop hook to read
        state_file = home / ".claude" / "skill-lab-session-state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps({
            "project_linked": True,
            "project_path": str(project_path),
            "session_id": hook_input.get("session_id", "unknown")
        }))

    # Check if we should prompt about experimental skills
    # Conditions: has experimental skills, project not linked, project has matching extensions
    if experimental_skills and not is_linked:
        # Build skill info for context
        skill_list = []
        for skill in experimental_skills:
            skill_info = f"- {skill['name']}"
            if skill.get('description'):
                skill_info += f": {skill['description']}"
            skill_list.append(skill_info)

        skills_text = "\n".join(skill_list)
        extensions_text = ", ".join(project_data["extensions"][:10])

        # Output using hookSpecificOutput.additionalContext format
        output = {
            "hookSpecificOutput": {
                "additionalContext": f"""[Skill Lab] Detected experimental skills available:

{skills_text}

Project file types: {extensions_text}

The project is NOT currently linked to experimental skills.
Use the skill-lab:skill-matcher agent to analyze if any experimental skills match this project's needs.
If matches are found, ask the user: "I found experimental skills that may be useful for this project. Would you like to link them using /skill-lab:link?"

Do NOT automatically link - always ask the user first."""
            }
        }
        print(json.dumps(output, indent=2))
    else:
        # Output standard data for reference
        output = {
            "skill_lab_status": "ready",
            "project": {
                "path": str(project_path),
                "is_linked_to_experimental": is_linked,
                "extensions": project_data["extensions"][:20],
                "extension_counts": dict(list(project_data["extension_counts"].items())[:20]),
                "total_files": project_data["total_files"]
            },
            "experimental_skills": experimental_skills,
            "has_experimental_skills": len(experimental_skills) > 0
        }
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
