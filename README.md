# Skill Lab

A Claude Code plugin for Blue-Green skill development. Safely develop and test skills in an isolated experimental environment before promoting to stable/production.

## Features

- **Blue-Green Architecture**: Physical separation between stable (production) and experimental (development) skills
- **Git Worktree Isolation**: Both environments share Git history but have independent working directories
- **Auto-Detection**: Automatically suggests relevant experimental skills based on your project's file types
- **Natural Language Control**: Use conversational commands to manage your environment
- **Multi-Language Support**: Commands and responses adapt to your conversation language

## Installation

### Step 1: Add the Marketplace

```bash
/plugin marketplace add your-username/skill-lab
```

### Step 2: Install the Plugin

```bash
/plugin install skill-lab@your-username-skill-lab
```

### Step 3: Initialize the Environment

```bash
/skill-lab:setup
```

This creates:
- `~/Desktop/skills-stable` - Production skills (linked to `~/.claude/skills`)
- `~/Desktop/skills-experimental` - Development skills (Git Worktree on `dev` branch)

## Commands

| Command | Description |
|---------|-------------|
| `/skill-lab:setup` | Initialize the environment (run once) |
| `/skill-lab:status` | Check environment and experimental branch status |
| `/skill-lab:sync` | Commit experimental changes and merge to stable |
| `/skill-lab:link` | Link current project to experimental skills |
| `/skill-lab:unlink` | Unlink project from experimental skills |

## Workflow

```
1. Create skills in ~/Desktop/skills-experimental
         │
         ▼
2. Link your project: /skill-lab:link
         │
         ▼
3. Test and iterate on your skills
         │
         ▼
4. When ready, sync: /skill-lab:sync "Add new feature"
         │
         ▼
5. Skills now available globally via ~/.claude/skills
```

## Natural Language Support

You can also use natural language:

- "Set up my skill development environment"
- "Link this project to the lab"
- "Sync my experimental skills to stable"
- "Show me what's in the experimental environment"
- "Disconnect from experimental" / "断开连接"

## Architecture

```
~/.claude/skills (Global) ──────────────────┐
                                            │ symlink/junction
                                            ▼
~/Desktop/skills-stable (main branch) ◄────────────────────┐
    │                                                       │
    │ Git Worktree                                         │ merge
    ▼                                                       │
~/Desktop/skills-experimental (dev branch) ─────sync───────┘
    │
    └── .venv/ (isolated Python environment)
```

## Directory Structure

```
skill-lab/
├── .claude-plugin/
│   └── plugin.json           # Plugin manifest
├── skills/
│   ├── setup/                # /skill-lab:setup
│   ├── status/               # /skill-lab:status
│   ├── sync/                 # /skill-lab:sync
│   ├── link/                 # /skill-lab:link
│   └── unlink/               # /skill-lab:unlink
├── agents/
│   └── skill-matcher.md      # Haiku agent for skill matching
├── hooks/
│   └── hooks.json            # SessionStart and Stop hooks
├── scripts/
│   ├── bootstrap.py          # Environment setup script
│   ├── handler.py            # CLI handler
│   └── hooks/                # Hook scripts
├── references/
│   └── architecture.md       # Detailed architecture docs
└── README.md
```

## Requirements

- Claude Code v1.0.33 or later
- Git
- Python 3.8+

## License

MIT
