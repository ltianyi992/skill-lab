---
name: status
description: "Check the status of skill-lab environment. Shows experimental branch status, pending changes, and available skills. Use when: user asks about environment status, what skills exist, or checks experimental changes."
---

# Environment Status

Check the current state of the skill-lab environment.

## Execution

Run the handler script:

```bash
python "$PLUGIN_ROOT/scripts/handler.py" info
```

## Information to Display

Present the status in a clear, organized format:

### Environment Health
- Whether stable and experimental folders exist
- Whether the global skills link is configured
- Current Git branch in experimental

### Experimental Branch Status
- Clean or has uncommitted changes
- List of modified files
- List of untracked files (new skills)

### Available Skills
Run `python "$PLUGIN_ROOT/scripts/handler.py" skills` to list experimental skills.

## Example Output Format

```
Skill Lab Status

Environment:
  Stable:       ~/Desktop/skills-stable (OK)
  Experimental: ~/Desktop/skills-experimental (OK)
  Global Link:  ~/.claude/skills → stable (OK)

Experimental Branch (dev):
  Status: 2 modified files, 1 new skill

  Modified:
    - pdf-helper/handler.py
    - pdf-helper/SKILL.md

  New Skills:
    - code-analyzer/

Available Experimental Skills:
  1. pdf-helper - Extract text from PDF files
  2. code-analyzer - Analyze code structure
```

Adapt the output format to the user's language.
