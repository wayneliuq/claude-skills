# Graph-freshness setup & findings

_Feature: graph-freshness · 2026-05-26_

Records the machine-global config changes (which live outside this repo's git tree) so they are reproducible, plus the D4 documentation-indexing determination.

## D1 — SessionStart full reparse (`~/.claude/settings.json`)

**Before:**
```json
"SessionStart": [
  { "matcher": "", "hooks": [
    { "type": "command", "command": "code-review-graph status", "timeout": 10 }
  ]}
]
```

**After:**
```json
"SessionStart": [
  { "matcher": "", "hooks": [
    { "type": "command", "command": "sh -c '[ -d .code-review-graph ] && code-review-graph build --skip-flows'", "timeout": 120 }
  ]}
]
```

**Why:** the old `status` only printed stats; it never rebuilt. A full `build` at session start catches drift no matter how it arrived (pull / rebase / branch switch / external edit). The `[ -d .code-review-graph ]` guard makes it a true no-op in repos without a graph (avoids paying full-tree parse cost and avoids auto-creating unwanted graphs). `--skip-flows` keeps the full file reparse (signatures + FTS — the freshness guarantee) and only defers the flow/community pass; timeout raised 10 → 120 for large repos.

## D2 — All editing tools trigger a refresh (`~/.claude/settings.json`)

**Before:** PostToolUse matcher `"Edit|Write|Bash"`
**After:** PostToolUse matcher `"Edit|Write|MultiEdit|NotebookEdit|Bash"` (hook command `code-review-graph update --skip-flows`, timeout 30, unchanged).

**Why:** the old matcher missed `MultiEdit` and `NotebookEdit`, so edits via those tools never triggered a rebuild — a silent staleness gap depending purely on which tool was used. The new matcher enumerates the complete set of Claude file-editing tools (Edit, Write, MultiEdit, NotebookEdit) plus Bash (shell-driven writes).

> ⚠️ **Maintenance note:** this matcher is a static allowlist. If Claude's editing-tool roster changes (a new file-editing tool is added), this matcher MUST be revisited or the "every editing tool" guarantee silently regresses.

`.ipynb` files ARE indexed by code-review-graph (`parser.py` maps `.ipynb → notebook`), so a `NotebookEdit` registers a real node change — validating D2 on a notebook is meaningful, not a no-op.

## D3 — Machine-wide post-merge refresh (per-repo install + init.templateDir)

In-repo artifacts (version-controlled):
- `scripts/git-hooks/post-merge` — canonical hook template (guards: `command -v code-review-graph` + `[ -d .code-review-graph ]`; `update --base ORIG_HEAD --skip-flows` with bare-update fallback).
- `scripts/install-graph-freshness-hooks.sh` — idempotent installer.

**Mechanism — and why NOT `core.hooksPath`:** global `core.hooksPath` is all-or-nothing — once set, git resolves *every* hook type from one dir for *every* repo and never falls back to per-repo `.git/hooks/`. That would have **silently disabled** `~/Documents/Development/axiph/.git/hooks/pre-commit` (which runs `code-review-graph detect-changes` + a managed `axiph-schema-warn` schema-drift guard). Instead the installer copies `post-merge` into each repo's own `.git/hooks/` (append-only — warns and skips any foreign hook, never overwrites) and sets `git config --global init.templateDir ~/.config/git/template` so future clones are seeded.

**Apply:**
```sh
sh scripts/install-graph-freshness-hooks.sh            # scan ~/Documents/Development (or pass repo paths)
sh scripts/install-graph-freshness-hooks.sh --uninstall  # rollback (removes only our hooks; unsets template)
```

**Verified on install:** axiph & memory.line & wayne-life-os got post-merge; axiph's pre-commit left untouched (timestamp unchanged); claude-skills' pre-existing post-merge refreshed in place with the new guard; firing axiph's post-merge advanced its graph's last-updated (cross-repo refresh proof); the hook no-ops cleanly in a graph-less dir; a fresh `git init` repo is seeded from the template.

> ⚠️ **Per-clone caveat:** existing repos need a one-time installer run; the template only auto-covers *new* clones. Re-running the installer is safe (idempotent).
