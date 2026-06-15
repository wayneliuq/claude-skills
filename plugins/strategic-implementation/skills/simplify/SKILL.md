---
name: simplify
description: Code-level simplicity reviewer. Scans changed files (default `git diff <merge-base>...HEAD`) for reuse misses, dead code candidates, comment hygiene problems, and shape/naming inconsistencies. Reports only — never auto-edits source. Graph-first scan via code-review-graph MCP; file reads only as fallback. Invoked as a final pass by `post-execution` regression-check, and standalone-runnable on any branch.
---

# simplify

Code-level simplicity review of a changed working set. Produces a structured report; the PM (or a downstream skill) decides per-finding disposition. The skill never auto-edits source.

## Attribution

Adapted from two upstream sources:

- **`anthropic-skills:simplify`** (top-level Anthropic skill — "Review changed code for reuse, quality, and efficiency, then fix any issues found"). This in-repo skill keeps the review portion and intentionally **drops** the auto-fix portion (HARD DECISION from the v3.2.1 brief: report-only, PM-gated dispositions).
- **`agents/plan-simplify.md`** (in-plugin plan-time simplicity reviewer used by `review`). That agent operates on execution plans before code exists; this skill operates on actual diffs after code lands. Distinct names, distinct surfaces.

## Inputs

- **Target ref** (optional; default `git diff $(git merge-base HEAD main)...HEAD`). If a `<base>` arg is provided, use `git diff <base>...HEAD`.
- **Feature folder** (optional). If provided, write the report there; else write to `./` (cwd).
- **Max LOC per finding** (optional; default 50).

## Step 0 — Pre-flight

1. `command -v git` succeeds.
2. `mcp__code-review-graph__list_graph_stats_tool` returns `total_nodes > 0`. If 0 (graph empty for this repo): emit `FLAG: graph empty; falling back to file-read-only mode` and proceed with reduced confidence.
3. `git diff --name-only <base>...HEAD` returns a non-empty list. If empty: write a one-line report saying "no changed files in target ref; nothing to review" and exit 0.

## Step 1 — Identify changed files

```
git diff --name-only <base>...HEAD
```

Filter to source files (skip pure docs unless the deliverable is itself a docs/skill change — heuristic: include any path under `plugins/`, `src/`, `lib/`, `app/`, etc., even if `.md`).

## Step 2 — Graph-first scan (token-efficient)

For each changed file with a graph entry:

- **Reuse-miss detection.** For every new function / class / public symbol introduced in this diff, run `mcp__code-review-graph__semantic_search_nodes` with the symbol name + a short purpose phrase. If the search returns existing nodes with similar purpose at high similarity, flag as **reuse miss**.
- **Size flags.** Run `mcp__code-review-graph__find_large_functions_tool` over the changed files; flag any function exceeding the repo's existing 90th-percentile size as **shape/naming inconsistency** (size axis).
- **Dead-code candidates.** Run `mcp__code-review-graph__refactor_tool` with dead-code mode over the changed files; corroborate each candidate with `query_graph` `callers_of` to confirm zero callers.
- **Unused exports.** For every new public function/class, `query_graph` `callers_of` — zero callers in this repo == flag as **dead code (unused export)** unless the symbol is on a known external-API surface.

## Step 3 — File-read fallback

Only for files the graph cannot analyze (e.g. markdown skills, shell scripts, config files):

- `Read` with `offset`/`limit` to pull short hunks around the changed lines (use `git diff -U0 <base>...HEAD <file>` to get exact line ranges). Never read the whole file.
- Apply lightweight heuristics:
  - **Comment hygiene:** comment lines exceeding 30% of the changed-block size; stale `TODO`/`FIXME`; comments restating the next line ("// increment i" → noise).
  - **Shape/naming inconsistency:** new identifiers diverging from sibling-file conventions (camelCase vs snake_case, `*_tool` vs `tool_*` etc.).

## Step 4 — Findings classification

Each finding falls into one of four categories:

1. **Reuse miss** — the diff introduces a symbol that already exists or has a near-duplicate.
2. **Dead code** — a function/class/branch is added but unused, or removed callers leave residual code.
3. **Comment hygiene** — over-commenting, stale TODOs, redundant docstrings, or commented-out code.
4. **Shape/naming inconsistency** — new code diverges from sibling-file conventions in style, naming, or sizing.

Severity:
- `high` — same-name same-purpose duplicate of an existing symbol; dead-code with zero callers in same diff; commented-out code blocks ≥ 10 lines.
- `med` — near-duplicate (semantic, not syntactic); naming divergence; stale TODOs older than 90 days.
- `low` — minor over-commenting; restating-next-line noise.

Cap each finding at the `max_loc_per_finding` bound (default 50); if the offending region is larger, cite ranges and summarize.

## Step 5 — Write report

Choose path:
- If feature folder provided: scan for existing `simplify-report-NN.md` files; pick `NN = (max existing) + 1`, zero-padded; default `01`. Write to `<feature-folder>/simplify-report-NN.md`.
- Else: write to `./simplify-report-NN.md` (cwd) with the same numbering rule.

Report structure:

```markdown
# Simplify report NN — <feature slug or repo name>
_Target ref: `<base>...HEAD` · Date: <date> · Mode: <graph-first | read-fallback>_

## Summary
- Files scanned: <N>
- Findings: <total> (high: <h>, med: <m>, low: <l>)
- Categories: reuse-miss <r>, dead-code <d>, comment-hygiene <c>, shape/naming <s>

## Findings

### F-01 — <category> — <severity> — <one-line title>
**File:** `<path>:<line-range>`
**Symbol / region:** `<name or excerpt>`
**Why:** <one paragraph; cite graph evidence if applicable, e.g. "duplicates `existing_symbol at other/file.py:88` per semantic_search_nodes>0.85">
**Suggested action:** <one sentence>

### F-02 — ...
```

The report is output-only. The PM dispositions each finding **conversationally** (`apply` / `defer` / `dismiss`) in chat — `executing-plans` / `post-execution` record the disposition; the report file is not hand-edited. The skill never edits source.

## Step 6 — Output

Print to chat:

```
Simplify report written: <path>
Findings: <total> (high: <h>, med: <m>, low: <l>)
```

Do not summarize each finding inline; the report is the artifact.

If invoked from `executing-plans` or `post-execution`, return the report path so the calling skill can surface it for PM disposition.

## Standalone invocation

Invokable as `/strategic-implementation:simplify` on any committed branch. Default behavior: scan `git diff $(git merge-base HEAD main)...HEAD`, write `./simplify-report-NN.md`.

## Tone discipline

Terse. Substance exact. Drop articles, filler ("just", "really", "basically"), pleasantries, hedging. Fragments OK if unambiguous. One sentence per update is enough.

**Carve-outs (do NOT compress):** code blocks, tool output, BLOCK/FLAG callouts, irreversible-action warnings, PM-facing approval prompts.

---

## Record routing — externalized artifact store

Per-feature **records** (brief / plan / validation-log / checkpoint / reports / mockup / brief-meta) route through the store adapter, not the feature folder directly: wherever a step says write/read `<feature-folder>/<file>`, use the store address `<repo-id>/<date-slug>/<file>` with in-repo fallback. Full read/write/fallback protocol: [`scripts/store/README.md`](../../scripts/store/README.md#record-routing-protocol-agent-facing). **Durable tier — `project-learnings.md`, `documentation-registry.md` — stays in-repo, never routed to the store.**
