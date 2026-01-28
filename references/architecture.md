# Blue-Green Development Architecture

## Overview

This architecture implements **physical isolation** between stable and experimental code using Git Worktrees, enabling safe experimentation without risking production stability.

## Directory Mapping

```
~/.claude/skills (Global Scope)
        |
        v (Junction/Symlink)
~/Desktop/skills-stable (main branch)
        |
        +-- .venv/                 <- Production Python environment
        +-- requirements.txt       <- Synced dependencies
        +-- pdf/                   <- Example stable skill
        |       +-- SKILL.md
        |
        +-- [other stable skills...]

~/Desktop/skills-experimental (dev branch - Git Worktree)
        |
        +-- .venv/                 <- Development Python environment
        +-- requirements.txt       <- Development dependencies
        +-- [experimental skills...]
```

## Git Worktree Isolation

### What is a Git Worktree?

Git Worktrees allow multiple working directories attached to a single repository. Each worktree can have a different branch checked out, enabling:

- **Parallel development**: Work on `main` and `dev` simultaneously
- **Physical separation**: Each branch has its own directory
- **Shared history**: Both directories share the same Git history

### Worktree Structure

```
skills-stable/           <- Primary repository (main branch)
    .git/                <- Full Git directory

skills-experimental/     <- Linked worktree (dev branch)
    .git                 <- File pointing to main .git
```

### Key Commands

```bash
# Create worktree (done by bootstrap)
git worktree add ../skills-experimental dev

# List worktrees
git worktree list

# Remove worktree
git worktree remove ../skills-experimental
```

## Junction/Symlink Design

### Why Link to Global Scope?

The `~/.claude/skills` directory is Claude's global skill scope. By linking it to `skills-stable`:

1. Skills in stable are immediately available to Claude globally
2. Experimental skills remain isolated until merged
3. Single source of truth for production skills

### Platform-Specific Links

| Platform | Link Type | Command |
|----------|-----------|---------|
| Windows  | Junction  | `mklink /J target source` |
| macOS    | Symlink   | `ln -s source target` |
| Linux    | Symlink   | `ln -s source target` |

### Windows Special Handling

On Windows, `mklink` requires:
1. **cmd.exe** - PowerShell doesn't support `mklink` directly
2. **May need Admin** - Junction creation sometimes requires elevated privileges

If automatic creation fails, run manually in **Administrator CMD**:
```cmd
mklink /J "C:\Users\<username>\.claude\skills" "C:\Users\<username>\Desktop\skills-stable"
```

### Safety Considerations

- **Never overwrite existing directories**: The bootstrap checks if `~/.claude/skills` exists as a directory
- **Junctions are transparent**: Applications see them as regular directories
- **Breaking the link**: Deleting the junction/symlink does not delete the target

## Blue-Green Workflow

### Development Flow

```
1. Develop in skills-experimental (dev branch)
   |
2. Install dependencies in experimental venv:
   - pip install <package>
   - pip freeze > requirements.txt
   |
3. Test and validate changes
   |
4. Use /skill-lab:sync to sync:
   - git add & commit in experimental
   - git merge dev into main (in stable)
   - Auto-install requirements.txt to stable venv
   |
5. Changes + dependencies now live in stable (global scope)
```

### Dependency Sync Flow

```
experimental/.venv          stable/.venv
      |                           |
      | pip install pypdf         |
      v                           |
requirements.txt ----sync----> requirements.txt
                                  |
                                  v
                           pip install -r requirements.txt
```

### Rollback Strategy

If a merged change causes issues:

```bash
cd ~/Desktop/skills-stable
git revert HEAD
# Or reset to previous commit
git reset --hard HEAD~1
```

## Virtual Environment Isolation

Both folders have their own `.venv`:

```bash
~/Desktop/skills-experimental/.venv/    <- Development environment
    bin/python    (or Scripts/python.exe on Windows)
    lib/
    ...

~/Desktop/skills-stable/.venv/          <- Production environment
    bin/python    (or Scripts/python.exe on Windows)
    lib/
    ...
```

### Environment Variables

| Variable | Points To | Usage |
|----------|-----------|-------|
| `EXPERIMENTAL_PYTHON` | experimental/.venv/python | Development/testing |
| `STABLE_PYTHON` | stable/.venv/python | Production skills |
| `SKILL_PYTHON` | stable/.venv/python | Default for skill execution |

### Why Two Venvs?

| Aspect | Experimental | Stable |
|--------|--------------|--------|
| **Purpose** | Development & testing | Production use |
| **Dependencies** | May have untested packages | Only synced, validated packages |
| **Used by** | Developer during skill creation | Claude Code globally via ~/.claude/skills |
| **Updated** | Manually by developer | Automatically on /skill-lab:sync |

This ensures:
- Experimental dependencies don't affect production
- Clean environment for testing new packages
- Automatic dependency sync on merge
- Skills always have their required packages in production

## Benefits Summary

| Aspect | Benefit |
|--------|---------|
| **Isolation** | Physical separation prevents accidental changes |
| **Speed** | No branch switching needed |
| **Safety** | Stable always contains tested code |
| **Flexibility** | Easy to experiment without risk |
| **Visibility** | Clear which code is production vs experimental |
