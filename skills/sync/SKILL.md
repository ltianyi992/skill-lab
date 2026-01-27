---
name: sync
description: "Sync experimental skills to stable/production. Commits changes in experimental and merges to stable branch. Use when: user wants to promote skills, sync to stable, publish skills, or move experimental to production."
argument-hint: "[commit message]"
---

# Sync to Stable

Commit changes in the experimental environment and merge them into stable (production).

## Execution

```bash
python "$PLUGIN_ROOT/scripts/handler.py" sync -m "$ARGUMENTS"
```

If no commit message provided via `$ARGUMENTS`, either:
1. Auto-generate a message based on changes
2. Ask the user for a brief description

## Workflow

1. **Check for changes** in experimental folder
2. **Stage all changes** (`git add .`)
3. **Commit** with the provided message
4. **Merge** dev branch into main (in stable folder)

## User Communication

### Before Sync
Show what will be synced:
```
Ready to sync to stable:

Changes to commit:
  - Modified: pdf-helper/handler.py
  - New: code-analyzer/

Commit message: "Add code-analyzer skill and improve pdf-helper"

Proceed? [Y/n]
```

### After Sync
```
Synced successfully!

Commit: abc1234
Message: "Add code-analyzer skill and improve pdf-helper"

Your skills are now available globally via ~/.claude/skills
```

### If No Changes
```
Nothing to sync - experimental branch is clean.
```

### If Merge Conflict
```
Sync partially complete - merge conflict detected.

Your changes are committed in experimental (commit abc1234).
However, merging to stable failed due to conflicts.

Please resolve manually:
  cd ~/Desktop/skills-stable
  git merge dev
  # resolve conflicts
  git commit
```

Adapt all messages to the user's language.
