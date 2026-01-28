# Skill Lab

**[中文](README.md) | English**

**One-click setup for Claude Code Skills development environment**

---

## Why Skill Lab?

We're entering the **Age of Skills**.

Claude Code's Skills give AI extensible capabilities — you can download skills created by others or write your own. But here's the problem:

- Is that downloaded skill safe? Will it break your environment if you put it directly into `~/.claude/skills`?
- Your own skill is still being debugged — how do you avoid affecting ongoing projects?
- Every time you want to try a new skill, you have to manually backup and restore. Too tedious!

**Skill Lab was built to solve these problems.**

It provides a **safe sandbox environment** where you can:
- Experiment with any skill (downloaded or self-made)
- Without worrying about breaking your stable environment
- One-click sync to production when ready

---

## Core Concept: Blue-Green Deployment

```
Your Project
    │
    │ Need a skill?
    ▼
┌─────────────────────────────────────────────────────┐
│  EXPERIMENTAL (Development)                          │
│  ~/Desktop/skills-experimental                       │
│                                                      │
│  - Freely experiment with any new skill              │
│  - Isolated Python virtual environment               │
│  - Something wrong? Delete and restart, zero impact  │
└─────────────────────────────────────────────────────┘
                    │
                    │ Tests passed? One-click sync
                    ▼
┌─────────────────────────────────────────────────────┐
│  STABLE (Production)                                 │
│  ~/Desktop/skills-stable                             │
│                                                      │
│  - Auto-linked to ~/.claude/skills                   │
│  - Only verified skills can enter                    │
│  - Globally available, shared across all projects    │
└─────────────────────────────────────────────────────┘
```

**Simply put: Experiment in the lab first, deploy only when confirmed safe.**

---

## One-Click Setup

### Installation

```bash
# 1. Add the plugin source
/plugin marketplace add your-username/skill-lab

# 2. Install the plugin
/plugin install skill-lab@your-username-skill-lab

# 3. Initialize the environment (run once)
/skill-lab:setup
```

Three steps, and your skill development environment is ready.

### What You Get After Setup

| Directory | Purpose |
|-----------|---------|
| `~/Desktop/skills-stable` | Stable version, auto-linked globally |
| `~/Desktop/skills-experimental` | Experimental version, safe playground |
| Each has its own `.venv` | Isolated dependencies, no conflicts |

---

## Use Cases

### Case 1: Trying a Downloaded Skill

```
1. Put the downloaded skill into ~/Desktop/skills-experimental/
2. Run /skill-lab:link in your project
3. Test if the skill works well and is safe
4. Satisfied? Run /skill-lab:sync to sync to stable
5. Not satisfied? Just delete it, nothing affected
```

### Case 2: Developing Your Own Skill

```
1. Create your skill in ~/Desktop/skills-experimental/
2. Install dependencies: pip install xxx && pip freeze > requirements.txt
3. Link to project for testing: /skill-lab:link
4. Iterate until satisfied
5. Sync to stable: /skill-lab:sync (dependencies auto-install to stable)
```

### Case 3: Smart Matching

When you open a project, Skill Lab automatically detects:

```
"I noticed your project has PDF files, and you have a 'pdf' skill
in your experimental environment. Would you like to link it to help
process PDFs?"
```

**Ask first, act later. Never autonomous.**

---

## Command Reference

| Command | Purpose |
|---------|---------|
| `/skill-lab:setup` | Initialize environment (once) |
| `/skill-lab:status` | Check environment status |
| `/skill-lab:sync` | Sync experimental to stable (with dependencies) |
| `/skill-lab:link` | Link current project to experimental |
| `/skill-lab:unlink` | Unlink project |
| `/skill-lab:skill-matcher` | Detect skill-project compatibility |

---

## Technical Architecture

```
~/.claude/skills ◄─── Junction/Symlink
        │
        ▼
skills-stable/                    skills-experimental/
├── .venv/ (prod deps)            ├── .venv/ (dev deps)
├── requirements.txt              ├── requirements.txt
├── pdf/                          ├── pdf/
│   └── SKILL.md                  │   └── SKILL.md
└── [other stable skills]         └── [experimental skills]
        │                                   │
        │◄────── git merge ◄───────────────┘
        │◄────── pip install -r requirements.txt
```

Both directories share Git history via **Git Worktree**, but are physically isolated. During sync:
1. Code merges via `git merge`
2. Dependencies auto-install to stable via `pip install`

---

## Why This Matters

**Three trends in the Age of Skills:**

1. **Skills will multiply** — Communities will produce countless skills; you need a safe way to try them
2. **Skills will get complex** — Skills with dependencies and scripts need isolated environments
3. **Skills will become standard** — Like VS Code extensions, managing skills needs professional tools

**Skill Lab is that professional tool.**

It's not just a "development environment" — it's an **upgrade in workflow**:

- From "modify global directly" → "experiment first, deploy later"
- From "manage dependencies manually" → "auto-sync dependencies"
- From "fix after breaking" → "isolated testing, zero risk"

---

## Requirements

- Claude Code v1.0.33+
- Git
- Python 3.8+

## Project Structure

```
skill-lab/
├── skills/                 # Plugin commands
│   ├── setup/             # Initialize environment
│   ├── status/            # Check status
│   ├── sync/              # Sync to stable
│   ├── link/              # Link project
│   ├── unlink/            # Unlink project
│   └── skill-matcher/     # Smart matching
├── hooks/                  # Auto-triggered hooks
├── scripts/               # Core scripts
│   ├── bootstrap.py       # Environment setup
│   └── handler.py         # Command handler
└── references/
    └── architecture.md    # Detailed architecture docs
```

## License

MIT

---

> **Skill Lab — Making every skill experiment safe and controlled.**
