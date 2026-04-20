# strategic-implementation

A Claude Code plugin that runs PM-described work through a lean planning-to-execution pipeline built for Opus 4.7. One PM-approvable artifact (the product brief), one plan-mode review gate (the execution plan), and deliverable-gated execution with per-deliverable validation — no sessions, no LOC budgets.

**Version:** 2.0.0

---

## What it does

Takes a PM description of work → produces an approved product brief → drafts and reviews an execution plan inside Claude Code plan mode → executes deliverable-by-deliverable with the validation method declared at brief time → runs a regression check at the end.

v2 is a ground-up redesign targeting ≥70% review-phase token reduction vs. v1, higher autonomy for Opus 4.7, and a workflow legible to a non-coder PM.

---

## Workflow at a glance

```
/strategic-implementation
  │
  ├─ Execution plan approved?   → invoke executing-plans directly
  ├─ Brief drafted, not planned? → resume at execution-plan
  └─ Nothing yet?                → full workflow ↓
  │
  ▼
[clarify] — one-pass: assumptions, ≤3 questions, ALL doc references, autonomy level
  │
  ▼
Scope assessment
  ├─ One-sentence, one-area, no new patterns → fast-path
  └─ Otherwise ↓
  │
  ▼
[product-brief-drafter] — draft `product-brief_<slug>.md`
  │
  ▼
PM revision loop (inline `<!-- pm: ... -->` markers) ⇄ [product-brief-drafter] revise mode
  │
  ▼  (PM approves the brief)
[execution-plan]
  ├─ EnterPlanMode (plan mode is BOTH drafting env AND approval gate)
  ├─ Survey repo with Glob/Grep; draft deliverable DAG with declared validation per deliverable
  ├─ Invoke [review] inside plan mode
  │   ├─ Pre-filter specialists by domain triggers
  │   ├─ [alignment] + [simplify] in parallel (generalist tier)
  │   └─ [boundaries] / [runtime-risk] / [tests] / [frontend-engineer] only on flag (specialist tier)
  ├─ Apply patches; re-check consistency
  └─ Present via plan-mode UI; on approve → save + ExitPlanMode + invoke executing-plans
  │
  ▼
[executing-plans] — deliverable-gated
  ├─ Per-deliverable pre-flight env check for declared validation
  ├─ Build → validate (preview | cli | tdd | post-hoc) → atomic commit
  ├─ Deviation log: `validation-log.md`
  ├─ Preview-unavailable fallback: pause (supervised/auto) or auto-TDD (yolo)
  └─ On final deliverable complete → [post-execution: regression-check]
  │
  ▼
[post-execution]
  ├─ regression-check — modified-file discovery, cross-contamination, suite run, acceptance-test authoring
  ├─ triage (on PM-reported issue) — TDD fix, log to validation-log
  └─ learnings-synthesis (when validation-log has ≥2 meaningful deviations)

[prune-tests] — explicit, PM-invoked. Gated by `.strategic-implementation/ga-state.json`.
```

---

## Artifacts

Per feature, under `docs/strategic-implementation/<YYYY-MM-DD>-<slug>/`:

- `product-brief_<slug>.md` — PM-approvable. The only document the PM signs off on.
- `execution-plan.md` — agent-reviewed. Approved inside plan mode.
- `validation-log.md` — deviations, appended during execution.
- `post-execution-report.md` — regression-check output.

Shared: `docs/strategic-implementation/project-learnings.md` (appended by post-execution learnings-synthesis).

Repo-level GA state: `.strategic-implementation/ga-state.json` (see `docs/ga-state-schema.md`).

---

## Skills (8)

| Skill | Role |
|---|---|
| `strategic-implementation` | Orchestrator. Routes clarify → brief → execution-plan. Ends when execution starts. |
| `clarify` | One-pass entry gate. Collects all doc refs + autonomy level upfront. |
| `product-brief-drafter` | Produces `product-brief_<slug>.md` in draft or revise mode. Single PM-approvable artifact. |
| `execution-plan` | Enters plan mode; drafts the deliverable DAG; invokes review inside plan mode; patches; exits on approval. |
| `review` | Tiered review: pre-filter + generalist (alignment + simplify) + specialists on flag. |
| `executing-plans` | Deliverable-gated execution. Pre-flight env check, validation per declared method, atomic commit per deliverable, deviation log. |
| `post-execution` | Three modes: `regression-check`, `triage`, `learnings-synthesis`. |
| `prune-tests` | PM-invoked. GA-state-gated. Per-batch confirmation. Removes pre-GA unit tests. |

---

## Agents (7)

All agents emit JSON (`{status, flags, recommendations}`), cap at ~1500 tokens each, and target ≤120 lines of prompt.

**Generalist tier — always runs:**
- `alignment` — brief fit + architecture alignment + PMF + plan-level future-proofing. Routes specialists.
- `simplify` — single pass for a shorter path to the brief's acceptance criteria.

**Specialist tier — runs only on flag or pre-filter match:**
- `boundaries` — security + data-model + api-contract merged.
- `runtime-risk` — performance + dependency merged.
- `tests` — validation-method adequacy against v2's goal-level acceptance model (not line-level coverage).
- `technical-expert` — stack pitfalls + step-ordering errors.
- `frontend-engineer` — UI + UX + a11y + preview-fit (absorbs v1 ux-pmf-review). Contextual — only if UI surface exists.

---

## Autonomy levels

| Level | Behavior |
|---|---|
| `supervised` | Pause at every gate for PM review. |
| `auto` (default) | Pause only on FLAG/BLOCK and at PM-approval gates (brief, execution plan). |
| `yolo` | Pause only on BLOCK. Preview-unavailable auto-escalates to TDD. |

Set at `clarify` time, carried through the workflow.

---

## Validation taxonomy

Each deliverable declares its validation method at brief time:

| Method | When |
|---|---|
| `preview` | Visually observable via Claude Code preview tool |
| `cli` | A command whose output proves the behavior |
| `tdd` | Acceptance test written before implementation |
| `post-hoc` | Manual PM inspection (rare; reserved for things none of the above fit) |

The `tests` agent flags honesty of method choice; `executing-plans` pre-flights the method's prerequisites before building.

---

## GA state & prune-tests

Pre-GA, v2 intentionally favors goal-level acceptance tests over line-level unit tests. At GA prep, the PM runs `prune-tests` to remove the sparse line-level tests that accumulated.

Gated by `<repo>/.strategic-implementation/ga-state.json`:
- `pre-ga` / `ga-prep` → prune runs, per-batch PM confirmation, separate commits.
- `ga` → prune refuses; post-GA deletion requires its own brief.

Schema: see `docs/ga-state-schema.md`.

---

## Token reduction (vs. v1.4.0)

v2 targets ≥70% review-phase reduction via:

- Single PM artifact (brief) vs. v1's spec + sessionized-guide + per-session-plans.
- Plan-mode hidden prompting replaces v1's hand-authored drafter prompts.
- Tiered review (generalist → specialists on flag) vs. v1's always-parallel 10-agent panel.
- Panel consolidation: 10 always-on → 4 always-eligible + contextual.
- JSON output contracts with `max_tokens: 1500` hints vs. v1's freeform prose.
- Merged post-execution skills replace v1's bug-fix + post-mortem + end-of-implementation.
- Dropped sessionization, LOC gates, revision log, per-step commits, double agent panels.

---

## Feature folder layout

```
docs/strategic-implementation/2026-04-20-auth-redesign/
├── product-brief_auth-redesign.md
├── execution-plan.md
├── validation-log.md
└── post-execution-report.md
```

Plus `docs/strategic-implementation/project-learnings.md` at the root.
