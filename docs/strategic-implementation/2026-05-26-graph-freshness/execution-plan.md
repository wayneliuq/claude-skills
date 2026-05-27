# Execution Plan: Harden code-review-graph freshness

_Implements: product-brief_graph-freshness.md · Date: 2026-05-26 · Autonomy: auto_

## Context

The code-review-graph silently goes stale because the only rebuild trigger (a PostToolUse `update --base HEAD~1`) re-parses just the tip commit; multi-commit batches (pull/rebase/branch switch) and edits via un-matched tools leave files stale, downgrading skills to file-read mode. This plan closes those gaps machine-wide: full reparse at session start (D1), all-editing-tools coverage (D2), and a per-repo-installed `post-merge` git hook (seeded to future clones via `init.templateDir`) so external/pulled changes rebuild everywhere (D3). D4 records the documentation-indexing investigation as a not-feasible determination with a researched alternative.

## Out-of-tree note (read first)

D1, D2, and D3 modify **machine-global files outside this repo** (`~/.claude/settings.json`, global git `init.templateDir`, and per-repo `.git/hooks/` in other repos). Those are not in this repo's git tree, so per-deliverable commits capture only the **in-repo reproducible artifacts**: the canonical hook template + installer script (D3) and the setup/findings record (D1/D2/D4). Each deliverable's commit bundles its in-repo artifact; the live config edit is applied as an execution step and verified by observation.

## Library lifecycle audit

### code-review-graph CLI
- **State that persists:** SQLite graph at `<repo>/.code-review-graph/graph.db`, a derived cache. Records "built-at commit" + per-file nodes/edges. `update` re-parses only files in `git diff <base>` (default `HEAD~1`) — the staleness root cause. `build` re-parses the whole tree.
- **Quirks / gotchas:** No language/glob config; `EXTENSION_TO_LANGUAGE` is hard-coded in the installed package (no `.md`). FTS5 indexes only the `nodes` table (parsed-code symbols), never raw file text. `update`/`build` in a repo with **no** `.code-review-graph/` may initialize one — so a global hook must guard on graph existence to stay a true no-op. Rebuild is sub-second on this repo; ruled-out concerns (timeout, SQLite lock) are not addressed by design.
- **Doc consulted:** installed package `…/site-packages/code_review_graph/parser.py:74` (extension map), `search.py:25` (FTS scope); `code-review-graph build|update --help`.

### git (hooks + init.templateDir)
- **State that persists:** Per-repo hooks live in each repo's `.git/hooks/`. `init.templateDir` (global) seeds **newly created/cloned** repos' `.git/` from a template dir at init/clone time — it does NOT touch existing repos and does NOT override per-repo hooks. `post-merge` runs at repo top-level after merge/pull; `ORIG_HEAD` = pre-merge HEAD (spans the whole pulled range).
- **Quirks / gotchas:** `core.hooksPath` was the original clarify-time mechanism but is **rejected** — it is all-or-nothing: a global value makes git resolve *every* hook type from one dir for *every* repo, never falling back to per-repo `.git/hooks/`. Verified blast radius: `~/Documents/Development/axiph/.git/hooks/pre-commit` (installed by code-review-graph: `detect-changes` + a managed `axiph-schema-warn` schema-drift guard) would be **silently disabled**. code-review-graph's own `install` also writes per-repo `pre-commit` hooks, so the conflict recurs. Chosen mechanism (per-repo install + `init.templateDir`) preserves all existing per-repo hooks.
- **Doc consulted:** `git help config` (core.hooksPath, init.templateDir); `git help githooks`; live scan: existing non-sample hooks = `axiph/.git/hooks/pre-commit`, `claude-skills/.git/hooks/post-merge`. No global `core.hooksPath`/`init.templateDir` set.

## Deliverables (DAG)

### D1 — Session start does a full reparse
- **Integration-risk class:** `a` (depends on code-review-graph CLI runtime)
- **User-acceptance steps (from brief):**
  1. In a repo, introduce a batch of changes not from this machine's Claude edits (pull several commits, switch branch, or rebase).
  2. Start a fresh Claude Code session in that repo.
  3. Confirm the graph reflects current files and current commit, not an earlier snapshot.
- **Validation method (chosen here):** `cli` + `post-hoc`.
  - cli (in-session, proves the mechanism): deliberately stale the graph (e.g. `update --base HEAD` after multi-file change, or note built-at < HEAD), run the **exact** new SessionStart command manually, confirm `code-review-graph status` shows built-at == HEAD and file/node counts current.
  - cli (config shape): `~/.claude/settings.json` SessionStart hook command == full `build` (not `status`).
  - post-hoc (per L-005 — settings reload only next session): on the next real session start, the SessionStart context shows fresh-build output. Cannot be observed in the current session.
- **Files:** `~/.claude/settings.json` (SessionStart hook); record in `docs/strategic-implementation/2026-05-26-graph-freshness/setup-and-findings.md`.
- **Steps:**
  1. In `~/.claude/settings.json`, change the SessionStart hook command from `code-review-graph status` to a graph-existence-guarded full build: `sh -c '[ -d .code-review-graph ] && code-review-graph build --skip-flows'`. The guard (mirrors D3's hook) makes it a true no-op in repos without a graph — avoids paying full-tree parse cost and avoids auto-initializing unwanted graphs in unrelated repos (runtime-risk finding). `--skip-flows` keeps the **full file reparse** (signatures + FTS — the freshness guarantee: built-at == HEAD, counts current) and only defers the derived flow/community pass; it does NOT weaken the HARD DECISION. Consistent with the existing PostToolUse `--skip-flows`.
  2. Raise that hook's `timeout` from 10 to 120 (full build can exceed 10s on large repos; the guard caps this cost to repos that actually use the graph).
  3. Leave PreToolUse (rtk) and PostToolUse untouched.
  4. Record the before/after snippet in `setup-and-findings.md`.
- **Deps:** none
- **Pre-flight env check:** `code-review-graph` on PATH; `~/.claude/settings.json` parses as valid JSON before and after.
- **may-invalidate:** none
- **Visual contract:** n/a
- **Consumer audit:** n/a — no shape change (config value only).

### D2 — Every editing tool triggers a refresh
- **Integration-risk class:** `a` (depends on CLI runtime + harness hook dispatch)
- **User-acceptance steps (from brief):**
  1. Have Claude change a tracked code file using each of the different ways it can edit files.
  2. After each, check the graph's reported state.
  3. Confirm the change is reflected regardless of which editing path produced it.
- **Validation method (chosen here):** `cli` + `post-hoc`.
  - cli (config shape): `~/.claude/settings.json` PostToolUse matcher == `Edit|Write|MultiEdit|NotebookEdit|Bash`.
  - post-hoc (per L-005 — matcher reload only next session): next session, perform a `MultiEdit` (code file) and a `NotebookEdit` (`.ipynb`) on tracked files; after each confirm `code-review-graph status` `last_updated` advances AND that a symbol from the edited file appears/updates in the graph (`status`/`query` shows the change reflected, not merely a timestamp bump — proves the brief's "change is reflected", not just "command ran"). `.ipynb` IS indexed (`parser.py` maps `.ipynb → notebook`), so a notebook edit registers a real node change. Not observable in current session.
- **Files:** `~/.claude/settings.json` (PostToolUse matcher); record in `setup-and-findings.md`.
- **Steps:**
  1. Edit the PostToolUse matcher string from `Edit|Write|Bash` to `Edit|Write|MultiEdit|NotebookEdit|Bash`. Completeness: these are the four file-editing tools Claude exposes (Edit, Write, MultiEdit, NotebookEdit) plus Bash (catches shell-driven writes) — the enumeration is the complete editing-tool set at authoring time, satisfying the "every editing tool" HARD DECISION by construction, not assertion.
  2. Leave the hook command (`update --skip-flows`, timeout 30) unchanged.
  3. Record the change in `setup-and-findings.md`, including a note that this matcher is a static allowlist that MUST be revisited if the Claude editing-tool roster changes (future-proofing).
- **Deps:** D1 (same file — sequence to avoid edit collision)
- **Pre-flight env check:** `~/.claude/settings.json` valid JSON after edit.
- **may-invalidate:** none
- **Visual contract:** n/a
- **Consumer audit:** n/a — no shape change.

### D3 — Machine-wide post-merge refresh via per-repo install + init template
- **Integration-risk class:** `a` (git + CLI runtime behavior)
- **Mechanism (revised after review):** `core.hooksPath` rejected — it is all-or-nothing and would silently disable `axiph/.git/hooks/pre-commit` (verified). Instead: a per-repo installer drops the `post-merge` hook into each repo's own `.git/hooks/` (appending, never clobbering existing hooks), and `init.templateDir` seeds future clones. Per-repo hooks (axiph's pre-commit, etc.) are untouched. "Machine-wide" is satisfied by running the installer across existing repos + the template covering future ones.
- **User-acceptance steps (from brief):**
  1. Pick a different repo than where this was set up (or a new clone).
  2. Pull a multi-commit batch into it.
  3. Confirm that repo's graph refreshes automatically from the pull, without copying setup into the repo first.
- **Validation method (chosen here):** `cli` (git hooks take effect immediately — fully in-session testable).
  1. In-repo artifacts exist: `scripts/git-hooks/post-merge` (canonical template) and `scripts/install-graph-freshness-hooks.sh` (installer).
  2. Run the installer; `git config --global init.templateDir` returns the template dir (`~/.config/git/template`) and `<template>/hooks/post-merge` is executable.
  3. Cross-repo (the brief's distinguishing signal): confirm a **second existing repo with a graph** (e.g. `axiph`) now has an executable `.git/hooks/post-merge` AND its pre-existing `.git/hooks/pre-commit` is **still present and unchanged**; then stale that repo's graph and fire its `post-merge` (invoke with `ORIG_HEAD` set, or a no-op merge) → its graph's built-at advances.
  4. Functional — graph-absent guard: run the hook from a dir with no `.code-review-graph/`; confirm it exits 0 and does nothing (no error, no graph created).
  5. Future-clone check: `git init` a throwaway repo; confirm it receives `post-merge` from the template.
- **Files (in-repo, committed):** `scripts/git-hooks/post-merge`, `scripts/install-graph-freshness-hooks.sh`. **Out-of-tree (applied, not committed):** `~/.config/git/template/hooks/post-merge`, global `init.templateDir`, and a `post-merge` copied into each targeted existing repo's `.git/hooks/`.
- **Steps:**
  1. Add `scripts/git-hooks/post-merge` — same logic as the current `.git/hooks/post-merge` **plus a graph-existence guard**: after the `command -v code-review-graph` guard, `[ -d .code-review-graph ] || exit 0` so it is a true no-op in graph-less repos. Then `code-review-graph update --base ORIG_HEAD --skip-flows` with the bare-`update` fallback (the fallback covers fast-forward pulls / absent ORIG_HEAD, verified).
  2. Add `scripts/install-graph-freshness-hooks.sh` — idempotent. Takes repo paths as args (default: a configurable base dir to scan). For each repo: if `.git/hooks/post-merge` is absent, install it; if present and already ours, refresh; if present and foreign, **append/warn — never overwrite**. Also set `git config --global init.templateDir ~/.config/git/template` and place `hooks/post-merge` there for future clones. Prints an uninstall note (remove `post-merge` from repos / unset `init.templateDir`). Does NOT set `core.hooksPath`, does NOT touch any other hook type.
  3. Run the installer against existing repos (this repo + the others under the dev base dir).
  4. This repo's existing `.git/hooks/post-merge` is refreshed in place from the template (the graph-existence guard added) — NOT deleted; under this mechanism the per-repo hook IS the live mechanism.
- **Deps:** none
- **Pre-flight env check:** scan existing repos for non-sample hooks before install (found: `axiph/.git/hooks/pre-commit`, `claude-skills/.git/hooks/post-merge`); installer must preserve foreign hooks. No global `core.hooksPath`/`init.templateDir` currently set.
- **may-invalidate:** none
- **Visual contract:** n/a
- **Consumer audit:** n/a — new files + git config; no data shape.

> **SCOPE / SAFETY CALLOUT (D3):** Chosen mechanism does NOT alter global hook resolution and does NOT override per-repo `.git/hooks/`. The installer is append-only/idempotent and must never overwrite a foreign hook (axiph's `pre-commit` stays intact). `init.templateDir` only seeds *new* repos. Rollback: delete the installed `post-merge` from each repo and `git config --global --unset init.templateDir`. The installer prints this.

### D4 — Documentation-indexing determination (not-feasible report)
- **Integration-risk class:** `d`
- **User-acceptance steps (from brief):**
  1. In a documentation-heavy repo, ask the graph for its coverage (file count / languages).
  2. Confirm prose/documentation files are represented, not only scripts and code.
  3. If the tool cannot represent documentation files at all, this deliverable is reported as not-feasible with the reason.
- **Validation method (chosen here):** `post-hoc` (documentation deliverable — evidence is PM reading the determination, no command output).
  - `docs/strategic-implementation/2026-05-26-graph-freshness/setup-and-findings.md` contains a "Documentation indexing (D4)" section stating: not feasible within code-review-graph (no `.md` in the hard-coded extension map; AST-only extraction; FTS indexes only parsed nodes; no language/glob flag → only path is forking the dependency, ruled out by the background brainstorm), plus the surveyed alternative (Graphify / `graphifyy`: indexes markdown but via an optional LLM pass, CLI/hook-based not MCP, separate tool adoption) and the rejected full-replacements (GitNexus, Codebase-Memory). Confirms step 3 of the acceptance flow (graph coverage shows code only; markdown unrepresentable).
- **Files:** `docs/strategic-implementation/2026-05-26-graph-freshness/setup-and-findings.md`.
- **Steps:**
  1. Write the D4 determination section with the findings above and a one-line forward pointer (Graphify as a separate future effort).
- **Deps:** none
- **may-invalidate:** none
- **Visual contract:** n/a
- **Consumer audit:** n/a.

## Parallel groups & order
- Group A (sequential, same file): D1 → D2.
- Group B: D3 (independent).
- Group C: D4 (independent).
- executing-plans runs one deliverable at a time; suggested order D1, D2, D3, D4. `setup-and-findings.md` is created in D1 and appended by D2/D4.

## Reused existing patterns
- Existing `~/.claude/settings.json` hooks (PostToolUse/SessionStart/PreToolUse) — edit in place, preserve `--skip-flows` convention and unrelated `enabledPlugins`/marketplaces.
- Existing `.git/hooks/post-merge` content (already authored, `command -v` guarded, `--base ORIG_HEAD`) — promoted to the canonical template, plus a graph-existence guard.
- D4 reuses already-completed research (no re-investigation).

## Risks & contingencies
- **Settings JSON corruption** — validate JSON parse before/after each edit; keep the unrelated keys untouched.
- **Global hook fires in graph-less repos** — mitigated by the `[ -d .code-review-graph ]` guard (D3 step 1) + validation step 4.
- **Full build slow on large repos at session start** — `--skip-flows` + timeout 120 + the graph-existence guard (D1 step 1) caps cost to repos that actually use the graph.
- **L-005 (config reload boundary)** — D1/D2 live-firing is unobservable in the current session; validation splits into in-session shape/command checks + post-hoc next-session confirmation. Plan does not claim in-session proof of hook firing.
- **Installer overwrites a foreign per-repo hook** — installer is append-only/idempotent and must never clobber an existing foreign hook (verified case: `axiph/.git/hooks/pre-commit`); validation step 3 confirms axiph's pre-commit survives.
- **`init.templateDir` collides with a pre-existing template** — none currently set (verified); installer should warn rather than overwrite if one appears.

## Out of scope for this plan
- Any remote/CI graph build.
- Replacing or forking code-review-graph; adopting Graphify or another tool (D4 records it as a separate future effort).
- The brief-biased "repomap" renderer from the background brainstorm.
- Speculative fixes for ruled-out failure modes (rebuild timeout, SQLite locking).

## Final steps on approval
1. Save execution plan → `docs/strategic-implementation/2026-05-26-graph-freshness/execution-plan.md`
2. Exit plan mode
3. Invoke `strategic-implementation:executing-plans`
   - Execution plan path: `docs/strategic-implementation/2026-05-26-graph-freshness/execution-plan.md`
   - Feature folder path: `docs/strategic-implementation/2026-05-26-graph-freshness/`
   - Autonomy level: auto
