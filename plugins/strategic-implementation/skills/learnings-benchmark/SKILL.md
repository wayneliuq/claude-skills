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

   > 🛑 **Working tree not clean.** Worktree dispatches branch off the current commit; uncommitted changes leak across groups asymmetrically.
   >
   > Remediation: commit or stash, then re-invoke.

   Exit.

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

`<feature-folder>` is `docs/strategic-implementation/<YYYY-MM-DD>-learnings-benchmark/` (create if absent). `<id>` is a short timestamped slug, e.g. `2026-05-05-1430`.

---

## Phase 2 — Compile tasks + run plan

For each selected group, pick a task:

1. **Corpus first.** Look in `plugins/strategic-implementation/skills/learnings-benchmark/benchmarks/<group_id-or-theme>/<task-slug>/`. If a `task.md` + `success-criteria.md` pair exists, use it.
2. **Synthesis fallback.** If no corpus task exists, generate one whose deltas would be observable: a small refactor, bug fix, or design choice that the learning's WHEN/DO logic would steer differently than the control. Prefer tasks where the right answer is itself contested.

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

For each `(task × group × trial)`, assemble the worker prompt.

**Task prompt is byte-identical across groups.** Only the system-augmentation differs:
- `test`: project-learnings injected verbatim (the relevant group's `learning_text`)
- `control`: no learnings text
- `modified` (if defined): the user-provided subset

**Per-trial random nonce.** Prepend a single line to every worker system prompt:

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
1. Complete the task and commit `trial-<n>/output/`.
2. Commit `trial-<n>/_run-stats.json` with self-recorded fields:
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
   This is a cross-check against external transcript parse; it does NOT drive decisions.
3. **MUST NOT spawn sub-agents** (no Task / Agent calls). Sub-agent token costs are invisible to the parent transcript and silently undercount.

If the worker fails to commit, the trial is marked `lost`.

---

## Phase 4 — Capture metrics + blind score

### External capture (primary signal)

Per call:
- `completion_ts` recorded when the Agent return arrives.
- `wall_clock_seconds = completion_ts − dispatch_ts`.
- Locate the agent's transcript at `~/.claude/projects/<encoded-worktree-path>/<session>.jsonl`. Parse cumulative `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens` from the API response entries.

Cross-check vs. `_run-stats.json`:
- transcript located AND cross-check within 10% → `clean`
- transcript not found → fall back to `_run-stats.json`, mark `transcript-unavailable` (flagged in report)
- both missing → `lost`

### Blind judge

Dispatch a separate `Agent(subagent_type:"general-purpose", model:<pinned>)` per trial with ONLY the rubric, the task description, and the trial's diff/output. The judge MUST NOT see: group label, group name, learnings text, trial number, dispatch order. Each judge invocation is a fresh agent (no batching across trials).

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
git add <feature-folder>/run-<id>/
git commit -m "learnings-benchmark: run-<id> on <model>"
```

The commit lands on the benchmarking branch only. **No merge step is offered.** The user merges manually.

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

---

## Failure modes (quick reference)

| Failure | Remediation |
|---|---|
| Worker did not commit (worktree auto-cleaned) | Mark `lost`; retry up to 2× per trial. If cell ends N<3 after retries, ABORT before Phase 5. |
| Transcript not findable at expected path | Fall back to `_run-stats.json`; mark `transcript-unavailable`. If all trials fall back, surface a transcript-path-broken warning (encoded-cwd path may have changed). |
| Judge returns malformed JSON | Re-dispatch judge once. On second failure, mark cell `unscored`. |
| Safety-refusal rate differs by >20% across groups | Mark the affected group `unbenchmarkable`. The asymmetry is itself a reportable finding. |
| Pricing-formula version changes mid-run (between original dispatch and auto-bump) | Abort the bump for that cell; mark cell low-confidence; report original trials only. |
