---
name: skill-matcher
description: "Analyze project file types and match against available experimental skills. Use when: user wants to find relevant skills, check skill compatibility, or see what experimental skills match the current project."
---

# Skill Matcher

Analyze the current project and find matching experimental skills.

## What This Does

1. Scans the current project for file types
2. Lists all available experimental skills from `~/Desktop/skills-experimental`
3. Analyzes semantic matches between project needs and skill capabilities
4. Reports which skills may be useful for this project

## Execution

Run the skill matcher using the main handler:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/handler.py" detect
```

## Interpreting Results

The handler outputs JSON with:

- `project_extensions`: File types found in the current project
- `experimental_skills`: Available skills with names and descriptions
- `potential_matches`: Skills that may be relevant based on semantic matching

## After Analysis

If matching skills are found and the project is NOT already linked:

1. Present the matches to the user
2. Explain why each skill might be useful
3. Ask: "Would you like to link these experimental skills to your project using `/skill-lab:link`?"

**Important:** Do NOT automatically link. Always ask the user for permission first.

## No Matches

If no experimental skills exist or none match:

- Inform the user that no matching skills were found
- Suggest they can create new skills in `~/Desktop/skills-experimental`
- Mention they can check `/skill-lab:status` to see the environment state
