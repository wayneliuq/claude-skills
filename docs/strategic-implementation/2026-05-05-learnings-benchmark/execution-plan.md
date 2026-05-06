# Execution Plan: Learnings Benchmark
_Implements: product-brief_learnings-benchmark.md · Date: 2026-05-05_

## Context

Add a new sibling skill `learnings-benchmark` to the `strategic-implementation` plugin. The skill runs controlled A/B (optional A/B/C) benchmarks comparing agents with vs without the project-learnings bundle on a pinned model, captures external timing + token-bucket metrics, has a blind judge agent grade outputs, and emits a per-learning-group keep / retire / modify report. The skill is prompt-only (one `SKILL.md`) with one seeded task in the `benchmarks/` corpus to bootstrap, and synthesis fallback covers the rest until the smoke run reveals which themes discriminate. Outcome: `/strategic-implementation:learnings-benchmark` becomes callable, refuses to run on `main`, and produces an evidence-backed recommendation per learning.

## Library lifecycle audit

### Agent / Task tool with `isolation: "worktree"`
- **State that persists:** Each Agent invocation with `isolation:"worktree"` materializes a temporary git worktree branched off the current branch. The worktree path + branch are returned only if the agent **made commits**; if the agent produced no commits, the worktree is auto-cleaned up and there is no path to scrape transcripts from. Agent transcripts also live under `~/.claude/projects/<encoded-cwd>/...` per session.
- **Quirks / gotchas:** (a) Auto-cleanup on no-changes silently destroys evidence — benchmark agents MUST commit something so the worktree survives. (b) Model parameter is per-call; missing it inherits the parent's model — silently breaks the "model-specific" guarantee. (c) Token totals are not part of the Agent tool's return value in standard form; must be cross-checked between an external transcript parse AND a worker-written `_run-stats.json` (mandatory, not fallback). (d) The `~/.claude/projects/<encoded-cwd>/<session>.jsonl` path is empirical, not a documented contract — the redundant worker-stats commit guards against silent format changes. (e) Sub-agents spawned by the worker land in a different session.jsonl under a separate session id; their token cost is invisible to the parent transcript. The worker's system prompt MUST forbid spawning sub-agents.
- **Doc consulted:** Agent tool description in this session's tool surface (top of conversation); confirmed `isolation: "worktree"`, `model`, `run_in_background` parameters; project-learnings L-005 (plugin-cache drift risk for skill-prose changes). No canonical published doc for the transcript-file path format — empirical only.

### Per-agent `model` parameter
- **State that persists:** none across calls; per-invocation only. But the absence of an explicit value means the model defaults to inheritance, which can drift run-to-run.
- **Quirks / gotchas:** Skill must hard-fail at Phase 0 if no model ID is supplied. No defaulting / no inference.
- **Doc consulted:** Agent tool description (top of conversation).

### Git
- **State that persists:** Worktrees are real branches off the current HEAD. Uncommitted changes in the working tree are NOT carried into worktrees, but the parent branch state is. Branch protection is honored only by humans / hooks — git itself will allow commits to `main`.
- **Quirks / gotchas:** (a) The skill must verify clean working tree before dispatching, otherwise comparing groups is not apples-to-apples (parent commit varies). (b) Branch-name collisions: re-running the skill on the same date needs an `<id>` suffix.
- **Doc consulted:** standard git semantics; no in-repo doc.

### Anthropic prompt-cache (API-side)
- **State that persists:** Per-account prompt cache keyed on prefix tokens; persists ~5 min within a project. Whichever group's worker dispatches first warms the cache (system prompt + tool surface); subsequent groups read cached prefixes for free, biasing `cache_read_input_tokens` and wall-clock asymmetrically.
- **Quirks / gotchas:** Even with parallel dispatch, the first few seconds are asymmetric. Two complementary mitigations applied: (a) inject a per-trial random nonce as the first line of the worker system prompt so prefixes are unique across trials/groups (cache reads near zero); (b) Phase 5 decision logic compares on `billed_total − cache_read_contribution` so any residual cache asymmetry doesn't sway the recommendation. Report header surfaces both raw and cache-discounted totals.
- **Doc consulted:** Anthropic prompt-cache behavior (general knowledge, no in-repo reference).

## Deliverables (DAG)

### D1 — `learnings-benchmark` skill file + bootstrap corpus task

- **Integration-risk class:** `a` — depends on Agent tool runtime + git worktree lifecycle + transcript-file format.
- **Validation:** `spec-conformance grep` (no behavioral validation in this deliverable; behavioral correctness is carried by D4). Grep assertions against the working-tree files: confirm frontmatter (`name: learnings-benchmark`, `description:` line ≥80 chars), all five phase headings present, each HARD DECISION clause appears (branch guard / byte-identical prompts / pinned model / blind judge / N≥3 / four token buckets / external wall-clock / explicit invocation), AND the brief-D1 `--dry-run` flag is documented in Step 1 inputs, AND brief-D2 branch refusal-on-main is documented in Step 0. The bootstrap corpus task file exists with non-empty `task.md` and `success-criteria.md`.
- **Files:**
  - `plugins/strategic-implementation/skills/learnings-benchmark/SKILL.md` (new)
  - `plugins/strategic-implementation/skills/learnings-benchmark/benchmarks/README.md` (new — short; describes corpus structure)
  - `plugins/strategic-implementation/skills/learnings-benchmark/benchmarks/tests/l-005-probe/task.md` (new — single seed task probing the L-005 plugin-cache validation theme)
  - `plugins/strategic-implementation/skills/learnings-benchmark/benchmarks/tests/l-005-probe/success-criteria.md` (new — blind rubric items)
- **Steps:**
  1. Create folder `plugins/strategic-implementation/skills/learnings-benchmark/`.
  2. Write `SKILL.md` with frontmatter `name: learnings-benchmark` and a one-line description matching repo style. Tone matches sibling skills (`clarify`, `executing-plans`): direct, no enthusiasm, `## Step N` / `## Phase N` sections separated by `---`. Target ≤300 lines (L-003 awareness; sections kept terse).
  3. Sections (in order):
     - **Header + invocation note** — "explicit invocation only; never auto-triggered."
     - **Step 0 — Branch + working-tree pre-flight.** Detect branch via `git branch --show-current`. Refuse on `main` / `master` / any branch matching `release/*` or `prod/*` with a one-line remediation: `git checkout -b benchmark/<YYYY-MM-DD>-<slug>`. Verify `git status --porcelain` is empty. (Honors brief D2.)
     - **Step 1 — Inputs.** Required: target model ID (literal, e.g. `claude-opus-4-7`); the skill hard-fails if missing — no defaulting, no inference. Optional: `--dry-run` flag (runs Phases 1-2 only and exits before dispatch — honors brief D1); third-group definition (modified/minimized learnings set); trial count override (default 3); `max_concurrent_dispatches` (default 4, hard cap 8); task corpus subset filter.
     - **Phase 1 — Gather learnings.** Read `docs/strategic-implementation/project-learnings.md` and `plugins/strategic-implementation/agents/*.md`. Propose semantic groupings (≥1 group per `#tag` and per agent role). User edits/approves; persist to `<feature-folder>/run-<id>/learnings.json` (keys: `group_id`, `title`, `source_paths`, `learning_text`, `selected: bool`).
     - **Phase 2 — Compile tasks + run plan.** Corpus-first: `plugins/strategic-implementation/skills/learnings-benchmark/benchmarks/<group_id>/<task-slug>/task.md` (D1 ships one bootstrap task under `tests/l-005-probe/`; remaining themes use synthesis fallback). Synthesis fallback: generate a task per selected group whose deltas would be observable (a small refactor, bug fix, or design choice that the learning's WHEN/DO logic would steer). Emit a plan summary table: tasks × groups × trials = total dispatches, max_concurrent, target model, formula version. User approves or aborts. If `--dry-run`, exit here.
     - **Phase 3 — Dispatch.** For each (task × group × trial), assemble a byte-identical prompt; the system-augmentation alone differs (test = learnings injected verbatim; control = none; modified = user-defined subset). Prepend a per-trial random nonce as the first line of every worker system prompt to neutralize API prompt-cache prefix-sharing across groups. Dispatch via `Agent(subagent_type:"general-purpose", isolation:"worktree", model:<pinned>, run_in_background:true)`. Pace dispatches in waves of `max_concurrent_dispatches`; do NOT fan out the full matrix at once. Record `dispatch_ts` per call. **Worker contract** (literal in the dispatch prompt):
       - The worker MUST commit `trial-<n>/output/` (the work) AND `trial-<n>/_run-stats.json` (the worker's self-recorded `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, and start/end ISO timestamps as a sanity-check against external capture).
       - The worker MUST NOT spawn sub-agents (Task / Agent calls). All work happens in-process. This is non-negotiable — sub-agent token costs are invisible to the parent transcript and silently undercount.
       - If the worker fails to commit, the trial is `lost`.
     - **Phase 4 — Capture metrics + blind score.**
       - **External capture (primary):** record `completion_ts` per call when the Agent return arrives; wall-clock = `completion_ts − dispatch_ts`. Locate the agent's transcript file at `~/.claude/projects/<encoded-worktree-path>/<session>.jsonl`; parse cumulative `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`. **Cross-check** against `_run-stats.json` from the worktree commit. If transcript-located path was taken AND cross-check is within 10%, mark trial `clean`. If transcript not found, fall back to `_run-stats.json` and mark trial `transcript-unavailable`. If both missing, mark trial `lost`.
       - **Blind judge:** dispatch a separate `Agent(subagent_type:"general-purpose", model:<pinned>)` with: the rubric, the task description, and the trial's diff/output ONLY. No group label, no learnings text, no trial number. Rubric: bug count, severity 1–3, task-completion (binary), code-quality 1–5. Judge returns JSON. Each judge call is a fresh agent (no batching).
     - **Step 4b — Auto-bump trials.** After Phase 4, if any (group × task) primary-metric stddev > 30% of mean, re-dispatch 2 additional trials for that cell. Use the SAME billed-total formula version as the original dispatch — do NOT mix formula versions within a run. If the formula version has changed since dispatch, abort the bump and report the original cell as low-confidence.
       - **Strict completion gate:** if any cell ends with N<3 successful (`clean` or `transcript-unavailable`) trials after retries (max 2 retries per lost trial), ABORT the run before Phase 5. Surface the asymmetry. Track refusal/lost-rate by group; if one group's failure rate exceeds another's by >20%, mark that group `unbenchmarkable` and refuse to score it.
     - **Phase 5 — Report + commit.**
       - Write `<feature-folder>/run-<id>/report.md` with: run header (model ID, branch, date, billed-total formula + version pin, rubric version, trial count, max_concurrent, run start/end), per-(group × task) scorecard table (mean ± stddev for bugs / severity-weighted bugs / billed_total / billed_total minus cache_read contribution / wall-clock / quality), per-bucket token totals (input / output / cache_read / cache_write) shown separately, recommendation per learning group (`keep` / `retire` / `modify` with rationale referencing the deltas), and a `Low-confidence runs` section flagging stddev > 30% of mean and any `transcript-unavailable` trials.
       - Decision logic (uses cache-discounted billed total to neutralize residual cache asymmetry): `keep` iff Δquality > stddev AND quality justifies (cache-discounted) token cost; `retire` iff Δquality ≤ stddev AND tokens-or-time worse on cache-discounted basis; `modify` otherwise (mixed signals → propose narrower scope).
       - Commit on the benchmarking branch only. No merge offered.
     - **Anti-bias rules block.** Explicit list at the bottom: no group labels in worker prompts; no "you are being benchmarked" text; no self-reported metrics drive decisions (worker's `_run-stats.json` is a cross-check only); identical seed/temperature; identical task wording byte-for-byte; per-trial random nonce on system prompt; cache-discounted comparison.
     - **Failure modes & remediation.** Compact: (a) worktree auto-cleaned → `lost`, retry up to 2× per trial; if cell N<3 after retries, ABORT before Phase 5; (b) transcript not findable → fall back to `_run-stats.json`, mark trial `transcript-unavailable`, flag in report; (c) judge malformed JSON → re-dispatch judge once; if fails, mark cell `unscored`; (d) safety-refusal asymmetry across groups → group flagged `unbenchmarkable`; (e) pricing-formula version change mid-run → abort bumped trials, mark cell low-confidence.
  4. Write `benchmarks/README.md` (≤30 lines): explains corpus structure (`<theme>/<task-slug>/{task.md, success-criteria.md}`), naming, how Phase 2 selects tasks, and that themes without a corpus task fall through to synthesis.
  5. Write the bootstrap corpus task `benchmarks/tests/l-005-probe/task.md` and `success-criteria.md`. The task probes L-005: present a deliverable plan whose validation depends on a plugin-cached agent and ask the worker to either (a) declare correct validation method, or (b) defend the choice. The right answer per L-005 is `post-hoc` or grep against working-tree, not in-session `cli` invocation. `success-criteria.md` lists blind rubric items (no learning name leaked).
- **Deps:** none
- **Pre-flight env check:** clean working tree on a non-main branch; Agent tool surface includes `isolation:"worktree"` and `model` parameters; user has provided a model ID (only relevant at execution-time of the skill itself, not at D1 build-time).
- **may-invalidate:** none — `documentation-registry.md` currently has only a strategic-implementation-internal entry; this skill does not change that doc's covered surface.
- **Visual contract:** n/a
- **Consumer audit:** n/a — additive, no shape changes to existing skills, agents, manifest, or shared docs.

### D2 — Repo README discoverability

- **Integration-risk class:** `d`
- **Validation:** `cli` — grep both READMEs for `learnings-benchmark` (≥1 mention each in the Skills table); confirm the "Skills (N)" header in both files was incremented from whatever value it currently has (dynamic — read first, then increment by 1; do not hardcode the new number).
- **Files:**
  - `README.md` (modify — Skills table row + dynamic count update)
  - `plugins/strategic-implementation/README.md` (modify — same)
- **Steps:**
  1. Grep current Skills count in both READMEs (e.g. `Skills (9)` or `Skills (10)`); record it. Increment by 1.
  2. Add a row to the Skills table in both READMEs: `| learnings-benchmark | Explicit-invocation A/B benchmark of project-learnings vs control on a pinned model. Branch-only; report committed to benchmarking branch. |`
  3. Update the "Skills (N) and agents (7)" header text in both READMEs with the incremented N.
  4. Do NOT bump version (additive skill, brief does not require it). Do NOT touch `plugin.json` or `package.json`. Do NOT add to the orchestrator (`strategic-implementation/SKILL.md`) workflow — this skill is explicit-invocation only and outside the brief→plan→execute arc.
- **Deps:** D1
- **Pre-flight env check:** D1 file present.
- **may-invalidate:** none in registry.
- **Visual contract:** n/a
- **Consumer audit:** n/a — README metadata only; no consumers parse the skill list programmatically (skills auto-discovered from folder structure).

### D3 — Smoke-run end-to-end validation (user-side, post-hoc)

- **Integration-risk class:** `a`
- **Validation:** `post-hoc` — manual smoke run by the user. Reasoning: D1 is itself a plugin file; per project-learnings L-005, working-tree edits to plugin skills are not visible to in-session agent invocations until the plugin cache is reinstalled. Therefore an automated `cli` invocation of the new skill from this same session would test the cached (absent) version, not the working tree. Validation must be a post-hoc reinstall + manual invocation by the user. Acceptance criteria are explicit and exercise both happy-path and one failure mode.
- **Files:** none modified — verification only.
- **Steps:**
  1. User reinstalls the plugin (or the harness rehydrates the cache).
  2. User creates a benchmarking branch: `git checkout -b benchmark/2026-05-05-smoke`.
  3. User runs `--dry-run` first: invoke `/strategic-implementation:learnings-benchmark` with `--dry-run`. Confirm: skill prints planned run (target model, learning groups, task list, trial count, branch name) and exits without dispatching. (Honors brief D1.)
  4. User runs full smoke from `main` to confirm refusal: confirm pre-flight refuses with the remediation message. (Honors brief D2.)
  5. User runs full smoke on the benchmarking branch with a trivial config: 1 selected learning group (the `tests/l-005-probe` corpus task), 3 trials, target model = current model ID.
  6. User confirms acceptance criteria (each must pass):
     - (a) Pre-flight refused on `main`; accepted on `benchmark/...` branch.
     - (b) `report.md` written under `<feature-folder>/run-<id>/` on the benchmarking branch.
     - (c) `git log main..HEAD --oneline` shows the report commit on the benchmarking branch only; `git log main` is unchanged.
     - (d) **Token bucket completeness**: report.md contains non-zero values for ALL FOUR token buckets (input, output, cache_read, cache_write) for every trial. If any bucket is missing or zero on a worker call, escalate.
     - (e) **Wall-clock completeness**: every trial has a non-zero wall-clock in seconds.
     - (f) **Transcript path resolved**: at least 1 trial in 3 reports `transcript-located` (not the `transcript-unavailable` fallback). If all 3 fall back, the encoded-cwd path resolution is broken and the run is degraded.
     - (g) **Failure-mode exercise** (one induced failure): kill or interrupt one worker before it commits its `trial-<n>/output/`. Confirm the harness marks the trial `lost`, retries up to 2×, and on second-failure either marks it `lost` permanently or aborts the cell per the strict completion gate.
- **Deps:** D1, D2
- **Pre-flight env check:** plugin reinstalled; clean working tree on a benchmarking branch; user has time for a multi-minute smoke run.
- **may-invalidate:** none.
- **Visual contract:** n/a
- **Consumer audit:** n/a

## Parallel groups & order

```
D1 ────► D2 ────► D3
```

D2 depends on D1. D3 depends on both. No parallel groups (each is small enough that ordering is fine; D2 is too small to justify parallelism with D1).

## Reused existing patterns

- **Skill file convention:** `plugins/strategic-implementation/skills/<name>/SKILL.md` with `name:` + `description:` frontmatter; auto-discovered from folder structure (no manifest entry needed) per `plugins/strategic-implementation/.claude-plugin/plugin.json`.
- **Tone + structure:** mirror `clarify/SKILL.md`, `executing-plans/SKILL.md`, `post-execution/SKILL.md` — `## Step N` / `## Phase N`, `---` separators, direct prose.
- **Branch pre-flight pattern:** `executing-plans/SKILL.md:18` — Step 0 with branch check + warning template. Reuse the wording shape verbatim, escalating from "warning" to "refuse" since this skill is harder-gated than executing-plans.
- **JSON schema convention:** `agents/*.md` token-cap pattern (~1500 tokens, JSON output) — the blind judge call inside Phase 4 follows this.
- **Validation-method honesty (project-learnings L-005):** D3 declared `post-hoc` rather than `cli` precisely because in-session validation of plugin-cache-loaded files is unreliable.

## Risks & contingencies

- **Worktree auto-cleanup on no-commit (carried from brief).** Mitigated by the worker-contract requirement that the agent commit `trial-<n>/output/` AND `_run-stats.json` before exit. If the agent forgets, the trial is `lost` and re-dispatched up to twice; if the cell ends with N<3 after retries, the run aborts before Phase 5 rather than proceeding with incomplete cells.
- **Transcript file location stability.** The encoded-cwd path is empirical, not documented. Defense in depth: every trial requires a worker-written `_run-stats.json` (mandatory, not transcript-miss-only); Phase 4 cross-checks external transcript parse against worker stats and flags any >10% discrepancy.
- **Cache warming bias on parallel dispatch.** Mitigated three ways: (a) per-trial random nonce on every worker system prompt; (b) report shows raw and cache-discounted billed totals separately; (c) decision logic uses the cache-discounted total. Residual asymmetry is bounded.
- **Sub-agent token leak.** Worker contract explicitly forbids spawning sub-agents. If a worker violates this, parent-transcript token totals would silently undercount; cross-check against `_run-stats.json` provides a sanity bound.
- **Concurrency saturation.** `max_concurrent_dispatches` capped at 8, default 4. Wave-based dispatch, not full fan-out. Surfaces in report header so PM can see what was used.
- **Asymmetric refusals across groups.** If safety-refusal rate differs by >20% between groups, the affected group is marked `unbenchmarkable` rather than scored. The asymmetry itself is reportable signal.
- **Pricing-formula version drift mid-run.** Formula version is captured at Phase 3 dispatch start and applied uniformly to all trials in the run, including auto-bumped trials. If the formula has changed before bumped trials run, the bump is aborted and the cell is marked low-confidence rather than mixing formula versions.
- **Plugin-cache drift (L-005).** D3 is `post-hoc` for exactly this reason. Brief D1 (`--dry-run`) and brief D2 (branch refusal) are both observable in the smoke run, so the post-hoc gate is honest.
- **Model-default leakage.** Skill hard-fails at Step 1 if no model ID is supplied. No fallback / no inference from current session.
- **SKILL.md size.** Target ≤300 lines (L-003 awareness). Sections compact; failure-mode prose terse.

## Out of scope for this plan

- Auto-applying recommendations to `project-learnings.md`.
- Cross-model comparison in a single run.
- Dollar-cost estimates against current pricing.
- Continuous / scheduled benchmarking.
- Replacing or modifying the deviation + project-learnings synthesis loop in `post-execution`.
- Adding the new skill to the orchestrator (`strategic-implementation/SKILL.md`) flow.
- Seeding a multi-theme corpus pre-smoke. After the smoke run validates the dispatch + capture path on the bootstrap task, additional corpus tasks can be authored as a follow-up — synthesis fallback covers the gap meanwhile.
- Plugin manifest version bump.

---

## Final steps on approval
1. Save execution plan → `docs/strategic-implementation/2026-05-05-learnings-benchmark/execution-plan.md`
2. Exit plan mode
3. Invoke `strategic-implementation:executing-plans`
   - Execution plan path: `docs/strategic-implementation/2026-05-05-learnings-benchmark/execution-plan.md`
   - Feature folder path: `docs/strategic-implementation/2026-05-05-learnings-benchmark/`
   - Autonomy level: auto
