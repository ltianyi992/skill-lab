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
        +-- claude-env-manager/    <- Seeded Manager Skill
        |       +-- SKILL.md
        |       +-- handler.py
        |
        +-- [other stable skills...]

~/Desktop/skills-experimental (dev branch - Git Worktree)
        |
        +-- .venv/                 <- Isolated Python environment
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

### Safety Considerations

- **Never overwrite existing directories**: The bootstrap checks if `~/.claude/skills` exists as a directory
- **Junctions are transparent**: Applications see them as regular directories
- **Breaking the link**: Deleting the junction/symlink does not delete the target

## Blue-Green Workflow

### Development Flow

```
1. Develop in skills-experimental (dev branch)
   |
2. Test and validate changes
   |
3. Use Manager Skill to sync:
   - git add & commit in experimental
   - git merge dev into main (in stable)
   |
4. Changes now live in stable (global scope)
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

The experimental folder includes its own `.venv`:

```bash
~/Desktop/skills-experimental/.venv/
    bin/python    (or Scripts/python.exe on Windows)
    lib/
    ...
```

This ensures:
- Experimental dependencies don't affect stable
- Clean environment for testing new packages
- Easy cleanup by deleting .venv

## Benefits Summary

| Aspect | Benefit |
|--------|---------|
| **Isolation** | Physical separation prevents accidental changes |
| **Speed** | No branch switching needed |
| **Safety** | Stable always contains tested code |
| **Flexibility** | Easy to experiment without risk |
| **Visibility** | Clear which code is production vs experimental |
