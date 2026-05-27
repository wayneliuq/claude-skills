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
