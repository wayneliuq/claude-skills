---
name: learnings-benchmark
description: Explicit-invocation A/B benchmark of project learnings vs control on a pinned model. Branch-only execution; isolated worktree per trial; blind judge scores outputs; per-learning keep / retire / modify report committed to the benchmarking branch. Run infrequently to decide which learnings still earn their keep as models improve.
---

# learnings-benchmark

Explicit-invocation only. **Never** auto-triggered by hooks, orchestrators, or other skills. The user invokes this skill directly when they want to know whether the project-learnings bundle still earns its keep on a given model.

Output is an evidence-backed keep / retire / modify recommendation per learning group, grounded in measured deltas (bugs, severity, billed tokens, wall-clock, blind quality). The skill does NOT modify `project-learnings.md` — the report is read-only; the user edits manually.

---

## Step 0 — Branch + working-tree pre-flight

Refuses to run on `main`, `master`, `release/*`, or `prod/*`. The benchmarking branch is the record; main never sees benchmark commits. (Honors brief D2.)

1. `git branch --show-current` → if it matches a refused pattern:

   > 🛑 **Refusing to run on `<branch>`.** This skill commits benchmark artifacts and must run on a dedicated branch.
   >
   > Remediation: `git checkout -b benchmark/<YYYY-MM-DD>-<slug>`

   Exit.

2. `git status --porcelain` → if non-empty:

   > 🛑 **Working tree not clean.** Worker worktrees branch off the current commit; uncommitted changes leak across groups asymmetrically.
   >
   > Remediation: commit or stash, then re-invoke.

   Exit.

3. **Resolve the clean base ref.** `BASE_SHA = $(git merge-base HEAD main)`. This is the parent commit before any benchmark commits — every worker and judge worktree is created at this commit so the benchmark machinery, prior runs, and per-run state are absent from the worker's checkout. If `git merge-base` fails (no shared history), abort with: `Refusing to run: cannot resolve clean base off main.`

4. **Ensure the private artifact dir is gitignored.** All ephemeral run state (learnings JSON, dispatched prompts, trial outputs, judge transcripts, in-progress reports) goes under `.benchmark-private/`. If `.benchmark-private/` is not listed in the repo `.gitignore`, append the line and commit the diff as the only tracked change at this stage:

   ```
   git status --porcelain .gitignore
   # if missing entry: append, then:
   git add .gitignore
   git commit -m "learnings-benchmark: ignore .benchmark-private/ runtime dir"
   ```

   This is the **last tracked write before all dispatches finish**. Everything between here and Phase 5 lives under `.benchmark-private/` and is invisible to workers (gitignored paths are not propagated by `git worktree add`).

---

## Step 1 — Inputs

**Required:**
- `model` — literal model ID (e.g. `claude-opus-4-7`). No defaulting, no inference from the current session. If absent, print `Refusing to run: target model ID not provided. Required.` and exit.

**Optional:**
- `--dry-run` — runs Phases 1–2 only and exits before any agent dispatch. Prints the planned run so the user can sanity-check before paying for trials. (Honors brief D1.)
- `third_group` — definition of a modified or minimized learnings set (path or inline subset). If present, the run uses three groups (test / control / modified); otherwise two.
- `trials` — integer; default 3. Auto-bumps to N+2 per cell on stddev > 30% of mean of the primary metric.
- `max_concurrent_dispatches` — integer; default 4; hard cap 8.

---

## Phase 1 — Gather learnings

Read learnings sources:
- `docs/strategic-implementation/project-learnings.md`
- `plugins/strategic-implementation/agents/*.md` (inlined hardening rules in review-agent files)

Propose **semantic groupings**. Default heuristic: ≥1 group per `#tag` in `project-learnings.md` (today: `#scope`, `#security`, `#technical`, `#tests`) plus one group per agent role with inlined rules. A learning may belong to multiple groups; record both.

Present the grouping as a numbered list. The user may `accept`, edit inline (rename / move / drop), or `cancel`.

On accept, persist to `.benchmark-private/<run-id>/learnings.json` (gitignored — workers cannot see it):

```json
{
  "run_id": "<id>",
  "groups": [
    {
      "group_id": "tests-validation-honesty",
      "title": "Validation method honesty (L-005, mocking-at-seam)",
      "source_paths": ["docs/strategic-implementation/project-learnings.md", "plugins/strategic-implementation/agents/tests.md"],
      "learning_text": "<verbatim WHEN/DO blocks concatenated>",
      "selected": true
    }
  ]
}
```

`<run-id>` is a short timestamped slug, e.g. `2026-05-05-1430`. The committed final report lives at `<feature-folder>/run-<run-id>/report.md` where `<feature-folder>` is `docs/strategic-implementation/<YYYY-MM-DD>-learnings-benchmark/` — but that directory is NOT created until Phase 5. Until then, every run artifact stays under `.benchmark-private/<run-id>/`.

---

## Phase 2 — Compile tasks + run plan

For each selected group, pick a task:

1. **Corpus first.** Look in `plugins/strategic-implementation/skills/learnings-benchmark/benchmarks/<group_id-or-theme>/<task-slug>/`. If a `task.md` + `success-criteria.md` pair exists, **read both files into the orchestrator's memory now**. The worker will receive `task.md` content inline through its dispatch prompt — never as a path reference — so it cannot search the worktree for criteria, sibling tasks, or rubrics.
2. **Synthesis fallback.** If no corpus task exists, generate one whose deltas would be observable: a small refactor, bug fix, or design choice that the learning's WHEN/DO logic would steer differently than the control. Prefer tasks where the right answer is itself contested. Synthesized tasks are written only to `.benchmark-private/<run-id>/tasks/<group_id>.md`, never to a tracked path.

Emit a plan summary table:

| field | value |
|---|---|
| target model | `<pinned model>` |
| groups | test, control[, modified] |
| tasks | `<list>` |
| trials per cell | `<N>` |
| max_concurrent | `<N>` |
| billed-total formula version | `v1` (see Phase 5) |
| total dispatches | tasks × groups × trials |

User approves or aborts. **If `--dry-run`: print the summary and exit.**

---

## Phase 3 — Dispatch

Each `(task × group × trial)` runs in its own **sanitized throwaway worktree** so the worker cannot grep its way into the benchmark machinery, prior runs, or the learnings corpus.

### Per-trial worktree setup (orchestrator runs these via Bash before dispatch)

```bash
WORK=.benchmark-private/<run-id>/trial-<n>/worktree
git worktree add --detach "$WORK" "$BASE_SHA"   # BASE_SHA from Step 0.3 — clean parent of benchmark commits
# Strip the benchmark machinery + learnings sources from this worktree only.
# The detached worktree has no upstream; rm here does not affect main or the benchmark branch.
rm -rf \
  "$WORK/plugins/strategic-implementation/skills/learnings-benchmark" \
  "$WORK/plugins/strategic-implementation/agents" \
  "$WORK/docs/strategic-implementation/project-learnings.md" \
  "$WORK"/docs/strategic-implementation/*learnings-benchmark* \
  "$WORK"/.benchmark-private 2>/dev/null || true
```

The worker therefore sees a checkout of the clean parent commit with all benchmark machinery removed. A grep for `benchmark`, `learning`, `trial`, `rubric`, or this skill's name turns up nothing. Gitignored files from the parent worktree (including `.benchmark-private/`) do NOT propagate to a `git worktree add` — that's load-bearing; do not break it.

### Worker prompt assembly

**Task prompt is byte-identical across groups.** Only the system-augmentation differs:
- `test`: project-learnings injected verbatim (the relevant group's `learning_text`)
- `control`: no learnings text
- `modified` (if defined): the user-provided subset

The prompt carries the task body **inline** (read from corpus or `.benchmark-private/<run-id>/tasks/`). The worker is never told "read `task.md`" or given any path inside `plugins/strategic-implementation/skills/learnings-benchmark/`. The worker is told its working directory is `<absolute-path-to-worktree>` and that it must `cd` there before any file operation.

**Per-trial random nonce.** Prepend a single line to every worker system prompt:

```
Trial-nonce: <16-hex-random>
```

This neutralizes API prompt-cache prefix-sharing across trials and groups. Cache reads on the worker prefix should be near zero; any residual asymmetry is bounded.

### Dispatch

**Dispatch in waves of `max_concurrent_dispatches`** (NOT a single fan-out). The orchestrator already created the isolated worktree, so do **not** pass `isolation: "worktree"` (that would create a second worktree off the current branch HEAD — the un-sanitized one). For each call:

```
Agent(
  subagent_type: "general-purpose",
  model: <pinned>,
  run_in_background: true,
  prompt: <worker-prompt>   # opens with: "Working directory: <abs WORK path>. cd there before any file operation."
)
```

Record `dispatch_ts` per call.

### Worker contract (literal in the dispatch prompt)

The worker MUST:
1. `cd` into the working directory provided in the prompt and perform all file reads/writes there.
2. **Stay inside the working directory.** Do NOT read or write any file outside it. Do NOT use `../` to navigate above it. Do NOT use absolute paths whose prefix is outside the working directory. The worker is launched from a parent process whose CWD contains unrelated files; reading those would invalidate the trial.
3. Complete the task. Write outputs to `./output/` inside that working directory (NOT the standard branch tree).
4. Write `./_run-stats.json` with self-recorded fields:
   ```json
   {
     "input_tokens": <int>,
     "output_tokens": <int>,
     "cache_creation_input_tokens": <int>,
     "cache_read_input_tokens": <int>,
     "start_iso": "<ISO-8601>",
     "end_iso": "<ISO-8601>"
   }
   ```
   This is a cross-check against external transcript parse; it does NOT drive decisions. The worker does NOT need to commit; the orchestrator harvests the worktree directly after the agent returns.
5. **MUST NOT spawn sub-agents** (no Task / Agent calls). Sub-agent token costs are invisible to the parent transcript and silently undercount.

### Post-dispatch harvest + cleanup (orchestrator)

When each Agent call returns:

```bash
# Harvest into the gitignored run-private tree.
mkdir -p ".benchmark-private/<run-id>/trial-<n>/"
cp -R "$WORK/output" ".benchmark-private/<run-id>/trial-<n>/output"
cp     "$WORK/_run-stats.json" ".benchmark-private/<run-id>/trial-<n>/_run-stats.json" 2>/dev/null || true
git worktree remove --force "$WORK"
```

If the worker did not produce `./output/`, mark the trial `lost`. If `_run-stats.json` is absent, fall back to transcript parse only (Phase 4 cross-check).

---

## Phase 4 — Capture metrics + blind score

### External capture (primary signal)

Per call:
- `dispatch_ts` recorded when `Agent(...)` is invoked.
- `completion_ts` recorded when the Agent return arrives.
- `wall_clock_seconds = completion_ts − dispatch_ts`.
- Locate the agent's transcript under `~/.claude/projects/<encoded-orchestrator-cwd>/`. Because workers are dispatched **without** `isolation: "worktree"`, every worker transcript lives under the orchestrator's project path (encoded from the orchestrator's CWD), not under the per-trial worktree path. To attribute a transcript to a trial, scan `*.jsonl` files in that directory and pick the one whose first user-message timestamp falls within `[dispatch_ts, completion_ts]`. Parse cumulative `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens` from the API response entries.

Cross-check vs. `_run-stats.json`:
- transcript matched by timestamp window AND cross-check within 10% → `clean`
- transcript not found OR no transcript matches the timestamp window → fall back to `_run-stats.json`, mark `transcript-unavailable` (flagged in report)
- both missing → `lost`

### Blind judge

Dispatch a separate `Agent(subagent_type:"general-purpose", model:<pinned>)` per trial with ONLY the rubric, the task description, and the trial's diff/output — **all passed inline in the prompt**. The judge MUST NOT see: group label, group name, learnings text, trial number, dispatch order, any path under `.benchmark-private/`, any path under `plugins/strategic-implementation/skills/learnings-benchmark/`. Each judge invocation is a fresh agent (no batching across trials).

**Judge isolation.** Use the same sanitized-worktree pattern as workers: create `.benchmark-private/<run-id>/judge-<n>/worktree` off `BASE_SHA`, strip the benchmark machinery, dispatch without `isolation`, then `git worktree remove --force`. The judge's worktree need not contain repo code at all — but using the same pattern keeps it consistent and prevents the judge from greping the repo for context that would leak the run.

**Rubric (fixed; version-tagged in the report header):**
```json
{
  "bug_count": <int ≥ 0>,
  "severity_max": <int 0|1|2|3, where 0 = no bugs>,
  "task_complete": <bool>,
  "code_quality": <int 1-5>
}
```

If the judge returns malformed JSON: re-dispatch once. On second failure, mark the cell `unscored`.

### Step 4b — Auto-bump trials

After Phase 4, if any `(group × task)` cell has primary-metric stddev > 30% of mean (primary metric: `code_quality`), re-dispatch 2 additional trials for that cell. Use the SAME billed-total formula version captured at Phase 3 dispatch start. **Do NOT mix formula versions within a run.** If the formula version has changed since dispatch (e.g. multi-day run), abort the bump and report the original cell as low-confidence.

### Strict completion gate

If any cell ends with N<3 successful trials (`clean` or `transcript-unavailable`) after retries (max 2 retries per `lost` trial), **ABORT** the run before Phase 5. Surface the asymmetry. Do NOT proceed to scoring with incomplete cells.

If one group's lost-trial rate exceeds another's by >20% (likely safety-refusal asymmetry tracking the learnings injection), mark the affected group `unbenchmarkable` and refuse to score it. The asymmetry itself is reportable signal.

---

## Phase 5 — Report + commit

Compose the report in `.benchmark-private/<run-id>/report.md`. **Then** create `<feature-folder>/run-<id>/` (this is the first tracked write since Step 0.4) and copy ONLY the final report — no learnings JSON, no trial outputs, no intermediate prompts, no judge transcripts. Those stay in `.benchmark-private/` (gitignored) as the audit trail.

### Report header

```
# Learnings Benchmark Report
- run_id: <id>
- target_model: <pinned model>
- branch: <benchmark branch>
- run_start / run_end: <ISO timestamps>
- trial_count_default: <N>
- max_concurrent: <N>
- rubric_version: v1
- billed_total_formula_version: v1
- billed_total formula: billed = output + cache_creation_input + (input_uncached × 1.0) + (cache_read × 0.1)
  (formula approximates current Claude pricing weighting; pin in report so cross-run comparisons stay honest)
- cache_discounted_total formula: billed − (cache_read × 0.1)
```

### Scorecard table — one block per learning group

```
## Group: <group_id> — <title>
| metric | test (mean ± sd) | control (mean ± sd) | [modified] | Δ (test − control) | sig |
|---|---|---|---|---|---|
| bug_count | ... | ... | ... | ... | flag if |Δ| ≤ sd |
| severity_weighted_bugs (= bug_count × severity_max) | ... | ... | ... | ... | ... |
| task_complete_rate | ... | ... | ... | ... | ... |
| code_quality | ... | ... | ... | ... | ... |
| billed_total | ... | ... | ... | ... | ... |
| cache_discounted_total | ... | ... | ... | ... | ... |
| wall_clock_seconds | ... | ... | ... | ... | ... |
| input_tokens | ... | ... | ... | ... | — |
| output_tokens | ... | ... | ... | ... | — |
| cache_read_tokens | ... | ... | ... | ... | — |
| cache_write_tokens | ... | ... | ... | ... | — |
```

### Recommendation per group

Decision logic uses the **cache-discounted billed total** to neutralize residual cache asymmetry:

- **keep** iff Δquality > stddev AND quality delta justifies the cache-discounted token-cost delta.
- **retire** iff Δquality ≤ stddev AND tokens-or-time worse on cache-discounted basis.
- **modify** otherwise (mixed signals: e.g. quality up on some tasks, neutral on others). Cite which task patterns drove the win.

State the recommendation in one sentence with a numeric justification (cite the deltas).

### Low-confidence runs section

List any `(group × task)` cell with: stddev > 30% of mean on the primary metric after auto-bump; any `transcript-unavailable` trials; any `unscored` cells; any `unbenchmarkable` group.

### Commit

```
mkdir -p <feature-folder>/run-<run-id>/
cp .benchmark-private/<run-id>/report.md <feature-folder>/run-<run-id>/report.md
git add <feature-folder>/run-<run-id>/report.md
git commit -m "learnings-benchmark: run-<run-id> on <model>"
```

The commit lands on the benchmarking branch only and contains exactly one tracked file (the report). **No merge step is offered.** The user merges manually.

`.benchmark-private/<run-id>/` remains on disk as the local audit trail — workers' raw outputs, judge transcripts, prompts, learnings JSON. It is gitignored, so it never bleeds into future worker dispatches and never lands on the branch. The user may delete it after reviewing the report.

---

## Anti-bias rules (load-bearing invariants)

These restate the load-bearing constraints from earlier phases as a single checklist. If any is violated, the run is invalid.

1. **No group labels in worker prompts.** No `test`, `control`, `modified`, `with-learnings`, `without-learnings`, group titles, or trial numbers anywhere in the worker prompt.
2. **No "you are being benchmarked" language.** The worker prompt reads like a normal task assignment.
3. **No self-reported metrics drive decisions.** `_run-stats.json` is a cross-check only; Phase 5 scoring uses external capture.
4. **Identical task wording byte-for-byte across groups.** Only the system-augmentation differs.
5. **Per-trial random nonce** on every worker system prompt (Phase 3).
6. **Cache-discounted comparison** for the keep/retire/modify decision (Phase 5).
7. **Blind judge.** Fresh agent per trial; no group label, no learnings text, no trial number.
8. **Wave-based dispatch.** No full fan-out; cap at `max_concurrent_dispatches`.
9. **Sanitized worker worktree.** Every worker (and judge) runs in a worktree created off `BASE_SHA` with `plugins/strategic-implementation/skills/learnings-benchmark/`, `plugins/strategic-implementation/agents/`, `docs/strategic-implementation/project-learnings.md`, and any prior benchmark folder removed. **Do NOT use the Agent `isolation: "worktree"` parameter** — it would create a worktree off the un-sanitized benchmark-branch HEAD.
10. **No tracked benchmark artifacts during the run.** Between Step 0.4 (`.gitignore` commit) and Phase 5 (report commit), no files are written into the tracked tree of the benchmark branch. All run state lives under `.benchmark-private/<run-id>/`. Violation = workers can grep prior trials' outputs and bias the current trial.
11. **Inline task delivery.** Worker prompts include the task body inline. Workers are never given a path inside the corpus or any benchmark directory. The corpus exists for orchestrator + reproducibility, not for worker discovery.

---

## Failure modes (quick reference)

| Failure | Remediation |
|---|---|
| Worker did not produce `./output/` in its sanitized worktree before the orchestrator's harvest step | Mark `lost`; retry up to 2× per trial. If cell ends N<3 after retries, ABORT before Phase 5. |
| Transcript not findable at expected path | Fall back to `_run-stats.json`; mark `transcript-unavailable`. If all trials fall back, surface a transcript-path-broken warning (encoded-cwd path may have changed). |
| Judge returns malformed JSON | Re-dispatch judge once. On second failure, mark cell `unscored`. |
| Safety-refusal rate differs by >20% across groups | Mark the affected group `unbenchmarkable`. The asymmetry is itself a reportable finding. |
| Pricing-formula version changes mid-run (between original dispatch and auto-bump) | Abort the bump for that cell; mark cell low-confidence; report original trials only. |
