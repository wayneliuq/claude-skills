# Execution Plan: context-mode adoption + /simplify skill (v2 — post-review)
_Implements: docs/strategic-implementation/2026-05-07-context-mode-and-simplify/product-brief_context-mode-and-simplify.md · Date: 2026-05-07 · Patched after alignment + simplify review_

## Context

Adopt three context-mode paradigms (graph-first reading, deliverable checkpointing, terse output) into the strategic-implementation skill chain by editing in-place skill prompts. Build a new `simplify` skill packaged inside this plugin (with attribution to upstream `anthropic-skills:simplify` / our existing plan-time `simplify` agent), auto-invoked mid-execution per a hardcoded rule plus a final pass in `post-execution`. Add a deterministic-script telemetry deliverable that emits `token-report.md` per feature folder using the harness's session JSONL transcript and `rtk gain --format json -p -H`.

**Review changes from v1 → v2:**
- Dropped standalone D3 (terseness rule); folded the 5-line block into the per-deliverable file edits where each skill is already being touched.
- Dropped D1's post-execution step (not in D1's brief UA steps).
- D5 counter persistence: derive from `git log` against `simplify-report-*.md` mtime; no new state.
- D5 PM-disposition contract spec'd: PM appends `<!-- pm-disposition: apply|defer|dismiss -->` per finding.
- D6 dropped baseline-comparison section from v1; pre-flight tightened to project-specific transcript dir.
- D6 simplify-report numbering: `simplify-report-NN.md` zero-padded monotonic per feature folder.
- D5 knob front-matter deferred; defaults hardcoded, tuneable via skill prompt edit.
- All artifact-creating deliverables now flag `may-invalidate: documentation-registry.md`.

Brief is approved (v0.3, three HARD DECISIONs locked).

## Library lifecycle audit

### code-review-graph MCP
- **State that persists:** Graph stored under `.code-review-graph/`. Auto-rebuilds on file changes via `PostToolUse` hooks. Lifetime = working tree; per-branch.
- **Quirks / gotchas:** Hooks can fail silently. `list_graph_stats_tool` returns last-built timestamp. **Mitigation:** D1 adds a graph-health pre-flight in `execution-plan` Step 2 — emit `FLAG: graph stale (last-built: <ts>)` and fall through to file-read mode.
- **Doc consulted:** `~/CLAUDE.md`, in-prompt MCP tool descriptions.

### Claude Code session JSONL transcript
- **State that persists:** One `.jsonl` per session under `~/.claude/projects/<path-encoded-cwd>/<uuid>.jsonl`. Path encoding: `/` → `-`, prefix `-`. Verified by inspection.
- **Quirks / gotchas:** Format undocumented; may shift across versions. D5 (was D6) script writes `unavailable` on parse failure and never blocks.
- **Doc consulted:** Direct inspection of `~/.claude/projects/` during planning.

### rtk CLI
- **State that persists:** Cumulative token-savings store. `rtk gain --format json -p -H` returns project-scoped command history.
- **Quirks / gotchas:** Possible name collision with `reachingforthejack/rtk`. D5 script verifies `rtk --version` matches "Rust Token Killer" before invoking; falls through to `unavailable` otherwise.
- **Doc consulted:** `~/RTK.md`, `rtk gain --help` (verified during planning).

### WebFetch
- One-time research read of `mksglu/context-mode` README — already done. No further runtime dependency.

---

## Deliverables (DAG)

### D1 — Graph-first reading wired into clarify + execution-plan, with terseness addendum
- **Integration-risk class:** `a` — depends on code-review-graph MCP.
- **User-acceptance steps (from brief):**
  1. Run `/strategic-implementation` on any feature touching existing code.
  2. Watch the `execution-plan` drafting messages — they cite results from `semantic_search_nodes`, `get_architecture_overview`, `query_graph`, or `get_impact_radius` instead of full-file `Read` calls.
  3. The plan text references concrete symbols (`function foo at path/file.py:42`, "callers: `bar`, `baz`") rather than paraphrased file content.
  4. Confirm at least one `Read` was avoided in favor of a graph query for a file the plan needed to ground a deliverable in.
- **Validation method:** `post-hoc` — verified on the next real run via D5's graph-vs-read ratio.
- **Files:**
  - `plugins/strategic-implementation/skills/clarify/SKILL.md`
  - `plugins/strategic-implementation/skills/execution-plan/SKILL.md`
- **Steps:**
  1. In `execution-plan/SKILL.md` Step 2, prepend a graph-health pre-flight: call `list_graph_stats_tool`; if stale, `FLAG: graph stale` and continue with file reads, else use graph-first.
  2. In the same Step 2, replace "Use **Glob** and **Grep**" with "Prefer code-review-graph queries (`semantic_search_nodes`, `query_graph`, `get_architecture_overview`); fall back to Glob/Grep/Read only when the graph cannot answer." Keep path-verification rule.
  3. In `clarify/SKILL.md`, after the doc-references step, add: "If clarify needs to ground a question in concrete repo symbols, prefer `semantic_search_nodes` over Read."
  4. **Append the shared Tone-discipline block** to both files (canonical 5-line block — see "Shared blocks" section below).
- **Deps:** none.
- **Pre-flight env check:** code-review-graph MCP responds to `list_graph_stats_tool`.
- **may-invalidate:** none.
- **Visual contract:** n/a.
- **Consumer audit:** n/a.

### D2 — `checkpoint.md` per atomic commit
- **Integration-risk class:** `d`.
- **User-acceptance steps (from brief):**
  1. During a multi-deliverable execution, observe `executing-plans` writing/updating a single `checkpoint.md` (alongside `validation-log.md`) at each deliverable's commit.
  2. Open `checkpoint.md` mid-run — see four short sections: **Done**, **In progress**, **Open decisions**, **Unresolved deviations** — each one line per entry, no prose.
  3. Force a context compaction (or open a fresh Claude Code session) and resume — the next deliverable picks up using `checkpoint.md` as the rehydration source.
  4. On final deliverable completion, `checkpoint.md` shows a terminal "complete" marker.
- **Validation method:** `cli` — `grep -A5 "checkpoint.md" plugins/strategic-implementation/skills/executing-plans/SKILL.md` shows the new write step inside the atomic-commit block. End-to-end behavior validated on the next real run.
- **Files:**
  - `plugins/strategic-implementation/skills/executing-plans/SKILL.md`
- **Steps:**
  1. In the per-deliverable atomic-commit section of `executing-plans/SKILL.md`, add a sub-step: write/update `<feature-folder>/checkpoint.md` in the same `git add` set as the deliverable's files and `validation-log.md`.
  2. Inline schema in the skill prompt:
     ```
     ## Done
     - D1 — <name> — <commit-sha-short> — <date>

     ## In progress
     - D<n> — <name> — started <date>

     ## Open decisions
     - <one line; resolved by editing the line, not appending>

     ## Unresolved deviations
     - <one line per active deviation; reference validation-log row id>

     <!-- complete: <date> --> (only on final deliverable)
     ```
  3. Explicit rule: "If you start a fresh session mid-execution, read `checkpoint.md` BEFORE the plan; treat it as the source of truth for what's done."
  4. Append the shared Tone-discipline block to `executing-plans/SKILL.md`.
- **Deps:** none.
- **Pre-flight env check:** none.
- **may-invalidate:** `docs/strategic-implementation/documentation-registry.md` (new artifact `checkpoint.md` per feature folder; one-row registry addition).
- **Visual contract:** n/a.
- **Consumer audit:** n/a.

### D3 — `simplify` skill packaged in this plugin
- **Integration-risk class:** `d` — new file creation.
- **User-acceptance steps (from brief):**
  1. List skills in this plugin — `simplify` appears under `plugins/strategic-implementation/skills/`.
  2. Run `/strategic-implementation:simplify` directly on any committed branch — it produces a short, structured report: **reuse misses**, **dead code candidates**, **comment hygiene**, **shape/naming inconsistencies**, with file:line citations.
  3. The skill's SKILL.md credits the upstream `anthropic-skills:simplify` it was adapted from.
  4. The skill uses graph tools (`semantic_search_nodes`, `find_large_functions_tool`, `refactor_tool`) and only falls back to file reads when the graph can't answer.
- **Validation method:** `cli` — invoke `/strategic-implementation:simplify` on the branch this work commits to; verify the produced `simplify-report-NN.md` exists and contains the four sections.
- **Files:**
  - `plugins/strategic-implementation/skills/simplify/SKILL.md` (NEW)
- **Steps:**
  1. Create `plugins/strategic-implementation/skills/simplify/` directory.
  2. Write `SKILL.md`:
     - Frontmatter: name, description, version.
     - Attribution paragraph: credits upstream `anthropic-skills:simplify` (top-level skill seen in available-skills) AND the existing in-plugin `agents/simplify.md` (plan-time simplicity reviewer — different surface; this skill is the code-level cousin).
     - Inputs: target ref (default `git diff <merge-base>...HEAD`), feature folder (optional), max-LOC-per-finding (default 50).
     - Step 1 — Identify changed files via `git diff --name-only <base>...HEAD`.
     - Step 2 — Graph-first scan (token-efficient):
       - `semantic_search_nodes` against each new function/class to detect duplicates of existing primitives (reuse miss).
       - `find_large_functions_tool` over changed files (size flags).
       - `refactor_tool` (dead-code mode) over changed files.
       - `query_graph` `callers_of` each new public function to surface unused exports.
     - Step 3 — File-read fallback: only for files the graph can't analyze; pull short hunks via `Read` with offset/limit, never whole files.
     - Step 4 — Findings classification: **reuse miss** / **dead code** / **comment hygiene** (over-commented, stale TODOs, redundant docstrings) / **shape/naming inconsistency**.
     - Step 5 — Write `<feature-folder>/simplify-report-NN.md` (zero-padded monotonic; pick `NN` as `(max existing) + 1`, default `01`). If no feature folder, write to `./simplify-report-NN.md`.
     - Step 6 — Each finding block ends with the line `<!-- pm-disposition: -->` (empty by default). PM fills with `apply` / `defer` / `dismiss`. The skill never auto-edits source.
     - Append the shared Tone-discipline block.
- **Deps:** D1 (shared graph-first paradigm).
- **Pre-flight env check:** code-review-graph MCP responds; `git diff` runnable.
- **may-invalidate:** `docs/strategic-implementation/documentation-registry.md` (new skill + new artifact `simplify-report-NN.md` per feature folder).
- **Visual contract:** n/a.
- **Consumer audit:** n/a.

### D4 — Auto-invocation of `simplify` (mid-execution + post-execution final pass)
- **Integration-risk class:** `d`.
- **User-acceptance steps (from brief):**
  1. Multi-deliverable run (≥4 deliverables): after 3 commits, `executing-plans` invokes `simplify` automatically; report appears in feature folder.
  2. On a long deliverable adding ≥400 changed lines, simplify also fires after that single deliverable.
  3. On a 2-deliverable run, simplify does NOT fire mid-execution — runs once at the end via `post-execution`.
  4. Threshold knobs (`every_n_deliverables`, `loc_threshold`) are visible — for v2, knobs live in the `simplify` skill prompt as named constants; v3 may surface them in plan front-matter.
  5. PM is shown each report and chooses `apply` / `defer` / `dismiss` per finding (no auto-apply).
- **Validation method:** `cli` — read the patched skill prompts and confirm the trigger logic and PM-disposition rule are present. End-to-end on next real ≥4-deliverable run (post-hoc).
- **Files:**
  - `plugins/strategic-implementation/skills/executing-plans/SKILL.md`
  - `plugins/strategic-implementation/skills/post-execution/SKILL.md`
- **Steps:**
  1. In `executing-plans/SKILL.md`, after each deliverable's atomic commit:
     - **Counters via git-log derivation (no new state):**
       - `deliverables_since_simplify` = `git log --oneline <last-simplify-report-NN.md mtime>..HEAD -- <feature-folder> | wc -l`
       - `loc_since_simplify` = `git log -p <last-simplify-report-NN.md mtime>..HEAD | grep -E "^[+-]" | grep -vE "^[+-]{3}" | wc -l`
       - If no prior simplify-report exists in feature folder, count from feature-folder creation (`git log --diff-filter=A -- <feature-folder> | head -1`).
     - If `deliverables_since_simplify >= 3` OR `loc_since_simplify >= 400`, invoke `strategic-implementation:simplify`. Counters reset implicitly when the new `simplify-report-NN.md` lands.
     - Skip if total plan deliverables ≤ 3 (final pass only).
  2. In `post-execution/SKILL.md` regression-check mode, add a mandatory final `simplify` invocation before PASS verdict.
  3. PM-disposition contract: PM edits `simplify-report-NN.md` in place, filling each finding's `<!-- pm-disposition: -->` line with `apply` / `defer` / `dismiss`. Both `executing-plans` and `post-execution` block on this PM action only when autonomy is `supervised`; in `auto`, proceed and surface unfilled dispositions in the deviation log.
  4. Hardcoded defaults at top of `simplify/SKILL.md`: `# defaults: every_n_deliverables=3, loc_threshold=400`.
  5. Append the shared Tone-discipline block to both modified skills.
- **Deps:** D3 (skill must exist).
- **Pre-flight env check:** D3 landed; `git log` available.
- **may-invalidate:** none.
- **Visual contract:** n/a.
- **Consumer audit:** n/a.

### D5 — `token-report.md` deterministic telemetry script
- **Integration-risk class:** `b` — depends on harness session JSONL transcript format (undocumented, real-I/O integration risk).
- **User-acceptance steps (from brief):**
  1. After a multi-deliverable run completes, open the feature folder and find `token-report.md`.
  2. Five sections (was six in v1; baseline comparison dropped): tool-call mix, graph-vs-read ratio, tool-output volume, Bash savings via rtk, simplify dispositions.
  3. Source data: `~/.claude/projects/<encoded-cwd>/<session-uuid>.jsonl` + `rtk gain --format json -p -H`. On format failure or rtk absence, write `unavailable`, never block.
  4. Produced by deterministic script — no LLM step, zero token cost.
- **Validation method:** `integration-test` — run the script against the current session's JSONL and the actual `rtk` binary; assert produced `token-report.md` has the five sections, that the rtk section reads either real data OR `unavailable`, and that exit code is 0 even when sub-sections fail.
- **Files:**
  - `plugins/strategic-implementation/scripts/token-report.sh` (NEW; bash + jq)
  - `plugins/strategic-implementation/skills/post-execution/SKILL.md` (invoke script at end of regression-check)
- **Steps:**
  1. Create `plugins/strategic-implementation/scripts/`.
  2. Write `token-report.sh`:
     - Args: `<feature-folder>` (required), `<session-start-iso>` (optional; default = first event timestamp in latest matching transcript).
     - Resolve project transcript dir: `~/.claude/projects/$(pwd | sed 's|/|-|g; s|^|-|')`.
     - **Pre-flight:** project-specific dir exists AND contains `*.jsonl`. If not, transcript-derived sections all `unavailable`; rtk section may still produce.
     - Pick newest matching `*.jsonl`.
     - jq aggregation:
       - Tool-call counts by `tool_name`.
       - Graph-tool calls = any `tool_name` matching `mcp__code-review-graph__*` or starting with `query_graph`/`semantic_search_nodes`/`get_architecture_overview`/`get_impact_radius`/`detect_changes`/`find_large_functions`/`refactor_tool`. File reads = `Read`.
       - Tool-output bytes total + per-category (Bash, file reads, MCP, WebFetch).
     - rtk: `command -v rtk && rtk --version 2>&1 | grep -qi "rust token killer"` → run `rtk gain -p -H -f json` and aggregate over session window. Else `unavailable`.
     - Simplify dispositions: glob `<feature-folder>/simplify-report-*.md`; count findings; parse `<!-- pm-disposition: ... -->` lines.
     - Write `<feature-folder>/token-report.md` with five sections + header `<!-- transcript-format: v1 (2026-05) -->`.
     - Exit 0 even on partial failure; print `unavailable` per section as needed.
  3. In `post-execution/SKILL.md` regression-check mode, after the final `simplify` pass: invoke `bash plugins/strategic-implementation/scripts/token-report.sh <feature-folder>`. Skill verifies the file landed; never reads or interprets.
  4. `chmod +x` on the script; commit tracked-as-executable.
- **Deps:** D4 (simplify dispositions are an input section).
- **Pre-flight env check:** `command -v jq`; project-specific transcript dir exists with at least one `.jsonl`.
- **may-invalidate:** `docs/strategic-implementation/documentation-registry.md` (new artifacts: `token-report.md` per feature folder, `scripts/` directory).
- **Visual contract:** n/a.
- **Consumer audit:** n/a.

---

## Shared blocks

### Tone-discipline block (appended to clarify, execution-plan, executing-plans, post-execution, simplify SKILL.md)

```markdown
## Tone discipline
Terse. Substance exact. Drop articles, filler ("just", "really", "basically"), pleasantries, hedging. Fragments OK if unambiguous. One sentence per update is enough.

**Carve-outs (do NOT compress):** code blocks, tool output, BLOCK/FLAG callouts, irreversible-action warnings, PM-facing approval prompts.
```

---

## Parallel groups & order

```
Group 1 (parallel; no deps): D1, D2
Group 2 (after Group 1):     D3 (uses D1's graph-first paradigm)
Group 3 (after D3):          D4
Group 4 (after D4):          D5
```

Sequential within `executing-plans`: D1 → D2 → D3 → D4 → D5.

## Reused existing patterns

- **Atomic-commit pattern** in `executing-plans` — D2 piggybacks; no new commit machinery.
- **Skill prompt-as-config pattern** — D1, D2, D4 modify skill text; no separate config files.
- **`agents/simplify.md` plan-time reviewer** — different surface (plan vs code); D3's SKILL.md acknowledges in attribution.
- **Feature-folder convention** — `checkpoint.md`, `simplify-report-NN.md`, `token-report.md` all live there.
- **Documentation registry** — D2, D3, D5 add one-row entries each.
- **Git log as event log** — D4 derives counters from `git log` instead of inventing a counter file.

## Risks & contingencies

- **Graph stale during D1's first real run.** Pre-flight `list_graph_stats_tool`; FLAG and continue with reads if stale. D5 surfaces this in the graph-vs-read ratio.
- **Checkpoint drift from validation-log.** Same atomic commit; checkpoint is a strict projection. Explicit rule in skill prompt.
- **Terseness over-applied to safety callouts.** Carve-out list explicit in shared block.
- **Simplify false-positives mid-run.** Report-only; PM gates each finding via the disposition contract.
- **Transcript JSONL format drift.** D5 writes `unavailable` and continues. Format-version pin in header surfaces drift.
- **rtk name collision.** D5 verifies version-string match.
- **Counter derivation false-zeros.** If `git log` finds no `simplify-report-*.md` in a fresh feature folder, the counter starts from feature-folder creation — correct. If a deliverable is committed without touching the feature folder, the counter under-counts; mitigation: rule in skill prompt that every deliverable's atomic commit must touch the feature folder (it already does, via `validation-log.md` and now `checkpoint.md`).
- **Auto-trigger loops.** `simplify` never auto-edits; reports only. No loop possible.
- **Follow-ups out of v1 (deferred deliberately):** baseline comparison in token-report (re-add when 2nd comparable run exists); D1 step 4 `detect_changes` in post-execution regression-check (revisit if regression-check value observed); plan-front-matter knob parser for D4 thresholds (revisit if defaults prove wrong).

## Out of scope for this plan

- Installing the context-mode plugin / its MCP server.
- Sandboxed-execution analog (`ctx_execute`).
- SQLite/FTS5 session store.
- Telemetry dashboard / web UI.
- Hook-level auto-routing.
- Live (mid-run) token counters.
- Auto-applying `simplify` findings.
- Plan front-matter knob parser (deferred to v3 of this work).
- `detect_changes` in post-execution (deferred).
- Baseline-comparison section in `token-report.md` (deferred until 2nd comparable run exists).

---

## Final steps on approval
1. Save execution plan → `docs/strategic-implementation/2026-05-07-context-mode-and-simplify/execution-plan.md`
2. Exit plan mode
3. Invoke `strategic-implementation:executing-plans`
   - Execution plan path: `docs/strategic-implementation/2026-05-07-context-mode-and-simplify/execution-plan.md`
   - Feature folder path: `docs/strategic-implementation/2026-05-07-context-mode-and-simplify/`
   - Autonomy level: auto
