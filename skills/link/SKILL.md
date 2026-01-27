---
name: link
description: "Link a project to the experimental skills environment. Creates a local .claude/skills shortcut so the project can use experimental skills. Use when: user wants to connect project to lab, use experimental skills, or test skills in a project."
argument-hint: "[project-path]"
---

# Link Project to Experimental

Create a local `.claude/skills` link in a project folder pointing to the experimental environment.

## Execution

```bash
python "$PLUGIN_ROOT/scripts/handler.py" link "$ARGUMENTS"
```

If no path provided via `$ARGUMENTS`, use the current working directory.

## What This Does

Creates a junction/symlink:
```
<project>/.claude/skills → ~/Desktop/skills-experimental
```

This allows the project to access experimental skills without affecting the global stable skills.

## User Communication

### Before Linking
```
Link this project to experimental skills?

Project: /path/to/your/project
Target:  ~/Desktop/skills-experimental

This creates a local shortcut - your project will use experimental skills
instead of the global stable ones.

Proceed? [Y/n]
```

### After Linking
```
Project linked to experimental environment!

Created: /path/to/your/project/.claude/skills
      → ~/Desktop/skills-experimental

You can now use experimental skills in this project.
Say "unlink" when you're done experimenting.
```

### If Already Linked
```
This project is already linked to experimental skills.
Link: /path/to/your/project/.claude/skills
```

### If Path Invalid
```
Cannot link: the specified path does not exist or is not a directory.
```

Adapt all messages to the user's language.
