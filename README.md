# claude-skills

Personal Claude Code plugins for my development workflow.

## Plugins

| Plugin | Description |
|---|---|
| [`strategic-implementation`](./plugins/strategic-implementation/) | Full planning-to-execution workflow: clarify → architecture → implementation guide → session plan → execute |

## Using this as a Claude Code marketplace

Add this repo as a marketplace once:

```bash
claude plugin marketplace add https://github.com/wayneliuq/claude-skills.git
```

Then install any plugin from it:

```bash
claude plugin install strategic-implementation@wayneliuq
```

To get updates after new plugins or changes are pushed:

```bash
claude plugin marketplace update wayneliuq
```

---

## How to create your own Claude Code GitHub marketplace

### 1. Repo structure

```
your-repo/
├── .claude-plugin/
│   └── marketplace.json        ← marketplace catalog (required)
└── plugins/
    └── your-plugin/
        ├── .claude-plugin/
        │   └── plugin.json     ← plugin manifest (required)
        ├── skills/
        │   └── skill-name/
        │       └── SKILL.md    ← skill definition
        └── agents/
            └── agent-name.md  ← optional agents
```

### 2. Marketplace catalog — `.claude-plugin/marketplace.json`

```json
{
  "name": "your-github-username",
  "owner": { "name": "Your Name" },
  "metadata": {
    "description": "Your marketplace description",
    "homepage": "https://github.com/your-username/your-repo"
  },
  "plugins": [
    {
      "name": "your-plugin",
      "version": "1.0.0",
      "source": "./plugins/your-plugin",
      "description": "What this plugin does"
    }
  ]
}
```

### 3. Plugin manifest — `plugins/your-plugin/.claude-plugin/plugin.json`

```json
{
  "name": "your-plugin",
  "version": "1.0.0",
  "description": "What this plugin does",
  "author": { "name": "Your Name" },
  "repository": "https://github.com/your-username/your-repo"
}
```

### 4. Skill definition — `skills/skill-name/SKILL.md`

```markdown
---
name: skill-name
description: One-line description shown in /help and used by Claude to decide when to invoke it
---

# Skill Title

Instructions for Claude...
```

Skills are invoked as `/your-plugin:skill-name` once the plugin is installed.

### 5. Adding a new plugin to the marketplace

1. Create the plugin directory under `plugins/`
2. Add its `.claude-plugin/plugin.json` manifest
3. Add an entry to `.claude-plugin/marketplace.json`
4. Push to GitHub

Users update with `claude plugin marketplace update your-github-username`.

### Key rules

- `marketplace.json` must be at `.claude-plugin/marketplace.json` (not the repo root)
- Each plugin needs its own `.claude-plugin/plugin.json`
- Skill files must be named `SKILL.md` (uppercase)
- The `name` field in `marketplace.json` must match the marketplace name users register (typically your GitHub username)

---

## Attribution

Some skills in `_copied-skills/` are derived from the
[superpowers](https://github.com/anthropics/claude-code-skills) plugin
by Anthropic, used here under their original license with modifications.
