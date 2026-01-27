#!/usr/bin/env python3
"""
Skill Lab - Environment Bootstrap Script

Sets up the Blue-Green development environment for Claude Code skills:
1. Creates stable folder (~/Desktop/skills-stable) with Git repo
2. Creates experimental folder (~/Desktop/skills-experimental) as Git Worktree
3. Links ~/.claude/skills to stable folder for global availability
4. Creates Python virtual environment in experimental folder

This script is called by the /skill-lab:setup command.

Usage:
    python bootstrap.py
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


class SkillLabBootstrap:
    """Handles the Skill Lab environment initialization."""

    def __init__(self):
        self.home = Path.home()
        self.desktop = self.home / "Desktop"
        self.stable_path = self.desktop / "skills-stable"
        self.experimental_path = self.desktop / "skills-experimental"
        self.claude_skills_path = self.home / ".claude" / "skills"
        self.os_type = platform.system()  # 'Windows', 'Darwin', 'Linux'

    def log(self, message: str, status: str = "INFO"):
        """Print formatted log message."""
        symbols = {
            "INFO": "[*]",
            "OK": "[+]",
            "WARN": "[!]",
            "ERROR": "[-]",
            "STEP": "[>]"
        }
        print(f"{symbols.get(status, '[*]')} {message}")

    def run_command(self, cmd: list, cwd: Path = None) -> tuple:
        """Execute a shell command and return (success, output)."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)

    def check_prerequisites(self) -> bool:
        """Verify required tools are available."""
        self.log("Checking prerequisites...", "STEP")

        # Check Git
        success, output = self.run_command(["git", "--version"])
        if not success:
            self.log("Git is not installed or not in PATH", "ERROR")
            return False
        self.log(f"Git: {output.strip()}", "OK")

        # Check Python (we're running, so it exists)
        self.log(f"Python: {sys.version.split()[0]}", "OK")

        # Check OS
        self.log(f"OS: {self.os_type}", "OK")

        return True

    def step1_create_stable_directory(self) -> bool:
        """Create the stable skills directory."""
        self.log("Creating stable directory...", "STEP")

        if self.stable_path.exists():
            self.log(f"Already exists: {self.stable_path}", "WARN")
            return True

        try:
            self.stable_path.mkdir(parents=True, exist_ok=True)
            self.log(f"Created: {self.stable_path}", "OK")
            return True
        except Exception as e:
            self.log(f"Failed: {e}", "ERROR")
            return False

    def step2_init_git_repo(self) -> bool:
        """Initialize Git repository in stable folder."""
        self.log("Initializing Git repository...", "STEP")

        git_dir = self.stable_path / ".git"
        if git_dir.exists():
            self.log("Git already initialized", "WARN")
            return True

        # git init
        success, output = self.run_command(["git", "init"], cwd=self.stable_path)
        if not success:
            self.log(f"Failed to init git: {output}", "ERROR")
            return False

        # Create initial README
        readme_path = self.stable_path / "README.md"
        readme_content = """# Skills Stable

This is your stable/production skills folder.

## How It Works

- Skills here are available globally via `~/.claude/skills`
- Only place tested and validated skills here
- Use `~/Desktop/skills-experimental` for development

## Managed by

[Skill Lab](https://github.com/your-username/skill-lab) plugin for Claude Code.

## Commands

- `/skill-lab:status` - Check environment status
- `/skill-lab:sync` - Sync experimental skills here
- `/skill-lab:link` - Link a project to experimental
- `/skill-lab:unlink` - Unlink a project
"""
        readme_path.write_text(readme_content, encoding="utf-8")

        # Configure git user (local to repo)
        self.run_command(["git", "config", "user.email", "skill-lab@local.dev"], cwd=self.stable_path)
        self.run_command(["git", "config", "user.name", "Skill Lab"], cwd=self.stable_path)

        # Initial commit
        self.run_command(["git", "add", "README.md"], cwd=self.stable_path)
        success, output = self.run_command(
            ["git", "commit", "-m", "Initial commit: Skill Lab stable branch"],
            cwd=self.stable_path
        )
        if not success:
            self.log(f"Failed to commit: {output}", "ERROR")
            return False

        self.log("Git repository initialized", "OK")
        return True

    def step3_create_dev_branch(self) -> bool:
        """Create the dev branch."""
        self.log("Creating dev branch...", "STEP")

        # Check if branch exists
        success, output = self.run_command(
            ["git", "branch", "--list", "dev"],
            cwd=self.stable_path
        )
        if "dev" in output:
            self.log("Dev branch already exists", "WARN")
            return True

        success, output = self.run_command(
            ["git", "branch", "dev"],
            cwd=self.stable_path
        )
        if not success:
            self.log(f"Failed: {output}", "ERROR")
            return False

        self.log("Dev branch created", "OK")
        return True

    def step4_create_worktree(self) -> bool:
        """Create Git worktree for experimental folder."""
        self.log("Creating experimental worktree...", "STEP")

        if self.experimental_path.exists():
            self.log(f"Already exists: {self.experimental_path}", "WARN")
            # Check if it's a valid worktree
            success, output = self.run_command(["git", "worktree", "list"], cwd=self.stable_path)
            if str(self.experimental_path) in output or "skills-experimental" in output:
                self.log("Valid worktree detected", "OK")
                return True
            self.log("Directory exists but not a worktree - may need manual cleanup", "WARN")
            return True

        success, output = self.run_command(
            ["git", "worktree", "add", str(self.experimental_path), "dev"],
            cwd=self.stable_path
        )
        if not success:
            self.log(f"Failed: {output}", "ERROR")
            return False

        self.log(f"Worktree created: {self.experimental_path}", "OK")
        return True

    def step5_create_venv(self) -> bool:
        """Create Python virtual environment in experimental folder."""
        self.log("Creating Python virtual environment...", "STEP")

        venv_path = self.experimental_path / ".venv"
        if venv_path.exists():
            self.log("Virtual environment already exists", "WARN")
            return True

        success, output = self.run_command(
            [sys.executable, "-m", "venv", str(venv_path)]
        )
        if not success:
            self.log(f"Failed: {output}", "ERROR")
            return False

        # Add .venv to .gitignore
        gitignore_path = self.experimental_path / ".gitignore"
        gitignore_content = ".venv/\n__pycache__/\n*.pyc\n.DS_Store\n"
        gitignore_path.write_text(gitignore_content, encoding="utf-8")

        self.log(f"Virtual environment created: {venv_path}", "OK")
        return True

    def step6_create_global_link(self) -> bool:
        """Create junction/symlink from ~/.claude/skills to stable."""
        self.log("Creating global skills link...", "STEP")

        # Ensure .claude directory exists
        claude_dir = self.home / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)

        # Check if skills path already exists
        if self.claude_skills_path.exists():
            # Check if it's already a link
            if self.claude_skills_path.is_symlink() or self._is_junction(self.claude_skills_path):
                self.log(f"Link already exists: {self.claude_skills_path}", "WARN")
                return True

            # It's a real directory - ABORT
            self.log(f"ABORT: {self.claude_skills_path} exists as a directory!", "ERROR")
            self.log("Cannot overwrite existing skills directory.", "ERROR")
            self.log("Please backup and remove it manually to proceed.", "ERROR")
            return False

        # Create the link
        try:
            if self.os_type == "Windows":
                cmd = f'mklink /J "{self.claude_skills_path}" "{self.stable_path}"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(result.stderr)
            else:
                os.symlink(self.stable_path, self.claude_skills_path)

            self.log(f"Linked: {self.claude_skills_path} -> {self.stable_path}", "OK")
            return True

        except Exception as e:
            self.log(f"Failed: {e}", "ERROR")
            if self.os_type == "Windows":
                self.log("On Windows, try running as Administrator", "INFO")
            return False

    def _is_junction(self, path: Path) -> bool:
        """Check if a path is a Windows junction point."""
        if self.os_type != "Windows":
            return False
        try:
            import ctypes
            FILE_ATTRIBUTE_REPARSE_POINT = 0x400
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            return attrs != -1 and (attrs & FILE_ATTRIBUTE_REPARSE_POINT)
        except Exception:
            return False

    def _verify_setup(self) -> bool:
        """Verify the setup is correct, especially the global link target."""
        self.log("Verifying setup...", "STEP")

        # Verify global link exists
        if not self.claude_skills_path.exists():
            self.log(f"Global link does not exist: {self.claude_skills_path}", "ERROR")
            return False

        # Check what the link points to
        try:
            if self.claude_skills_path.is_symlink():
                target = self.claude_skills_path.resolve()
            elif self._is_junction(self.claude_skills_path):
                # For Windows junctions, use dir command to check target
                import subprocess
                result = subprocess.run(
                    f'dir "{self.claude_skills_path.parent}" /AL',
                    shell=True, capture_output=True, text=True
                )
                # Parse output to find junction target
                target = self.stable_path  # Default assumption
                if "skills-stable" in result.stdout:
                    target = self.stable_path
                elif "skills-experimental" in result.stdout:
                    target = self.experimental_path
                    self.log(f"ERROR: Global link points to experimental!", "ERROR")
                    self.log(f"  Expected: {self.stable_path}", "ERROR")
                    self.log(f"  Actual:   skills-experimental", "ERROR")
                    return False
            else:
                self.log(f"Global skills path is a directory, not a link", "WARN")
                return True

            # Verify target is stable, not experimental
            stable_resolved = self.stable_path.resolve()
            experimental_resolved = self.experimental_path.resolve()

            if str(target) == str(stable_resolved):
                self.log(f"Verified: Global link -> skills-stable", "OK")
                return True
            elif str(target) == str(experimental_resolved):
                self.log(f"ERROR: Global link points to experimental!", "ERROR")
                self.log(f"  Expected: {self.stable_path}", "ERROR")
                self.log(f"  Actual:   {target}", "ERROR")
                return False
            else:
                self.log(f"Warning: Global link points to unknown target: {target}", "WARN")
                return True

        except Exception as e:
            self.log(f"Could not verify link target: {e}", "WARN")
            return True  # Don't fail on verification errors

    def run(self) -> bool:
        """Execute the complete bootstrap process."""
        print()
        print("=" * 50)
        print("  Skill Lab - Environment Setup")
        print("=" * 50)
        print()

        if not self.check_prerequisites():
            return False

        print()

        steps = [
            ("Creating stable folder", self.step1_create_stable_directory),
            ("Initializing Git", self.step2_init_git_repo),
            ("Creating dev branch", self.step3_create_dev_branch),
            ("Creating experimental worktree", self.step4_create_worktree),
            ("Creating virtual environment", self.step5_create_venv),
            ("Creating global skills link", self.step6_create_global_link),
        ]

        for name, step_func in steps:
            if not step_func():
                self.log("Setup failed!", "ERROR")
                return False
            print()

        # Verify the setup is correct
        if not self._verify_setup():
            self.log("Setup verification failed!", "ERROR")
            return False
        print()

        print("=" * 50)
        self.log("Setup completed successfully!", "OK")
        print("=" * 50)
        print()
        print("Environment Summary:")
        print(f"  Stable:       {self.stable_path}")
        print(f"  Experimental: {self.experimental_path}")
        print(f"  Global Link:  {self.claude_skills_path} -> {self.stable_path}")
        print()
        print("Next Steps:")
        print("  1. Create skills in ~/Desktop/skills-experimental")
        print("  2. Link projects: /skill-lab:link")
        print("  3. When ready, sync: /skill-lab:sync")
        print()

        return True


def main():
    bootstrap = SkillLabBootstrap()
    success = bootstrap.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
