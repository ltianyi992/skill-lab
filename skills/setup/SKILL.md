---
name: setup
description: "Initialize the Blue-Green skill development environment. Creates stable and experimental folders with Git Worktree isolation. Run this once after installing the plugin. Use when: user wants to set up skill-lab, initialize environment, or first time setup."
disable-model-invocation: true
allowed-tools: Bash(python *)
---

# Environment Setup

Initialize the Blue-Green development environment for skill development.

## What This Does

1. Creates `~/Desktop/skills-stable` (production skills, main branch)
2. Creates `~/Desktop/skills-experimental` (development skills, dev branch via Git Worktree)
3. Links `~/.claude/skills` → `skills-stable` (global availability)
4. Creates Python virtual environment in experimental folder
5. Configures Git for version control

## Execution

> **⚠️ CRITICAL: You MUST execute the bootstrap.py script below. Do NOT attempt to create the environment manually.**

Run the bootstrap script using the exact command:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.py"
```

**Important Notes:**
- `${CLAUDE_PLUGIN_ROOT}` is automatically set by Claude Code to this plugin's directory
- Do NOT substitute or modify this variable
- Do NOT create folders or links manually - the script handles everything

## Verification

After running the script, verify the setup by checking the global link target:

**Windows:**
```bash
dir "%USERPROFILE%\.claude\skills"
```

**Mac/Linux:**
```bash
ls -la ~/.claude/skills
```

The link MUST point to `skills-stable`, NOT `skills-experimental`.

## Post-Setup

After successful setup, inform the user:

> Environment initialized successfully!
>
> - **Stable folder**: `~/Desktop/skills-stable` (globally available)
> - **Experimental folder**: `~/Desktop/skills-experimental` (for development)
>
> **Next steps:**
> 1. Create new skills in the experimental folder
> 2. Test them in your projects using `/skill-lab:link`
> 3. When ready, sync to stable using `/skill-lab:sync`
>
> Say "show skill-lab status" anytime to check your environment.

## Safety

- This script is idempotent (safe to run multiple times)
- Will NOT overwrite existing `~/.claude/skills` if it's a real directory
- Requires Git and Python to be installed
