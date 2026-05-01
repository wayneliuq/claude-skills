---
name: strategic-implementation
description: Outcome-first orchestrator. Routes PM-described work outside-in — clarify → product brief → optional UI mockup → execution plan (in plan mode) → deliverable-gated execution → post-execution. Single-artifact approval (the brief). Plan mode is both drafting environment and approval gate for the execution plan.
---

# strategic-implementation

Outcome-first planning-to-execution orchestrator. Every feature starts from the user-observable outcome and works backwards to implementation. The PM approves one artifact (the product brief). The execution plan is reviewed and approved inside Claude Code plan mode. Execution is deliverable-gated — no sessions, no LOC budgets.

---

## Validation honesty principle

**A green test suite is not a proxy for correctness.** A 100% passing run validates only the contracts your tests describe. If your tests systematically mock the integration points where your code actually lives — third-party runtimes, real network/browser behavior, cross-component reactive state — the suite is measuring orthogonal-to-correctness coverage. Validation methods must be honest about what they exercise; mocks at integration-risk seams require manual or integration-test validation as a backstop.

This principle motivates three gates baked into the workflow: integration-risk dependency collection (in `clarify`), library-lifecycle audit and per-deliverable integration-risk classification (in `execution-plan`), and consumer-audit on shape changes (in `execution-plan` + `executing-plans`). Reviewers (`tests`, `runtime-risk`, `alignment`) flag when these are missing or hand-wavy.

---

## Entry: three paths

Ask: **"Where are you in the process for this work?"**

- **Execution plan already approved** → invoke `strategic-implementation:executing-plans` directly, passing the plan path and feature folder.
- **Product brief drafted, not yet planned** → continue to Step 4 (execution-plan) with the existing brief.
- **Nothing yet** → Step 1.

---

## Step 1 — Clarify

Announce: "Starting clarification."
Invoke `strategic-implementation:clarify`.

Clarify collects in a single pass: assumptions, approach-changing questions, ALL document references (architecture, UX/PMF, security, schema — as applicable), and the autonomy level.

Store everything clarify returns. No re-asking downstream.

---

## Step 2 — Scope assessment

After clarification, assess:

**Fast-path** (all three true):
1. Deliverable describable in one sentence
2. Change contained to one area
3. No new architectural patterns or dependencies

**If fast-path:**
1. Create `docs/strategic-implementation/<YYYY-MM-DD>-<slug>/`.
2. Write a one-page `execution-plan.md` inline (single deliverable, validation method, files).
3. Announce: "Fast-path: skipping brief. Starting execution."
4. Invoke `strategic-implementation:executing-plans` with the plan path, feature folder, autonomy level.

This skill ends.

**Otherwise:** continue to Step 3.

---

## Step 3 — Product brief

Announce: "Drafting product brief."
Invoke `strategic-implementation:product-brief-drafter` in `draft` mode with:
- Clarified request
- Document references (all of them)
- Autonomy level

The drafter writes `product-brief_<slug>.md` to a new feature folder. It returns the brief path and feature folder path.

### Revision loop

The PM reviews the brief. They can:
- Add inline `<!-- pm: ... -->` comments and reply "revise" → invoke `product-brief-drafter` in `revise` mode.
- Reply "approve" → proceed to Step 4.

Do not prompt the PM to decide — wait for their signal. The loop runs as many times as needed.

---

## Step 4 — Execution plan (plan mode)

On brief approval, announce: "Drafting execution plan in plan mode."
Invoke `strategic-implementation:execution-plan` with:
- Brief path
- Feature folder path
- Integration-risk dependencies (from clarify; may be empty)
- Autonomy level

`execution-plan` enters plan mode as its first action, drafts against the brief using live repo state, invokes `strategic-implementation:review` inside plan mode, applies review patches, and presents the plan via plan mode's native UI.

On PM approval (plan mode's approve button, or affirmative text reply): `execution-plan` saves the plan, exits plan mode, and invokes `executing-plans` itself.

This orchestrator does not re-handle execution — `execution-plan` owns the handoff.

---

## Step 5 — Execution (handled by executing-plans)

`executing-plans` runs deliverable-by-deliverable. For each deliverable:
- Pre-flight env check for the validation method
- Build
- Validate (preview / cli / tdd / post-hoc)
- Commit per deliverable (atomic)
- Log deviations to `validation-log.md`

On the final deliverable's completion, `executing-plans` invokes `strategic-implementation:post-execution` in `regression-check` mode.

---

## Autonomy semantics (apply throughout)

- `supervised`: pause at every gate for PM review (brief approval, plan approval, each deliverable).
- `auto` (default): pause only on FLAG / BLOCK and at PM-approval gates (brief, execution plan). Non-blocking steps proceed.
- `yolo`: pause only on BLOCK. Preview-unavailable auto-escalates to TDD rather than pausing.

---

## Constraints

- No code before brief approval and execution-plan approval.
- Execution plan is reviewed; brief is not (brief review is the PM's inline review).
- Plan mode is entered inside `execution-plan` — not here.
- Before invoking `product-brief-drafter`, `executing-plans`, or `post-execution`, exit plan mode if active. Never exit plan mode before invoking `execution-plan` (it enters plan mode itself).
- Hard decisions in the brief are locked; review cannot reverse them.
- `executing-plans` owns all per-deliverable flow. This skill ends when execution begins.
