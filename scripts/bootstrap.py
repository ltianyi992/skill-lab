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

    def _is_valid_worktree(self) -> bool:
        """Check if experimental path is a valid worktree of stable."""
        if not self.experimental_path.exists():
            return False

        # Check git worktree list from stable
        success, output = self.run_command(["git", "worktree", "list"], cwd=self.stable_path)
        if not success:
            return False

        # Check if experimental path appears in worktree list
        exp_str = str(self.experimental_path).replace("\\", "/")
        for line in output.split("\n"):
            if exp_str in line.replace("\\", "/") or "skills-experimental" in line:
                return True
        return False

    def _is_independent_git_repo(self, path: Path) -> bool:
        """Check if path is an independent git repository (not a worktree)."""
        git_path = path / ".git"
        if not git_path.exists():
            return False
        # If .git is a directory, it's a full repo; if it's a file, it's a worktree
        return git_path.is_dir()

    def _backup_directory(self, path: Path) -> Path:
        """Backup a directory by renaming it."""
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = path.parent / f"{path.name}_backup_{timestamp}"

        try:
            path.rename(backup_path)
            return backup_path
        except Exception as e:
            raise Exception(f"Failed to backup {path}: {e}")

    def _try_convert_to_worktree(self) -> bool:
        """Try to convert existing experimental directory to a worktree."""
        self.log("Attempting to convert existing directory to worktree...", "INFO")

        # Check if it's an independent git repo
        if self._is_independent_git_repo(self.experimental_path):
            self.log("Detected independent Git repository", "WARN")

            # Check for uncommitted changes
            success, status_output = self.run_command(
                ["git", "status", "--porcelain"],
                cwd=self.experimental_path
            )

            has_changes = bool(status_output.strip())

            # List existing skills (directories with SKILL.md)
            existing_skills = []
            try:
                for item in self.experimental_path.iterdir():
                    if item.is_dir() and (item / "SKILL.md").exists():
                        existing_skills.append(item.name)
            except Exception:
                pass

            if existing_skills:
                self.log(f"Found existing skills: {', '.join(existing_skills)}", "INFO")

            if has_changes:
                self.log("Repository has uncommitted changes", "WARN")

            # Backup the existing directory
            self.log("Backing up existing directory...", "INFO")
            try:
                backup_path = self._backup_directory(self.experimental_path)
                self.log(f"Backed up to: {backup_path}", "OK")
            except Exception as e:
                self.log(f"Backup failed: {e}", "ERROR")
                self.log("Please manually backup and remove the directory:", "ERROR")
                self.log(f"  {self.experimental_path}", "ERROR")
                return False

            # Now create the worktree
            success, output = self.run_command(
                ["git", "worktree", "add", str(self.experimental_path), "dev"],
                cwd=self.stable_path
            )
            if not success:
                self.log(f"Failed to create worktree: {output}", "ERROR")
                # Try to restore backup
                try:
                    backup_path.rename(self.experimental_path)
                    self.log("Restored backup", "INFO")
                except Exception:
                    pass
                return False

            self.log("Worktree created successfully", "OK")

            # Copy skills from backup if any
            if existing_skills:
                self.log("Restoring skills from backup...", "INFO")
                for skill_name in existing_skills:
                    src = backup_path / skill_name
                    dst = self.experimental_path / skill_name
                    try:
                        import shutil
                        if src.exists() and not dst.exists():
                            shutil.copytree(src, dst)
                            self.log(f"  Restored: {skill_name}", "OK")
                    except Exception as e:
                        self.log(f"  Failed to restore {skill_name}: {e}", "WARN")

                # Stage and commit restored skills
                self.run_command(["git", "add", "."], cwd=self.experimental_path)
                self.run_command(
                    ["git", "commit", "-m", "Restore skills from backup during worktree conversion"],
                    cwd=self.experimental_path
                )

            self.log(f"Backup preserved at: {backup_path}", "INFO")
            self.log("You can delete the backup after verifying everything works", "INFO")
            return True

        else:
            # Directory exists but is not a git repo - just backup and recreate
            self.log("Directory exists but is not a Git repository", "WARN")

            try:
                backup_path = self._backup_directory(self.experimental_path)
                self.log(f"Backed up to: {backup_path}", "OK")
            except Exception as e:
                self.log(f"Backup failed: {e}", "ERROR")
                return False

            # Create worktree
            success, output = self.run_command(
                ["git", "worktree", "add", str(self.experimental_path), "dev"],
                cwd=self.stable_path
            )
            if not success:
                self.log(f"Failed to create worktree: {output}", "ERROR")
                return False

            self.log("Worktree created successfully", "OK")
            return True

    def step4_create_worktree(self) -> bool:
        """Create Git worktree for experimental folder."""
        self.log("Creating experimental worktree...", "STEP")

        if self.experimental_path.exists():
            self.log(f"Directory exists: {self.experimental_path}", "INFO")

            # Check if it's already a valid worktree
            if self._is_valid_worktree():
                self.log("Valid worktree detected", "OK")
                return True

            # Not a valid worktree - this is the bug case!
            self.log("Directory exists but is NOT a valid worktree!", "WARN")
            self.log("This can cause sync issues between stable and experimental.", "WARN")

            # Try to fix it
            if not self._try_convert_to_worktree():
                self.log("", "ERROR")
                self.log("SETUP FAILED: Cannot create worktree structure.", "ERROR")
                self.log("", "ERROR")
                self.log("Manual fix required:", "ERROR")
                self.log(f"  1. Backup any important files from: {self.experimental_path}", "ERROR")
                self.log(f"  2. Delete the directory: {self.experimental_path}", "ERROR")
                self.log("  3. Re-run /skill-lab:setup", "ERROR")
                self.log("", "ERROR")
                return False

            return True

        # Directory doesn't exist - create fresh worktree
        success, output = self.run_command(
            ["git", "worktree", "add", str(self.experimental_path), "dev"],
            cwd=self.stable_path
        )
        if not success:
            self.log(f"Failed: {output}", "ERROR")
            return False

        self.log(f"Worktree created: {self.experimental_path}", "OK")
        return True

    def _create_venv_for_path(self, target_path: Path, name: str) -> bool:
        """Create Python virtual environment in a specified folder."""
        venv_path = target_path / ".venv"
        if venv_path.exists():
            self.log(f"{name} venv already exists", "WARN")
            return True

        success, output = self.run_command(
            [sys.executable, "-m", "venv", str(venv_path)]
        )
        if not success:
            self.log(f"Failed to create {name} venv: {output}", "ERROR")
            return False

        # Add .venv to .gitignore
        gitignore_path = target_path / ".gitignore"
        gitignore_content = ".venv/\n__pycache__/\n*.pyc\n.DS_Store\n"
        if gitignore_path.exists():
            existing = gitignore_path.read_text(encoding="utf-8")
            if ".venv/" not in existing:
                gitignore_path.write_text(existing + "\n" + gitignore_content, encoding="utf-8")
        else:
            gitignore_path.write_text(gitignore_content, encoding="utf-8")

        self.log(f"{name} venv created: {venv_path}", "OK")
        return True

    def step5_create_venv(self) -> bool:
        """Create Python virtual environment in experimental folder."""
        self.log("Creating experimental virtual environment...", "STEP")
        return self._create_venv_for_path(self.experimental_path, "Experimental")

    def step5b_create_stable_venv(self) -> bool:
        """Create Python virtual environment in stable folder."""
        self.log("Creating stable virtual environment...", "STEP")
        return self._create_venv_for_path(self.stable_path, "Stable")

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
                # Windows requires cmd.exe for mklink command (not powershell)
                # Junction (/J) usually doesn't require admin, but symlink (/D) does
                cmd = f'mklink /J "{self.claude_skills_path}" "{self.stable_path}"'
                result = subprocess.run(
                    ["cmd.exe", "/c", cmd],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    # Try with explicit cmd invocation if shell=True failed
                    self.log("Junction creation failed, may need admin rights", "WARN")
                    self.log(f"Error: {result.stderr.strip()}", "WARN")
                    raise Exception(result.stderr)
            else:
                os.symlink(self.stable_path, self.claude_skills_path)

            self.log(f"Linked: {self.claude_skills_path} -> {self.stable_path}", "OK")
            return True

        except Exception as e:
            self.log(f"Failed: {e}", "ERROR")
            if self.os_type == "Windows":
                self.log("", "INFO")
                self.log("On Windows, please run this command manually in CMD as Administrator:", "INFO")
                self.log(f'  mklink /J "{self.claude_skills_path}" "{self.stable_path}"', "INFO")
                self.log("", "INFO")
                self.log("Steps:", "INFO")
                self.log("  1. Press Win+X, select 'Terminal (Admin)' or 'Command Prompt (Admin)'", "INFO")
                self.log("  2. Copy and paste the mklink command above", "INFO")
                self.log("  3. Re-run /skill-lab:setup to verify", "INFO")
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
        """Verify the setup is correct, especially worktree and global link."""
        self.log("Verifying setup...", "STEP")

        errors = []

        # 1. Verify worktree structure
        self.log("Checking worktree structure...", "INFO")
        if not self._is_valid_worktree():
            errors.append("Experimental folder is NOT a valid worktree of stable!")
            self.log("  Worktree: INVALID", "ERROR")
        else:
            self.log("  Worktree: OK", "OK")

        # 2. Verify both directories exist
        if not self.stable_path.exists():
            errors.append(f"Stable folder does not exist: {self.stable_path}")
        if not self.experimental_path.exists():
            errors.append(f"Experimental folder does not exist: {self.experimental_path}")

        # 3. Verify both have .venv
        stable_venv = self.stable_path / ".venv"
        exp_venv = self.experimental_path / ".venv"
        if not stable_venv.exists():
            self.log("  Stable venv: MISSING", "WARN")
        else:
            self.log("  Stable venv: OK", "OK")
        if not exp_venv.exists():
            self.log("  Experimental venv: MISSING", "WARN")
        else:
            self.log("  Experimental venv: OK", "OK")

        # 4. Verify global link exists
        if not self.claude_skills_path.exists():
            errors.append(f"Global link does not exist: {self.claude_skills_path}")
            self.log("  Global link: MISSING", "ERROR")
        else:
            # Check what the link points to
            try:
                if self.claude_skills_path.is_symlink():
                    target = self.claude_skills_path.resolve()
                elif self._is_junction(self.claude_skills_path):
                    # For Windows junctions, use dir command to check target
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
                        errors.append("Global link points to experimental instead of stable!")
                        self.log("  Global link: WRONG TARGET (experimental)", "ERROR")
                else:
                    self.log("  Global link: Is a directory (not a link)", "WARN")
                    target = None

                if target:
                    # Verify target is stable, not experimental
                    stable_resolved = self.stable_path.resolve()
                    experimental_resolved = self.experimental_path.resolve()

                    if str(target) == str(stable_resolved):
                        self.log("  Global link: -> skills-stable (OK)", "OK")
                    elif str(target) == str(experimental_resolved):
                        errors.append("Global link points to experimental instead of stable!")
                        self.log("  Global link: -> skills-experimental (WRONG!)", "ERROR")
                    else:
                        self.log(f"  Global link: -> {target} (unknown)", "WARN")

            except Exception as e:
                self.log(f"  Could not verify link target: {e}", "WARN")

        # 5. Verify git branches
        self.log("Checking Git branches...", "INFO")
        success, stable_branch = self.run_command(
            ["git", "branch", "--show-current"],
            cwd=self.stable_path
        )
        success2, exp_branch = self.run_command(
            ["git", "branch", "--show-current"],
            cwd=self.experimental_path
        )
        stable_branch = stable_branch.strip() if success else "unknown"
        exp_branch = exp_branch.strip() if success2 else "unknown"

        self.log(f"  Stable branch: {stable_branch}", "OK" if stable_branch in ["main", "master"] else "WARN")
        self.log(f"  Experimental branch: {exp_branch}", "OK" if exp_branch == "dev" else "WARN")

        if exp_branch != "dev":
            self.log("  Expected experimental to be on 'dev' branch", "WARN")

        # Report errors
        if errors:
            self.log("", "ERROR")
            self.log("VERIFICATION FAILED:", "ERROR")
            for error in errors:
                self.log(f"  - {error}", "ERROR")
            self.log("", "ERROR")
            self.log("The environment may not work correctly for syncing.", "ERROR")
            self.log("Consider re-running /skill-lab:setup or manual fixes.", "ERROR")
            return False

        return True

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
            ("Creating experimental venv", self.step5_create_venv),
            ("Creating stable venv", self.step5b_create_stable_venv),
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
