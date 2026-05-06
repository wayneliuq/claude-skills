# Product Brief: Learnings Benchmark
_Slug: learnings-benchmark · Date: 2026-05-05 · Autonomy: auto_

## 1. Working backwards

The strategic-implementation plugin gains a new skill, `learnings-benchmark`, that the user invokes explicitly when they want to know whether the project learnings still earn their keep on a given model. One command kicks off a controlled benchmark: identical tasks run in isolated worktrees across a test group (with project learnings injected) and a control group (without), with an optional third "modified/minimized" group. The skill produces a per-learning-group scorecard — bugs, severity, billed tokens, wall-clock, blind quality score — and a keep / retire / modify recommendation grounded in measured deltas, not intuition. Re-running the skill after a model upgrade visibly changes the recommendations when the model has actually changed.

## 2. What the user does / sees

| # | Deliverable (user-observable) | Validation |
|---|---|---|
| D1 | The skill exists in the marketplace: `plugins/strategic-implementation/skills/learnings-benchmark/SKILL.md` with frontmatter matching repo conventions; `/strategic-implementation:learnings-benchmark` is callable. | `cli` — invoke the skill with `--dry-run`; it prints the planned run (target model, learning groups, task list, trial count, branch name) and exits without dispatching. |
| D2 | Pre-flight branch guard: invoking on `main` (or any protected branch) refuses with a clear error and a one-command remediation (the branch name to create). | `cli` — invoke from `main`; expect non-zero exit with the remediation message. Re-run on `benchmark/<date>-<slug>`; expect proceed. |
| D3 | Phase 1 — Learnings gathering: the skill scans `docs/strategic-implementation/project-learnings.md` and `plugins/strategic-implementation/agents/*.md`, proposes semantic groupings, and the user edits/approves the final set inline. | `cli` — run phase 1 only; user sees a grouped list and an edit prompt; approval persists to `<feature-folder>/run-<id>/learnings.json`. |
| D4 | Phase 2 — Task compilation & approval: corpus-first (reads `plugins/strategic-implementation/skills/learnings-benchmark/benchmarks/`); falls back to synthesizing a task per group from the learning text. User approves task set, group composition (test/control, optional modified), trial count, and pinned model ID. | `cli` — phase 2 emits a plan summary (tasks × groups × trials, total agent dispatches, est. tokens) and waits for approval; declined plans abort cleanly. |
| D5 | Phase 3 — Dispatch in isolated worktrees: each trial runs in its own `Agent(isolation:"worktree")` with the pinned `model` parameter; task prompts are byte-identical across groups; only the learnings injection differs. Trials run in parallel via `run_in_background` where capacity allows; otherwise dispatch order is randomized across groups. | `cli` — dispatched agents land in distinct worktree paths; each writes outputs into its own `run-<id>/trial-<n>/` task folder; the controller logs dispatch + completion timestamps externally. |
| D6 | Phase 4 — External measurement & blind scoring: the harness captures wall-clock (dispatch → completion) and token buckets (input / output / cache_read / cache_write) from transcripts — never from the agent's self-report. A separate blind judge agent grades each output (bug count, severity 1–3, task-completion binary, code-quality 1–5) without seeing group labels or which learnings were injected. | `post-hoc` — run a smoke benchmark with one trivial task and 3 trials per group; manually verify (a) the judge's input has no group label, (b) all four token buckets and a wall-clock are populated per trial, (c) trials with stddev > 30% of mean trigger an auto-bump to 5 trials. |
| D7 | Phase 5 — Report on the benchmarking branch: a per-learning-group scorecard with deltas, stddev, billed-total formula pinned, and a keep / retire / modify recommendation. Committed to the benchmarking branch under `<feature-folder>/run-<id>/report.md`. No commits to `main`; no merge step offered. | `cli` — `git log main..HEAD --oneline` after a run shows the report commit on the benchmarking branch only; `git log main` is unchanged. |

## 3. Success signal

After running the skill against the current `project-learnings.md` on a specific target model, the user can point to the generated report and read off, for each learning group, a keep / retire / modify recommendation backed by measured numbers (bug count, severity, billed tokens, wall-clock, blind quality). Re-running the same skill against the same learnings on a meaningfully different model produces visibly different recommendations.

## 4. Boundaries

**In scope:**
- New skill `learnings-benchmark` under `plugins/strategic-implementation/skills/`.
- Phases 1–5 as described.
- A small seeded `benchmarks/` corpus (≥1 task per current major learning theme) to bootstrap.
- Frontmatter, README touch-up, and any plugin manifest entry needed for `/strategic-implementation:learnings-benchmark` to be callable.

**Out of scope:**
- Auto-applying recommendations to `project-learnings.md` (read-only output; user edits manually).
- Cross-model comparison in a single run (one run = one pinned model).
- Cost estimation against current API pricing in dollars (the report shows the billed-total formula and token counts; pricing layer is deferred).
- Continuous / scheduled benchmarking.
- Replacing the deviation + project-learnings loop in strategic-implementation.

**Anti-goals (we'd reject these even if free):**
- Self-reported metrics from benchmark agents — token counts or timings the agent claims about itself are inadmissible by design.
- Heuristic scoring of "is this learning still relevant?" without running real tasks. The whole point is empirical evidence, not LLM-as-pundit.
- Any auto-merge or auto-PR of benchmark results into `main`. The benchmarking branch is the record.
- Telling the worker agents they are being benchmarked. Bias risk; the prompt must read as a normal task.

## 5. Decisions

| Decision | Choice | Status |
|---|---|---|
| Skill runs only on a dedicated benchmarking branch | `benchmark/<YYYY-MM-DD>-<slug>`; refuses on `main` or protected branches | `[HARD DECISION]` |
| Agent isolation | Each trial in its own git worktree via `Agent(isolation:"worktree")` | `[HARD DECISION]` |
| Task prompt invariance | Byte-identical across groups; only learnings injection differs | `[HARD DECISION]` |
| Model pinning | `model` parameter set on every dispatch; default-inheritance forbidden | `[HARD DECISION]` |
| Quality scoring | Blind judge agent; no group labels, no learnings visibility | `[HARD DECISION]` |
| Trial count | ≥3 per (group × task); auto-bump to 5 if stddev > 30% of mean on primary metric | `[HARD DECISION]` |
| Token measurement | Report input / output / cache_read / cache_write separately + billed-total formula pinned in the report | `[HARD DECISION]` |
| Wall-clock measurement | External (dispatch → completion); never self-reported | `[HARD DECISION]` |
| Invocation | Explicit only; never auto-triggered by hooks or other skills | `[HARD DECISION]` |
| Learnings sources | `project-learnings.md` + `plugins/strategic-implementation/agents/*.md`; user approves merged set | `settled` |
| Task source | Corpus-first (`benchmarks/`); fall back to synthesis from learning text | `settled` |
| Recommendation logic | keep if Δquality > stddev AND quality justifies token cost; retire if no quality delta and tokens/time worse; modify if mixed | `settled` |
| Optional third group | "modified/minimized" learnings set, user-defined per run | `settled` |
| Output artifacts | All under `<feature-folder>/run-<id>/` on the benchmarking branch | `settled` |

### Tradeoff — branch-only, no merge step

| Option | Pro | Con | Why we chose |
|---|---|---|---|
| Benchmark on `main` | Simpler workflow | Pollutes history with worktree experiments; risk of stray commits | rejected |
| Benchmark branch + auto-merge report | Report visible from `main` | Auto-merge invites accidental main commits; muddies the "benchmarks are records, not deliverables" stance | rejected |
| **Benchmark branch, no merge** | Records preserved, main untouched, user merges manually if desired | Slightly more friction to find old reports | **chosen** |

### Tradeoff — blind judge vs. self-judge or rubric-only

| Option | Pro | Con | Why we chose |
|---|---|---|---|
| Self-judge (worker scores own output) | Cheapest | Maximally biased; defeats the benchmark | rejected |
| Static rubric scored by harness | Deterministic | Cannot detect subtle bugs or quality differences in code | rejected |
| **Blind judge agent** | Catches semantic quality; bias-resistant when group labels withheld | Costs additional tokens; judge can be wrong (mitigated by N≥3 + variance reporting) | **chosen** |

## 6. Risks & unknowns

- **Worktree auto-cleanup on no-changes** — `Agent(isolation:"worktree")` cleans up worktrees that produced no commits. Benchmark agents may complete a task without committing, losing the transcript. Mitigation: the task prompt requires the agent to commit its output (even a notes file) so the worktree is preserved. Owner: skill author.
- **Token-bucket capture surface area** — the harness must read token counts from the run transcript / API metadata, not the agent's reply. If the Agent tool surface does not expose totals on return, the skill must locate the transcript file in the worktree. Owner: skill author; verify during D6.
- **Corpus drift** — a maintained `benchmarks/` corpus risks staleness as learnings change. Mitigation: synthesis fallback in phase 2; corpus tasks can be retired when their target learning is retired.
- **Judge bias from prompt phrasing** — a poorly worded rubric can systematically prefer one group's style. Mitigation: the rubric is fixed in the skill, version-bumped on change, and the report logs the rubric version used.
- **Variance dominates signal on small tasks** — with N=3 and short tasks, stddev can swallow real deltas. Mitigation: auto-bump to 5; flag low-confidence runs in the report rather than over-claim.
- **Cache pollution across trials** — running the same prompt back-to-back warms the cache and biases the second run. Mitigation: parallel dispatch, or randomized order across groups.

## 7. References & revision log

**Document references:**
- Architecture: `plugins/strategic-implementation/skills/strategic-implementation/SKILL.md` (orchestrator workflow); existing skill files (`clarify`, `execution-plan`, `executing-plans`, `post-execution`, `review`) as structural reference for the new skill.
- UX/PMF: n/a — internal developer tooling.
- Security policy: none.
- Schema/ERD: n/a — no data storage.

**Revision log:**
- v0.1 · 2026-05-05 · initial draft
