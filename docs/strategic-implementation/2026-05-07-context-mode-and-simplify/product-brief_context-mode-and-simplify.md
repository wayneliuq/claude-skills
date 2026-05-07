# Product Brief: Context-mode adoption + /simplify skill
_Slug: context-mode-and-simplify · Date: 2026-05-07 · Autonomy: auto_

## 1. Working backwards (≤5 sentences, release-note voice)
> Running `/strategic-implementation` on a multi-deliverable feature now feels lighter on context. Drafting stages cite concrete repo symbols (functions, files, callers) pulled from the code graph instead of re-reading whole files. Long-running executions emit a compact "checkpoint" at deliverable boundaries so a fresh session can pick up cleanly even after compaction. Mid-execution simplify passes catch reuse, dead-code, and over-commenting before the diff balloons. The chain's own output is terser by default — substance preserved, filler dropped — so token spend on a typical multi-deliverable run is meaningfully lower without anything visibly missing.

## 2. What the user does / sees

### D1 — Graph-first reading is wired into `clarify` and `execution-plan`
**How a user verifies:**
1. Run `/strategic-implementation` on any feature touching existing code.
2. Watch the `execution-plan` drafting messages — they cite results from `semantic_search_nodes`, `get_architecture_overview`, `query_graph` (callers/callees/tests-for), or `get_impact_radius` instead of full-file `Read` calls.
3. The plan text references concrete symbols (`function foo at path/file.py:42`, "callers: `bar`, `baz`") rather than paraphrased file content.
4. Confirm at least one `Read` was avoided in favor of a graph query for a file the plan needed to ground a deliverable in.

### D2 — Deliverable checkpoint file persists state across compaction
**How a user verifies:**
1. During a multi-deliverable execution, observe `executing-plans` writing/updating a single `checkpoint.md` (alongside `validation-log.md`) at each deliverable's commit.
2. Open `checkpoint.md` mid-run — see four short sections: **Done**, **In progress**, **Open decisions**, **Unresolved deviations** — each one line per entry, no prose.
3. Force a context compaction (or open a fresh Claude Code session) and resume — the next deliverable picks up using `checkpoint.md` as the rehydration source, not by re-reading the plan from scratch.
4. On final deliverable completion, `checkpoint.md` shows a terminal "complete" marker and is left in the feature folder as a record.

### D3 — Terse-output discipline rule in the skill chain
**How a user verifies:**
1. Run `/strategic-implementation` on a small feature; compare drafting/execution chatter vs. an older run.
2. The chain's user-facing messages are shorter — no pleasantries, no recap of what was just shown, no hedging — but every actionable item (path, decision, BLOCK/FLAG, next step) is still there.
3. Code, tool output, and security/irreversible-action callouts are unaffected (intentional carve-outs from the terseness rule).

### D4 — `/simplify` skill exists in this repo with attribution
**How a user verifies:**
1. List skills in this plugin — `simplify` appears under `plugins/strategic-implementation/skills/`.
2. Run `/strategic-implementation:simplify` directly on any committed branch — it produces a short, structured report: **reuse misses**, **dead code candidates**, **comment hygiene**, **shape/naming inconsistencies**, with file:line citations.
3. The skill's SKILL.md credits the upstream `anthropic-skills:simplify` it was adapted from.
4. The skill uses graph tools (`semantic_search_nodes` for reuse detection, `find_large_functions_tool`, `refactor_tool` for dead-code) and only falls back to file reads when the graph can't answer.

### D6 — Token-report at run end
**How a user verifies:**
1. After a multi-deliverable run completes, open the feature folder and find `token-report.md`.
2. The report has four sections, all auto-populated:
   - **Tool-call mix** — counts per tool name (Read, Edit, Bash, WebFetch, code-review-graph queries, etc.)
   - **Graph-vs-read ratio** — `<graph-tool calls> : <file-read calls of pre-existing source>` with a one-word verdict (`graph-dominant` / `mixed` / `read-dominant`)
   - **Tool-output volume** — total bytes returned by tool calls during the run, broken down by category (Bash output, file reads, MCP tool output, WebFetch)
   - **Bash savings (rtk)** — pulled from `rtk gain` (terminal-command token savings tracked by the rtk proxy): total saved this run, top contributing commands
   - **Simplify** — number of reports produced, findings count by category, PM disposition (`apply` / `defer` / `dismiss`) per finding
   - **Baseline comparison** — empty stub on first run, populated by hand once a second comparable run exists; later runs auto-fill against the prior comparable run if one is on disk
3. Source data is the harness's own session transcript (`~/.claude/projects/<slug>/<session>.jsonl`) plus `rtk gain --json` output for the time window of the run; if the transcript format isn't readable or `rtk` isn't installed, the report still writes with `unavailable` placeholders for those sections and the run is not blocked.
4. The report is produced by a deterministic script (jq/bash) — **no LLM interpretation, no model tokens spent generating the report**. The skill's only role is to invoke the script and verify the file landed. This makes the telemetry itself zero-cost and reproducible across runs.

### D5 — Auto-invocation of `/simplify` during and after execution
**How a user verifies:**
1. Start a multi-deliverable run (≥4 deliverables). After 3 commits, observe `executing-plans` invoking `simplify` automatically; its report appears in the feature folder as `simplify-report-<n>.md`.
2. On a long deliverable that adds ≥400 changed lines in one shot, simplify also fires after that single deliverable.
3. On a 2-deliverable run, simplify does **not** fire mid-execution — it runs once at the end via `post-execution`.
4. Threshold knobs (`every_n_deliverables`, `loc_threshold`) are visible in the execution plan's front-matter and override the defaults when set.
5. PM is shown each report and chooses `apply / defer / dismiss` per finding (auto-apply is opt-in only).

## 3. Success signal
On the next real multi-deliverable run, a side-by-side comparison against the prior comparable run shows: graph-tool calls in the drafting transcript outnumber whole-file reads of pre-existing source; at least one mid-execution simplify report is produced; total tokens consumed by the run drops measurably (target: ≥20% on jobs of ≥4 deliverables, no regression on smaller jobs).

## 4. Boundaries
**In scope:**
- Cherry-picked context-mode paradigms: structural-answer-first reading (via code-review-graph), checkpoint-on-compact pattern (lightweight, file-based), terse-output discipline.
- New `/simplify` skill packaged in `plugins/strategic-implementation/skills/simplify/` with attribution to upstream.
- Auto-invocation rule + threshold knobs.
- End-of-run `token-report.md` driven by transcript scrape + `rtk gain` (D6).
- Edits to `clarify`, `execution-plan`, `executing-plans`, `post-execution` skill prompts only as needed to wire the above.

**Out of scope:**
- Installing the context-mode plugin/MCP itself.
- A SQLite/FTS5 session store (the checkpoint is a single markdown file, not a database).
- Sandboxed-execution `ctx_execute` analog (we already have Bash + the graph; reuse those).
- `/simplify` auto-applying any change — it reports only; PM decides.
- Live (mid-run) token counters or hook-based instrumentation; telemetry is post-run only.
- A telemetry dashboard or web UI; `token-report.md` is the only artifact.

**Anti-goals (philosophy-level — we deliberately will not):**
- Build a parallel context-management layer when the code-review-graph MCP already provides the same structural-answer surface.
- Over-engineer the checkpoint into a structured DB; if a one-page markdown isn't enough, the design is wrong.
- Enforce terseness on code or on safety-critical callouts; substance always beats style.
- Couple `/simplify` so tightly to the chain that it can't run standalone on any branch.

## 5. Decisions
| Decision | Choice | Status |
|---|---|---|
| Adoption mode for context-mode | Cherry-pick paradigms, do not install upstream plugin | `[HARD DECISION]` |
| Structural-answer source | code-review-graph MCP (already installed, auto-updated by hooks) | `[HARD DECISION]` |
| Checkpoint storage | Single markdown file per feature folder; no DB | `[HARD DECISION]` |
| Simplify trigger rule | every 3 deliverables OR ≥400 LOC since last pass; final pass in post-execution; ≤3-deliverable plans = end-only | settled |
| Threshold knobs location | Plan front-matter (`every_n_deliverables`, `loc_threshold`) | settled |
| Simplify report disposition | Report-only by default; PM applies/defers/dismisses per finding | `[HARD DECISION]` |
| Attribution | `/simplify` SKILL.md credits `anthropic-skills:simplify` upstream | settled |
| Terseness scope | Skill chain user-facing messages only; code, tool output, safety callouts exempt | settled |
| Telemetry approach | Post-run transcript scrape + `rtk gain` for terminal calls; no live counters, no DB | `[HARD DECISION]` |
| Telemetry generation | Deterministic script only (jq/bash); no LLM step; zero token cost for the report itself | `[HARD DECISION]` |

### Tradeoff — checkpoint storage (HARD DECISION)
| Option | Pro | Con |
|---|---|---|
| Single markdown file (chosen) | Greppable, diff-able, survives compaction trivially, zero infra | Must keep small; not query-able |
| SQLite + FTS5 (context-mode style) | Rich retrieval, scales to many sessions | Major infra, lifecycle bugs, overkill for our deliverable cadence |

### Tradeoff — simplify report disposition (HARD DECISION)
| Option | Pro | Con |
|---|---|---|
| Report-only, PM decides (chosen) | Safe; no surprise rewrites mid-execution | PM has to act on each finding |
| Auto-apply low-risk findings | Less PM toil | Risk of unexpected diffs masking deviations; trust cost too high |

## 6. Risks & unknowns
- **Graph staleness.** Code-review-graph relies on hooks. If hooks fail silently the structural answers go stale and ground-truth drifts. Mitigation: `execution-plan` should call `list_graph_stats_tool` once at start and FLAG if the graph is older than the working tree.
- **Simplify false-positives mid-execution.** Reuse-detection may suggest collapsing functions that are intentionally separate. Mitigation: report-only, PM-gated.
- **Checkpoint drift from validation-log.** Two files tracking related state risks divergence. Mitigation: `executing-plans` writes both in the same atomic commit; checkpoint is a strict subset projection — no separate edit path.
- **Terseness over-applied.** Reviewers, PM-facing prompts, BLOCK/FLAG messages must remain readable. Mitigation: explicit carve-out list in the discipline rule.
- **Unknown:** the actual token delta. We're targeting ≥20% on long runs but can't confirm without one real comparable A/B; the success-signal call-out captures this.
- **Transcript format drift.** D6 reads `~/.claude/projects/<slug>/<session>.jsonl`, which is undocumented and may shift between Claude Code versions. Mitigation: scrape failure writes `unavailable` and never blocks; pin the format version in `token-report.md` so a future shift is visible.
- **`rtk` not installed.** D6's Bash-savings section depends on `rtk gain --json`. If `rtk` is absent, that section reads `unavailable`; rest of the report still produces.

## 7. References & revision log
**Document references:**
- Architecture: `docs/strategic-implementation/project-learnings.md` (de-facto working notes); `docs/strategic-implementation/documentation-registry.md` (registry index)
- UX/PMF: n/a — no user-facing UI
- Security policy: n/a — no auth/secrets/user data
- Schema/ERD: n/a — no data storage
- Upstream inspirations: `mksglu/context-mode` (paradigms only, not installed); `anthropic-skills:simplify` (skill template)

**Revision log:**
- v0.1 · 2026-05-07 · initial draft
- v0.2 · 2026-05-07 · added D6 (token-report.md driven by transcript scrape + `rtk gain`); added telemetry HARD DECISION; updated boundaries and risks
- v0.3 · 2026-05-07 · pinned D6 as deterministic-script-only (no LLM step, zero token cost for the report)
