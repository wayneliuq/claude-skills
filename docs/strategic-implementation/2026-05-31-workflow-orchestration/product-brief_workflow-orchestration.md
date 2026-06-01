# Product Brief: Cross-Domain Macro-Deliverable Execution

_Slug: workflow-orchestration · Date: 2026-05-31 · Autonomy: auto_

## 1. Working backwards (≤5 sentences, release-note voice)

> The strategic-implementation skill now recognizes when a piece of work is one user-validateable outcome that spans several domains (commonly backend, the API/contract between them, and frontend) and cannot be honestly split into independently-checkable pieces. Instead of forcing that work into many small sub-deliverables that can't each be validated on their own, the skill treats it as a single "macro-deliverable": it builds the domains together, holds them to one honest end-to-end validation of the integrated outcome, and remembers the validation approach used so the next similar feature reuses it. The whole outcome lands as one clean, validated record of work. When the underlying parallel capability is available the domains also build concurrently (observable in `/workflows`, typically faster) — but the core value is the honest validation of one cross-domain unit and the captured know-how, not the speed. Everything that *can* be cleanly decomposed still is — small and ordinary work runs exactly as before — and when the parallel capability is off, unavailable, or interrupted, the same macro-deliverable is simply built one domain at a time, with nothing lost.

## 2. What the user does / sees

**Who is the user of this feature:** The **skill operator** — a developer or PM running the `strategic-implementation` skill inside Claude Code to plan and execute a feature. Their interaction surface is the skill's normal flow (clarify → brief → execution plan → execution) plus Claude Code's `/workflows` progress view.

### D1 — During planning, the skill flags a cross-domain outcome that shouldn't be split, and marks it as a macro-deliverable
When an outcome spans multiple domains and its parts can't each be validated end-to-end on their own, the plan designates it a single macro-deliverable instead of fragmenting it into pieces that look done but can't be demonstrated.
**How a user verifies:**
1. Run the skill on a feature that is genuinely one cross-domain outcome (e.g. a new capability needing backend + the contract + frontend together to be usable).
2. Read the proposed execution plan and confirm that outcome appears as **one** deliverable explicitly marked as cross-domain / workflow-executed — not split into a backend piece, a contract piece, and a frontend piece that each claim to be independently validateable.
3. Confirm ordinary, cleanly-separable work in the same plan is still listed as normal individual deliverables.

### D2 — A macro-deliverable executes as a single workflow and lands as one clean record of work
At execution, the macro-deliverable's domains are built concurrently within one orchestrated run, validated together, and committed as one atomic unit.
**How a user verifies:**
1. Run the skill to execution on a plan containing a macro-deliverable.
2. Open `/workflows` and observe the domains building concurrently under one run.
3. After completion, inspect the project history and confirm the whole macro-deliverable produced **exactly one** atomic record of work (one commit), with the per-feature progress log and deviation log intact and consistent — identical bookkeeping shape to a sequential run, just produced faster.

### D3 — Only outcomes that truly need it use a workflow; everything else is untouched
The workflow path is a narrow exception. Work that can be cleanly decomposed, or that is small, runs through the existing sequential flow with zero added overhead.
**How a user verifies:**
1. Run the skill on a single-domain or trivially-small change.
2. Confirm no workflow is launched (nothing appears in `/workflows`) and the run proceeds exactly as in the current version.

### D4 — The skill degrades gracefully when parallel execution is unavailable
If the parallel capability is disabled, missing (older environment), or interrupted (the session ends mid-run), the macro-deliverable is built one domain at a time instead — no lost work, no error.
**How a user verifies:**
1. Disable the parallel capability (or run where it isn't available) and run the skill on a feature that would otherwise use a macro-deliverable workflow.
2. Confirm the skill completes the same outcome sequentially, produces the same single record of work, and surfaces a plain note that it ran sequentially — no error, no broken state.
3. Interrupt a macro-deliverable run partway (end the session) and resume; confirm work already completed is preserved and the remainder continues.

### D5 — The operator can see why the skill chose a workflow vs. sequential
Whenever the skill picks the workflow path (or declines it), it states the reason in one line so the choice is never opaque.
**How a user verifies:**
1. Run one cross-domain feature and one ordinary feature.
2. Confirm each run prints a one-line statement of the decision and the trigger that drove it (e.g. "macro-deliverable: cross-domain, not independently validateable → workflow" vs. "decomposable → normal sequential deliverables").

### D6 — The review step holds a macro-deliverable to honest end-to-end validation
When a plan contains a macro-deliverable, review checks that its chosen validation actually demonstrates the integrated cross-domain outcome — not just each domain on its own — and suggests a stronger cross-domain method when it falls short.
**How a user verifies:**
1. Run the skill on a plan containing a macro-deliverable whose validation only checks one domain (e.g. backend only).
2. Confirm the review surfaces a high-severity finding that the validation doesn't prove the integrated outcome, naming a concrete stronger cross-domain method.
3. Fix the plan to validate the integrated outcome end-to-end and confirm review now passes that deliverable.

### D7 — The skill remembers and reuses how cross-domain work was validated before
For cross-domain / integration-sensitive work, the skill records the validation approach it actually used and, on later similar work, recalls it instead of starting from scratch.
**How a user verifies:**
1. Run a cross-domain or integration-sensitive feature to completion; confirm the per-feature validation record now captures the validation **approach** used (the pipeline/infrastructure, not just a one-word method).
2. Later, start planning another similar feature; confirm the proposed plan cites how comparable past work was validated and lets that inform the chosen method — without you re-explaining it.
3. Run the same recall in a fresh project with no prior history and confirm it degrades quietly (no error, just "no prior validation approaches found").

## 3. Success signal

A single cross-domain macro-deliverable lands as **one** atomic commit whose validation proves the integrated cross-domain outcome end-to-end (not any single domain), and the validation approach it used is captured so a later similar feature recalls it instead of guessing — while normal and small deliverables trigger no workflow at all, and the per-feature bookkeeping (one record per deliverable, consistent progress/deviation logs) stays identical to a sequential run. As an observational follow-up (not a gated acceptance step), when the parallel capability is available the domains are seen building concurrently in `/workflows`, typically in less wall-clock than a domain-by-domain build.

## 4. Boundaries

**In scope:**
- Detecting, during planning, a cross-domain outcome that can't be split without losing end-to-end validateability, and marking it as a macro-deliverable.
- Executing a macro-deliverable as a single workflow: contract/seam first, remaining domains concurrently, validated together, one atomic commit.
- A criteria gate that confines the workflow path to outcomes that genuinely qualify.
- Graceful fallback to sequential build when the capability is unavailable, disabled, or interrupted.
- A visible one-line statement of the workflow-vs-sequential decision.
- Macro-deliverable-aware validation review: review holds a macro-deliverable to proving the integrated cross-domain outcome end-to-end.
- Validation-approach memory **scoped to cross-domain / integration-sensitive work**: capture the approach used, and recall it during later similar planning.

**Out of scope:**
- Running independent deliverables / deliverable groups concurrently (the inter-deliverable approach — explicitly rejected this round).
- Parallelizing the review step (reviewers stay as today).
- Parallelizing the clarify, brief-drafting, or mockup phases.
- Speculative or research-phase fan-out.
- A general skill-memory / persistence subsystem. Validation-approach memory here is deliberately narrow (cross-domain / integration-sensitive validation only); broad memory is a separate future feature.

**Anti-goals (philosophy-level — we deliberately will not):**
- Parallelize by default. Overhead and added failure surface on ordinary work is exactly what we're avoiding.
- Let a workflow weaken bookkeeping. A faster run that produces messier or inconsistent history is a regression.
- Let a workflow bypass a pause the operator would otherwise get (flagged items, blocks, approval gates).
- Make the operator configure or manage orchestration per-run.
- Use a macro-deliverable to dodge honest decomposition. If work *can* be split into independently-validateable pieces, it must be.

## 5. Decisions

| Decision | Choice | Status |
|---|---|---|
| When does the workflow path trigger? | Only for a macro-deliverable meeting ALL criteria: (a) spans multiple domains, (b) parts not independently end-to-end-validateable, (c) together one user-observable outcome, (d) large enough that concurrent build clearly beats sequential | `[HARD DECISION]` |
| Parallelism granularity | INTRA-deliverable only — concurrent build of one outcome's domains. The skill will NOT run independent deliverables/groups concurrently | `[HARD DECISION]` |
| Behavior when capability off/missing/interrupted | Graceful fallback to sequential build; never error, never lose work | `[HARD DECISION]` |
| Does a macro-deliverable change the per-deliverable record? | No — a macro-deliverable IS one deliverable → exactly one atomic commit, logs consistent | `[HARD DECISION]` |
| Does a workflow bypass operator pause gates? | No — flagged/blocked/approval gates still pause | `[HARD DECISION]` |
| Build ordering within a macro-deliverable | Contract/seam first, then remaining domains concurrently against the agreed contract | settled |
| Validation inside the workflow | Automatable validation only; manual-preview outcomes are built + auto-checked, then handed back for the human preview | settled |
| Macro-deliverable validation bar | Review (validation-adequacy) must hold a macro-deliverable to proving the integrated cross-domain outcome end-to-end; per-domain-only validation is a high-severity finding | `[HARD DECISION]` |
| Validation-approach memory scope | Capture + recall, scoped to cross-domain / integration-sensitive validation only; NOT a general memory subsystem | `[HARD DECISION]` |
| Validation-approach recall failure mode | Degrades quietly when no prior approaches / old records lack the captured approach — no error, no block | settled |
| Exact size/qualification thresholds | Set in execution plan, tuned conservatively toward fewer workflow launches | open |

### Tradeoff — Macro-deliverable as a narrow exception (HARD DECISION)
| Option | Pro | Con |
|---|---|---|
| Narrow macro-deliverable (chosen) | Keeps decomposition honest; workflow only where splitting would break validateability | Needs a criteria check that can mis-judge borderline cases |
| Workflow for any large work | Simpler trigger | Re-introduces overhead and erodes the deliverable-gating discipline |

### Tradeoff — One commit per macro-deliverable (HARD DECISION)
| Option | Pro | Con |
|---|---|---|
| One atomic commit (chosen) | Commit/validation unit equals the unit of user value; bookkeeping unchanged | Larger blast radius — a cross-domain commit is harder to bisect/revert than three small ones |
| Per-domain commits | Finer history | Re-introduces multi-commit merge/ordering and breaks the "one record per deliverable" model |

### Tradeoff — Graceful fallback (HARD DECISION)
| Option | Pro | Con |
|---|---|---|
| Graceful fallback (chosen) | Works on every environment/CLI version; never breaks existing runs | Two build paths to maintain (concurrent + sequential) |
| Hard dependency | One path | Breaks on older/disabled environments and after interruption — unacceptable |

## 6. Risks & unknowns

- **Bookkeeping under intra-deliverable concurrency.** Domains build concurrently but the outcome must land as one commit with consistent progress/deviation logs. This is simpler than concurrent *separate* commits (which we rejected) — there is still exactly one commit per deliverable — but the concurrent build must be isolated per domain and re-joined into one working tree before the single commit. The isolation pattern already used by the `learnings-benchmark` skill is the reference. Owner: execution-plan + runtime-risk reviewer.
- **Background counters are largely unaffected — confirm.** The deterministic hook counters (edit/command counts, chapter rotation) read project history sequentially and assume one commit at a time. Because a macro-deliverable still produces exactly one commit, this model should hold; the build must ensure no intermediate per-domain commits leak onto the main branch. Owner: execution-plan + runtime-risk reviewer.
- **No mid-run pause + no survival across restart.** The workflow runs in the background, can't pause for an operator gate mid-run, and doesn't survive a Claude Code restart. Mitigated by design: automatable validation runs inside the workflow, manual preview is handed back afterward, and an interrupted run falls back to sequential build on resume. Owner: execution-plan.
- **Contract-seam collision.** The integration point (the contract between domains) is where concurrent domain builds would conflict. Building the seam first, then fanning out the domains against the agreed contract, is the mitigation. Owner: execution-plan.
- **Research-preview dependency.** The parallel capability is new and version-gated; behavior may change. Mitigated by the graceful-fallback HARD DECISION.
- **Validation-approach memory is two-sided.** Recall only works if the approach was captured greppably; existing per-feature validation records pre-date the captured approach field, so recall must tolerate their absence. The capture side is a schema addition to the per-feature validation record — must stay backward-compatible with old records. Owner: execution-plan + executing-plans; `tests` reviewer consumes recalled approaches as the adequacy benchmark.
- **Recall precision.** "Similar past work" matching can mis-fire (surface an irrelevant prior approach). Kept low-risk by making recall advisory (it informs, never dictates, the method choice) and read-only. Owner: execution-plan.

## 7. References & revision log

**Document references:**
- Architecture: the skill's own `SKILL.md` files (registry: `review`, `executing-plans`, `execution-plan`, `simplify`)
- UX/PMF: n/a — no UI
- Security policy: none
- Schema/ERD: n/a — no data storage

**Affected skill files (internal plumbing, not PM-facing):**
- `plugins/strategic-implementation/skills/{executing-plans,execution-plan,learnings-benchmark}/SKILL.md`
- `plugins/strategic-implementation/agents/tests.md` (macro-deliverable validation rule; consume recalled validation approaches)
- `plugins/strategic-implementation/hooks/hooks.json`
- `plugins/strategic-implementation/scripts/hook-bash-counter.sh`, `hook-stop-orchestrator.sh`

**Integration-risk dependency:** the Workflow capability (Claude Opus 4.8 / Claude Code v2.1.154+) — research-preview, version-gated, disable-able, no mid-run input, non-session-surviving.

**Revision log:**
- v0.1 · 2026-05-31 · initial draft
- v0.2 · 2026-05-31 · Dropped reviewer-parallelism (old D1). Replaced inter-deliverable parallel groups with intra-deliverable cross-domain "macro-deliverable" execution: one user-validateable outcome, domains built concurrently in one workflow, one atomic commit. Added contract-seam-first ordering, automatable-validation-only with manual-preview handback, and the one-commit blast-radius tradeoff. Deleted the plan-mode open question (no workflow runs inside plan mode anymore).
- v0.4 · 2026-06-01 · Post-execution headline alignment (PM-requested). Softened §1 working-backwards and §3 success-signal to lead with the structural value (one cross-domain unit + honest e2e validation + captured validation approach) and recast concurrency-in-`/workflows` + wall-clock as an observational follow-up, not a gated acceptance step — matching the execution-time decision to defer the live concurrency proof to a post-hoc fresh-session trial (DEV-002). No deliverable or HARD DECISION changed.
- v0.3 · 2026-05-31 · Added D6 (macro-deliverable-aware validation review — `tests` reviewer holds a macro-deliverable to proving the integrated cross-domain outcome end-to-end) and D7 (validation-approach memory: capture the approach used + recall it on later similar planning, scoped to cross-domain / integration-sensitive work). Added two HARD DECISIONS (macro validation bar; memory scope) and the quiet-degrade failure mode. Added two-sided-memory and recall-precision risks. Explicitly scoped a general memory subsystem OUT.
