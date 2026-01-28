---
name: skill-matcher
description: "PROACTIVE skill matching - Use this BEFORE starting any task that might benefit from experimental skills. Analyzes project files and semantic matches against available skills. MUST be called when user requests work on: PDF, documents, data processing, or any task matching experimental skill keywords."
---

# Skill Matcher

**PROACTIVE WORKFLOW TOOL** - Analyze the current project and find matching experimental skills BEFORE starting tasks.

## WHEN TO USE (IMPORTANT!)

Call this skill-matcher **BEFORE** executing any user task when:

1. User requests work on specific file types (PDF, Excel, images, etc.)
2. User's task keywords match any experimental skill name or description
3. Starting a new session in a project that hasn't been checked yet
4. User explicitly asks about available skills

**DO NOT** skip this step and jump directly to task execution!

## What This Does

1. Scans the current project for file types
2. Lists all available experimental skills from `~/Desktop/skills-experimental`
3. Performs semantic matching between:
   - User's task description
   - Project file types
   - Skill names and descriptions
4. Reports which skills may be useful

## Execution

```bash
python scripts/handler.py detect
```

## Workflow After Detection

### If Matches Found (Project NOT Linked):

1. **STOP** - Do not proceed with the original task yet
2. **PRESENT** matches to user with clear explanation:
   ```
   I found an experimental skill that can help with your task:
   - **pdf**: [description]

   Would you like me to link it to this project? (/skill-lab:link)
   ```
3. **WAIT** for user response
4. If YES → Run `/skill-lab:link`, then proceed with task
5. If NO → Proceed without skill, note limitations

### If Matches Found (Project Already Linked):

- Proceed with task using the linked skills
- Mention which skill you're using

### If No Matches:

- Inform user no matching skills found
- Proceed with task using standard capabilities
- Suggest creating new skill if task is complex/recurring

## Example Workflow

```
User: "Help me extract tables from this PDF report"

WRONG ❌: Immediately try to read the PDF

RIGHT ✓:
1. Run skill-matcher detect
2. Find "pdf" skill matches
3. Ask: "I have a 'pdf' skill for PDF manipulation. Link it first?"
4. Wait for user confirmation
5. If yes, run /skill-lab:link
6. Then proceed with PDF extraction
```
