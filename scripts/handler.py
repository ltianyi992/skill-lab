#!/usr/bin/env python3
"""
Skill Lab - CLI Handler

Provides the core functionality for the Skill Lab plugin:
- Checking environment status
- Syncing changes from experimental to stable
- Linking/unlinking projects to experimental environment
- Listing experimental skills

Usage:
    python handler.py <command> [arguments]

Commands:
    status  - Check experimental branch status
    sync    - Commit and merge to stable
    link    - Link a project to experimental
    unlink  - Unlink a project from experimental
    skills  - List experimental skills
    info    - Show full environment info
    env     - Show environment variables
    scan    - Scan project file extensions
    detect  - Gather data for skill matching
"""

import os
import sys
import subprocess
import platform
import re
from pathlib import Path
from typing import Optional, Tuple, Dict, List


class SkillLabHandler:
    """Manages the Skill Lab Blue-Green development environment."""

    def __init__(self):
        self.home = Path.home()
        self.desktop = self.home / "Desktop"
        self.stable_path = self.desktop / "skills-stable"
        self.experimental_path = self.desktop / "skills-experimental"
        self.os_type = platform.system()

    def _run_git(self, args: list, cwd: Path) -> Tuple[bool, str]:
        """Execute a git command and return (success, output)."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60
            )
            output = result.stdout + result.stderr
            return result.returncode == 0, output.strip()
        except subprocess.TimeoutExpired:
            return False, "Git command timed out"
        except Exception as e:
            return False, str(e)

    def _is_junction(self, path: Path) -> bool:
        """Check if path is a Windows junction."""
        if self.os_type != "Windows":
            return False
        try:
            import ctypes
            FILE_ATTRIBUTE_REPARSE_POINT = 0x400
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            return attrs != -1 and (attrs & FILE_ATTRIBUTE_REPARSE_POINT)
        except Exception:
            return False

    def check_status(self) -> Dict[str, any]:
        """Check the git status of the experimental branch."""
        result = {
            "success": False,
            "branch": None,
            "clean": False,
            "changes": [],
            "untracked": [],
            "error": None
        }

        if not self.experimental_path.exists():
            result["error"] = f"Experimental path not found: {self.experimental_path}"
            return result

        # Get current branch
        success, branch = self._run_git(["branch", "--show-current"], self.experimental_path)
        if success:
            result["branch"] = branch

        # Get status
        success, status_output = self._run_git(
            ["status", "--porcelain"],
            self.experimental_path
        )

        if not success:
            result["error"] = f"Failed to get status: {status_output}"
            return result

        result["success"] = True

        if not status_output:
            result["clean"] = True
        else:
            for line in status_output.split("\n"):
                if line.startswith("??"):
                    result["untracked"].append(line[3:])
                elif line.strip():
                    result["changes"].append(line)

        return result

    def auto_commit_and_merge(self, commit_message: Optional[str] = None) -> Dict[str, any]:
        """Commit changes in experimental and merge to stable."""
        result = {
            "success": False,
            "committed": False,
            "merged": False,
            "commit_hash": None,
            "message": None,
            "error": None
        }

        # Check for changes
        status = self.check_status()
        if not status["success"]:
            result["error"] = status["error"]
            return result

        if status["clean"]:
            result["message"] = "No changes to commit in experimental"
            result["success"] = True
            return result

        # Stage all changes
        success, output = self._run_git(["add", "."], self.experimental_path)
        if not success:
            result["error"] = f"Failed to stage changes: {output}"
            return result

        # Commit
        if not commit_message:
            num_changes = len(status["changes"]) + len(status["untracked"])
            commit_message = f"Sync {num_changes} change(s) from experimental"

        success, output = self._run_git(
            ["commit", "-m", commit_message],
            self.experimental_path
        )
        if not success:
            result["error"] = f"Failed to commit: {output}"
            return result

        result["committed"] = True

        # Get commit hash
        success, commit_hash = self._run_git(
            ["rev-parse", "--short", "HEAD"],
            self.experimental_path
        )
        if success:
            result["commit_hash"] = commit_hash

        # Merge into stable
        success, output = self._run_git(
            ["merge", "dev", "-m", f"Merge dev: {commit_message}"],
            self.stable_path
        )

        if not success:
            result["error"] = f"Merge failed: {output}"
            result["message"] = "Changes committed but merge failed. Manual resolution may be needed."
            return result

        result["merged"] = True
        result["success"] = True
        result["message"] = f"Successfully synced and merged commit {result['commit_hash']}"

        return result

    def link_project(self, target_path: str) -> Dict[str, any]:
        """Create a local .claude/skills junction in a project folder."""
        result = {
            "success": False,
            "link_path": None,
            "target": None,
            "error": None,
            "message": None
        }

        project_path = Path(target_path).resolve()

        if not project_path.exists():
            result["error"] = f"Project path does not exist: {project_path}"
            return result

        if not project_path.is_dir():
            result["error"] = f"Project path is not a directory: {project_path}"
            return result

        # Create .claude directory in project
        project_claude_dir = project_path / ".claude"
        project_claude_dir.mkdir(parents=True, exist_ok=True)

        link_path = project_claude_dir / "skills"

        # Check if link already exists
        if link_path.exists():
            if link_path.is_symlink() or self._is_junction(link_path):
                result["success"] = True
                result["link_path"] = str(link_path)
                result["target"] = str(self.experimental_path)
                result["message"] = "Link already exists"
                return result
            else:
                result["error"] = f"Path exists and is not a link: {link_path}"
                return result

        # Create the link
        try:
            if self.os_type == "Windows":
                cmd = f'mklink /J "{link_path}" "{self.experimental_path}"'
                proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if proc.returncode != 0:
                    raise Exception(proc.stderr)
            else:
                os.symlink(self.experimental_path, link_path)

            result["success"] = True
            result["link_path"] = str(link_path)
            result["target"] = str(self.experimental_path)
            result["message"] = f"Linked {project_path} to experimental environment"

        except Exception as e:
            result["error"] = f"Failed to create link: {e}"

        return result

    def unlink_project(self, target_path: str) -> Dict[str, any]:
        """Remove the .claude/skills junction from a project folder."""
        result = {
            "success": False,
            "removed_path": None,
            "error": None,
            "message": None
        }

        project_path = Path(target_path).resolve()

        if not project_path.exists():
            result["error"] = f"Project path does not exist: {project_path}"
            return result

        link_path = project_path / ".claude" / "skills"

        if not link_path.exists():
            result["message"] = "Project is not linked to experimental skills"
            result["success"] = True
            return result

        # Check if it's a link
        is_link = link_path.is_symlink() or self._is_junction(link_path)

        if not is_link:
            result["error"] = f"Path exists but is not a link: {link_path}"
            result["message"] = "Cannot remove - this is a real directory, not a link"
            return result

        # Check if it points to our experimental path
        try:
            if link_path.is_symlink():
                target = link_path.resolve()
                if str(target) != str(self.experimental_path.resolve()):
                    result["warning"] = f"Link points to different location: {target}"
        except Exception:
            pass

        # Remove the link
        try:
            if self.os_type == "Windows":
                # On Windows, use rmdir for junctions
                cmd = f'rmdir "{link_path}"'
                proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if proc.returncode != 0:
                    raise Exception(proc.stderr)
            else:
                link_path.unlink()

            result["success"] = True
            result["removed_path"] = str(link_path)
            result["message"] = f"Unlinked {project_path} from experimental environment"

            # Clean up session state file if it exists
            state_file = self.home / ".claude" / "skill-lab-session-state.json"
            if state_file.exists():
                try:
                    state_file.unlink()
                except Exception:
                    pass

            # Clean up reminder shown file
            reminder_file = self.home / ".claude" / "skill-lab-reminder-shown.txt"
            if reminder_file.exists():
                try:
                    reminder_file.unlink()
                except Exception:
                    pass

        except Exception as e:
            result["error"] = f"Failed to remove link: {e}"

        return result

    def inject_env_vars(self) -> Dict[str, str]:
        """Get environment variables for the experimental Python environment."""
        venv_path = self.experimental_path / ".venv"

        if self.os_type == "Windows":
            python_path = venv_path / "Scripts" / "python.exe"
            pip_path = venv_path / "Scripts" / "pip.exe"
        else:
            python_path = venv_path / "bin" / "python"
            pip_path = venv_path / "bin" / "pip"

        return {
            "EXPERIMENTAL_PYTHON": str(python_path),
            "EXPERIMENTAL_PIP": str(pip_path),
            "EXPERIMENTAL_VENV": str(venv_path),
            "EXPERIMENTAL_PATH": str(self.experimental_path),
            "STABLE_PATH": str(self.stable_path),
        }

    def _parse_skill_frontmatter(self, skill_md_path: Path) -> Optional[Dict[str, str]]:
        """Parse the YAML frontmatter from a SKILL.md file."""
        try:
            content = skill_md_path.read_text(encoding="utf-8")

            frontmatter_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
            if not frontmatter_match:
                return None

            frontmatter = frontmatter_match.group(1)

            name_match = re.search(r'^name:\s*["\']?([^"\'\n]+)["\']?\s*$', frontmatter, re.MULTILINE)
            desc_match = re.search(r'^description:\s*["\']?([^"\'\n]+)', frontmatter, re.MULTILINE)

            if not name_match:
                return None

            return {
                "name": name_match.group(1).strip(),
                "description": desc_match.group(1).strip() if desc_match else ""
            }

        except Exception:
            return None

    def list_experimental_skills(self) -> List[Dict[str, str]]:
        """List all skills in the experimental environment with their metadata."""
        skills = []

        if not self.experimental_path.exists():
            return skills

        for item in self.experimental_path.iterdir():
            if not item.is_dir():
                continue

            if item.name.startswith('.') or item.name in {'__pycache__', 'node_modules'}:
                continue

            skill_md = item / "SKILL.md"
            if not skill_md.exists():
                continue

            metadata = self._parse_skill_frontmatter(skill_md)
            if metadata:
                metadata["path"] = str(item)
                skills.append(metadata)

        return skills

    def scan_project_extensions(self, project_path: Optional[str] = None) -> Dict[str, any]:
        """Scan a project directory and return file extension statistics."""
        path = Path(project_path) if project_path else Path.cwd()

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

        if not path.exists() or not path.is_dir():
            return {
                "error": f"Invalid project path: {path}",
                "extensions": [],
                "extension_counts": {},
                "total_files": 0,
                "project_path": str(path)
            }

        extension_counts: Dict[str, int] = {}
        total_files = 0
        max_files = 1000

        try:
            for file in path.rglob("*"):
                if total_files >= max_files:
                    break

                if not file.is_file():
                    continue

                # Check if in ignored directory
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

        sorted_extensions = sorted(
            extension_counts.keys(),
            key=lambda x: extension_counts[x],
            reverse=True
        )

        return {
            "extensions": sorted_extensions,
            "extension_counts": extension_counts,
            "total_files": total_files,
            "project_path": str(path),
            "truncated": total_files >= max_files
        }

    def detect_matches(self, project_path: Optional[str] = None) -> Dict[str, any]:
        """Gather data for skill matching."""
        project_data = self.scan_project_extensions(project_path)
        skills_data = self.list_experimental_skills()

        return {
            "project": {
                "path": project_data["project_path"],
                "extensions": project_data["extensions"],
                "extension_counts": project_data["extension_counts"],
                "total_files": project_data["total_files"]
            },
            "experimental_skills": skills_data,
            "has_skills": len(skills_data) > 0,
            "has_extensions": len(project_data["extensions"]) > 0
        }

    def get_info(self) -> Dict[str, any]:
        """Get comprehensive information about the environment."""
        global_link = self.home / ".claude" / "skills"
        global_link_exists = global_link.exists()
        global_link_is_link = global_link.is_symlink() or self._is_junction(global_link)

        return {
            "paths": {
                "stable": str(self.stable_path),
                "experimental": str(self.experimental_path),
                "global_skills": str(global_link),
            },
            "exists": {
                "stable": self.stable_path.exists(),
                "experimental": self.experimental_path.exists(),
                "global_link": global_link_exists and global_link_is_link,
            },
            "env_vars": self.inject_env_vars(),
            "status": self.check_status(),
            "skills": self.list_experimental_skills(),
            "os": self.os_type,
        }


def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Skill Lab CLI Handler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  status    Check experimental branch status
  sync      Commit and merge to stable
  link      Link a project to experimental
  unlink    Unlink a project from experimental
  skills    List experimental skills
  info      Show full environment info
  env       Show environment variables
  scan      Scan project file extensions
  detect    Gather data for skill matching
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # status
    subparsers.add_parser("status", help="Check experimental branch status")

    # sync
    sync_parser = subparsers.add_parser("sync", help="Commit and merge to stable")
    sync_parser.add_argument("-m", "--message", help="Commit message")

    # link
    link_parser = subparsers.add_parser("link", help="Link a project to experimental")
    link_parser.add_argument("path", nargs="?", default=".", help="Project path (default: current directory)")

    # unlink
    unlink_parser = subparsers.add_parser("unlink", help="Unlink a project from experimental")
    unlink_parser.add_argument("path", nargs="?", default=".", help="Project path (default: current directory)")

    # skills
    subparsers.add_parser("skills", help="List experimental skills")

    # info
    subparsers.add_parser("info", help="Show full environment info")

    # env
    subparsers.add_parser("env", help="Show environment variables")

    # scan
    scan_parser = subparsers.add_parser("scan", help="Scan project file extensions")
    scan_parser.add_argument("path", nargs="?", default=None, help="Project path (default: cwd)")

    # detect
    detect_parser = subparsers.add_parser("detect", help="Gather data for skill matching")
    detect_parser.add_argument("path", nargs="?", default=None, help="Project path (default: cwd)")

    args = parser.parse_args()
    handler = SkillLabHandler()

    if args.command == "status":
        result = handler.check_status()
    elif args.command == "sync":
        result = handler.auto_commit_and_merge(args.message)
    elif args.command == "link":
        result = handler.link_project(args.path)
    elif args.command == "unlink":
        result = handler.unlink_project(args.path)
    elif args.command == "skills":
        result = handler.list_experimental_skills()
    elif args.command == "info":
        result = handler.get_info()
    elif args.command == "env":
        result = handler.inject_env_vars()
    elif args.command == "scan":
        result = handler.scan_project_extensions(args.path)
    elif args.command == "detect":
        result = handler.detect_matches(args.path)
    else:
        parser.print_help()
        return

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
