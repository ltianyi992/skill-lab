---
name: unlink
description: "Unlink a project from experimental skills. Removes the local .claude/skills shortcut. Skills remain safe in experimental folder. Use when: user wants to disconnect, unlink, stop using experimental skills, or done experimenting."
argument-hint: "[project-path]"
---

# Unlink Project from Experimental

Remove the local `.claude/skills` link from a project folder.

## Execution

```bash
python "$PLUGIN_ROOT/scripts/handler.py" unlink "$ARGUMENTS"
```

If no path provided via `$ARGUMENTS`, use the current working directory.

## What This Does

Removes the junction/symlink at:
```
<project>/.claude/skills
```

**Important**: This only removes the shortcut. Your experimental skills remain safe in `~/Desktop/skills-experimental`.

## User Communication

### Before Unlinking
```
Unlink this project from experimental skills?

Project: /path/to/your/project
Current link: .claude/skills → ~/Desktop/skills-experimental

This only removes the shortcut - your skills stay safe in the experimental folder.
The project will return to using global stable skills.

Proceed? [Y/n]
```

### After Unlinking
```
Project unlinked from experimental environment.

Removed: /path/to/your/project/.claude/skills

Your experimental skills are still available at:
~/Desktop/skills-experimental

This project now uses global stable skills from:
~/.claude/skills
```

### If Not Linked
```
This project is not linked to experimental skills.
Nothing to unlink.
```

### If Link Points Elsewhere
```
Warning: The .claude/skills link in this project points to a different location:
Current: /path/to/your/project/.claude/skills → /some/other/path

This was not created by skill-lab. Remove anyway? [y/N]
```

Adapt all messages to the user's language.

## Natural Language Triggers

Users may express this intent in various ways:
- "unlink from experimental"
- "disconnect from lab"
- "stop using experimental skills"
- "remove experimental link"
- "断开连接"
- "取消链接"

Recognize these intents and execute this skill.
