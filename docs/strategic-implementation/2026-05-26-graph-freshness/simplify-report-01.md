# Simplify report 01 — graph-freshness
_Target ref: `7823237...HEAD` · Date: 2026-05-26 · Mode: read-fallback (POSIX sh; not in graph)_

## Summary
- Files scanned: 2 (`scripts/git-hooks/post-merge`, `scripts/install-graph-freshness-hooks.sh`)
- Findings: 2 (high: 0, med: 0, low: 2)
- Categories: reuse-miss 0, dead-code 0, comment-hygiene 1, shape/naming 1

Note: the content-level duplication between `scripts/git-hooks/post-merge` and the copies the installer writes is the intended mechanism (canonical template → per-repo copies), not a reuse miss — excluded by design. Installer helpers (`is_ours`, `collect_targets`) are shared across install/uninstall paths — no duplication. All functions are reachable; no dead code.

## Findings

### F-01 — shape/naming — low — Default repo base is machine-specific
**File:** `scripts/install-graph-freshness-hooks.sh:24`
**Symbol / region:** `REPO_BASE="${CRG_REPO_BASE:-$HOME/Documents/Development}"`
**Why:** The default scan root hardcodes one developer's layout. Mitigated — it is overridable via `CRG_REPO_BASE` and bypassed entirely when explicit repo paths are passed as args. For personal machine tooling this is acceptable, but the hardcoded default limits reuse by anyone else and is invisible unless they read the source.
**Suggested action:** Acceptable as-is for personal use; if shared, surface the default in a `--help`/usage line. Lean **dismiss** (env override + arg path already cover it).

<!-- pm-disposition: -->

### F-02 — comment-hygiene — low — Header comment dense on post-merge hook
**File:** `scripts/git-hooks/post-merge:2-13`
**Symbol / region:** 11-line header comment over a 17-line file (~65%).
**Why:** High comment-to-code ratio. However the comment explains genuinely non-obvious behavior (why `ORIG_HEAD` as base, why two guards, that it's a copied template, relationship to the PostToolUse hook) — this is load-bearing context for a file that will be copied into many repos with no other documentation nearby.
**Suggested action:** Keep. The density is justified by the hook's standalone-in-each-repo nature. Lean **dismiss**.

<!-- pm-disposition: -->
