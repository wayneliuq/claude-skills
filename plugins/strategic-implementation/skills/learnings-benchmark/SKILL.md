---
name: learnings-benchmark
description: Explicit-invocation A/B benchmark of project learnings vs control on a pinned model. Branch-only execution; isolated worktree per trial; blind judge scores outputs; per-learning keep / retire / modify report committed to the benchmarking branch. Run infrequently to decide which learnings still earn their keep as models improve.
---

# learnings-benchmark

Explicit-invocation only. **Never** auto-triggered by hooks, orchestrators, or other skills. The user invokes this skill directly when they want to know whether the project-learnings bundle still earns its keep on a given model.

The skill produces an evidence-backed keep / retire / modify recommendation per learning group, grounded in measured deltas (bugs, severity, billed tokens, wall-clock, blind quality). It does NOT modify `project-learnings.md` — output is read-only; the user edits manually.

You receive arguments at invocation time. See **Step 1 — Inputs**.

---

## Step 0 — Branch + working-tree pre-flight

**This step refuses to run on `main` / `master` / any branch matching `release/*` or `prod/*`.** The benchmarking branch is the record; main never sees benchmark commits.

1. `git branch --show-current` → record `<branch>`.
2. If `<branch>` matches `main`, `master`, `release/*`, or `prod/*`:

   > 🛑 **Refusing to run on `<branch>`.** This skill commits benchmark artifacts and must run on a dedicated branch.
   >
   > Remediation: `git checkout -b benchmark/<YYYY-MM-DD>-<slug>`

   Exit. No further work.

3. `git status --porcelain` → if non-empty:

   > 🛑 **Working tree not clean.** Worktree dispatches branch off the current commit; uncommitted changes leak across groups asymmetrically.
   >
   > Remediation: commit or stash, then re-invoke.

   Exit.

(Honors brief D2.)

---

## Step 1 — Inputs

**Required:**
- `model` — literal model ID (e.g. `claude-opus-4-7`). The skill **hard-fails** if missing. No defaulting, no inference from the current session.

**Optional:**
- `--dry-run` — runs Phases 1-2 only and exits before any agent dispatch. Prints the planned run (target model, learning groups, task list, trial count, branch name) so the user can sanity-check the plan before paying for trials. (Honors brief D1.)
- `third_group` — definition of a modified or minimized learnings set. Path to a file or inline subset list. If present, the run uses three groups (test / control / modified); otherwise two (test / control).
- `trials` — integer override; default 3. Auto-bump to N+2 fires per cell on stddev > 30% of mean of the primary metric.
- `max_concurrent_dispatches` — integer; default 4; hard cap 8. Wave size for parallel agent dispatch.
- `corpus_filter` — restrict Phase 2 task selection to a subset of corpus themes (e.g. `tests` only).

If `model` is absent: print one line — `Refusing to run: target model ID not provided. Required.` — and exit.

---

## Phase 1 — Gather learnings

Read the learnings sources:
- `docs/strategic-implementation/project-learnings.md`
- `plugins/strategic-implementation/agents/*.md` (inlined hardening rules in review-agent files)

Propose **semantic groupings**. Default heuristic: ≥1 group per `#tag` in `project-learnings.md` (today: `#scope`, `#security`, `#technical`, `#tests`) plus one group per agent role with inlined rules. A learning may belong to multiple groups; record both.

Present the grouping to the user as a numbered list. The user may:
- accept the proposal (`accept`)
- edit inline (rename groups, move learnings between groups, drop a learning, drop a group)
- abort (`cancel`)

On accept, persist to `<feature-folder>/run-<id>/learnings.json`:

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

The `<feature-folder>` is `docs/strategic-implementation/<YYYY-MM-DD>-learnings-benchmark/` (create if absent). The `<id>` is a short timestamped slug, e.g. `2026-05-05-1430`.

---

## Phase 2 — Compile tasks + run plan

For each selected group, pick a task:

1. **Corpus first.** Look in `plugins/strategic-implementation/skills/learnings-benchmark/benchmarks/<group_id-or-theme>/<task-slug>/`. If a `task.md` + `success-criteria.md` pair exists, use it.
2. **Synthesis fallback.** If no corpus task exists, generate one whose deltas would be observable: a small refactor, bug fix, or design choice that the learning's WHEN/DO logic would steer differently than the control. Prefer tasks where the right answer is itself contested (so a learning that points to the right answer pays off).

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

User approves or aborts.

**If `--dry-run`: print the summary and exit.** No dispatch.

---

## Phase 3 — Dispatch

For each `(task × group × trial)`, assemble the worker prompt.

**Task prompt is byte-identical across groups.** Only the system-augmentation differs:
- `test` group: project-learnings injected verbatim (the relevant group's `learning_text`)
- `control` group: no learnings text
- `modified` group (if defined): the user-provided subset

**Per-trial random nonce.** Prepend a single line to every worker system prompt of the form:

```
Trial-nonce: <16-hex-random>
```

This neutralizes API prompt-cache prefix-sharing across trials and groups. Cache reads on the worker prefix should be near zero; any residual asymmetry is bounded.

**Dispatch in waves of `max_concurrent_dispatches`** (NOT a single fan-out). For each call:

```
Agent(
  subagent_type: "general-purpose",
  isolation: "worktree",
  model: <pinned>,
  run_in_background: true,
  prompt: <worker-prompt>
)
```

Record `dispatch_ts` per call.

### Worker contract (literal in the dispatch prompt)

The worker MUST:
1. Complete the task and commit `trial-<n>/output/` (the work — code, doc, whatever the task asked for).
2. Commit `trial-<n>/_run-stats.json` with the worker's self-recorded fields:
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
   This is a cross-check against external transcript parse; it does NOT drive decisions on its own.
3. **MUST NOT spawn sub-agents** (no Task / Agent calls). All work happens in-process. Sub-agent token costs are invisible to the parent transcript and silently undercount.

If the worker fails to commit, the trial is marked `lost`.

---

## Phase 4 — Capture metrics + blind score

### External capture (primary signal)

Per call:
- `completion_ts` recorded when the Agent return arrives.
- `wall_clock_seconds = completion_ts − dispatch_ts`.
- Locate the agent's transcript at `~/.claude/projects/<encoded-worktree-path>/<session>.jsonl`. Parse cumulative `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens` from the API response entries.

Cross-check vs. `_run-stats.json` from the worktree commit:
- transcript located AND cross-check within 10% → mark trial `clean`
- transcript not found → fall back to `_run-stats.json`, mark trial `transcript-unavailable` (flagged in report)
- both missing → mark trial `lost`

### Blind judge

Dispatch a separate `Agent(subagent_type:"general-purpose", model:<pinned>)` per trial with ONLY:
- the rubric (below)
- the task description
- the trial's diff / output

The judge MUST NOT see: group label, group name, learnings text, trial number, dispatch order. Each judge invocation is a fresh agent (no batching across trials).

**Rubric (fixed; version-tagged in the report header):**
```json
{
  "bug_count": <int ≥ 0>,
  "severity_max": <int 0|1|2|3, where 0 = no bugs>,
  "task_complete": <bool>,
  "code_quality": <int 1-5>
}
```

If the judge returns malformed JSON: re-dispatch the judge once. On second failure, mark the cell `unscored`.

### Step 4b — Auto-bump trials

After Phase 4, if any `(group × task)` cell has primary-metric stddev > 30% of mean (primary metric: `code_quality`), re-dispatch 2 additional trials for that cell. Use the SAME billed-total formula version captured at Phase 3 dispatch start. Do **NOT** mix formula versions within a run. If the formula version has changed since dispatch (e.g. multi-day run), abort the bump and report the original cell as low-confidence.

### Strict completion gate

If any cell ends with N<3 successful trials (`clean` or `transcript-unavailable`) after retries (max 2 retries per `lost` trial), **ABORT** the run before Phase 5. Surface the asymmetry. Do NOT proceed to scoring with incomplete cells.

If one group's lost-trial rate exceeds another's by >20% (likely safety-refusal asymmetry tracking the learnings injection), mark the affected group `unbenchmarkable` and refuse to score it. The asymmetry itself is reportable signal.

---

## Phase 5 — Report + commit

Write `<feature-folder>/run-<id>/report.md`.

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
| severity_weighted_bugs | ... | ... | ... | ... | ... |
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
- **modify** otherwise (mixed signals: e.g. quality up on some tasks, neutral on others). Suggested narrower scope: cite which task patterns drove the win.

State the recommendation in one sentence with a numeric justification (cite the deltas).

### Low-confidence runs section

List any `(group × task)` cell with: stddev > 30% of mean on the primary metric after auto-bump; any `transcript-unavailable` trials; any `unscored` cells; any `unbenchmarkable` group.

### Commit

```
git add <feature-folder>/run-<id>/
git commit -m "learnings-benchmark: run-<id> on <model>"
```

The commit lands on the benchmarking branch only. **No merge step is offered.** The user merges manually if they want the report tracked elsewhere.

---

## Anti-bias rules (load-bearing)

1. **No group labels in worker prompts.** The worker prompt does not contain the strings `test`, `control`, `modified`, `with-learnings`, `without-learnings`, group titles, or trial numbers.
2. **No "you are being benchmarked" language.** The worker prompt reads exactly like a normal task assignment.
3. **No self-reported metrics drive decisions.** The worker's `_run-stats.json` is a sanity-check against external capture; it never feeds Phase 5 scoring.
4. **Identical task wording byte-for-byte across groups.** Only the system-augmentation (learnings injection) differs.
5. **Per-trial random nonce.** Every worker system prompt starts with a fresh nonce so prefix-cache reads stay symmetric.
6. **Cache-discounted comparison.** Decision logic uses billed-total minus cache-read contribution; raw cache_read shown separately for transparency.
7. **Blind judge.** Judge sees no group label, no learnings text, no trial number. Fresh agent per trial.
8. **Wave-based dispatch.** No full fan-out of the dispatch matrix. Cap at `max_concurrent_dispatches`.

---

## Failure modes & remediation

| Failure | Remediation |
|---|---|
| (a) Worker did not commit (worktree auto-cleaned) | Mark trial `lost`; retry up to 2× per trial. If cell ends with N<3 after retries, ABORT before Phase 5. |
| (b) Transcript file not findable at expected path | Fall back to `_run-stats.json`; mark trial `transcript-unavailable`; flag in report. If all trials in a run fall back, surface a transcript-path-broken warning (the encoded-cwd path may have changed in the harness). |
| (c) Judge returns malformed JSON | Re-dispatch judge once. On second failure, mark cell `unscored`. |
| (d) Safety-refusal rate differs by >20% across groups | Mark the affected group `unbenchmarkable`. Surface the asymmetry — it is itself a reportable finding. |
| (e) Pricing-formula version changes mid-run (between original dispatch and auto-bumped trials) | Abort the bump for that cell; mark cell low-confidence; report the original trials only. Do NOT mix formula versions. |
| (f) `model` argument absent at Step 1 | Refuse with `Refusing to run: target model ID not provided. Required.` |
| (g) `git status --porcelain` non-empty at Step 0 | Refuse with the working-tree-clean remediation. |
| (h) Branch is `main` / `master` / `release/*` / `prod/*` | Refuse with the benchmarking-branch remediation. |
