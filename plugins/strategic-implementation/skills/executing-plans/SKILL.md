---
name: executing-plans
description: Executes an approved v2 execution plan, one deliverable at a time. Deliverable-gated (not session-based). Per-deliverable pre-flight env check, validation per declared method (preview / cli / tdd / post-hoc), atomic commit per deliverable, deviation log. Invokes post-execution for regression-check on completion.
---

# executing-plans

Executes one approved execution plan end-to-end. v2 is **deliverable-gated** — each deliverable is an atomic unit with its own validation method declared at plan time.

You receive:
- Execution plan path (`<feature-folder>/execution-plan.md`)
- Feature folder path
- Autonomy level (`supervised` | `auto` | `yolo`)

Announce at start: "Starting execution: <feature slug>."

---

## Step 0 — Branch check

Run `git branch --show-current`. If result is `main` or `master`:

> ⚠️ **Warning: you are on `<branch>`.** Execution directly on main/master is strongly discouraged. Confirm to proceed, or switch to a feature branch first.

In `supervised` or `auto`: wait for explicit confirmation.
In `yolo`: proceed but log a `branch-risk` deviation.

---

## Step 1 — Read plan

Read `execution-plan.md` fully. Extract: deliverables, DAG order, parallel groups.

Initialize `validation-log.md` at `<feature-folder>/validation-log.md` with header:

```markdown
# Validation log
_Feature: <slug> · Started: <date> · Autonomy: <level>_
```

Initialize deviation counter `DEV-001`.

---

## Step 2 — Execute DAG

For each deliverable group in DAG order (parallel groups run concurrently, sequential groups run in order):

### Step 2a — Pre-flight env check

Before building the deliverable, verify the prerequisites for its validation method:

- **`preview`:** Claude Code preview tool available; dev server startable. If not available: apply preview-unavailable fallback (below).
- **`cli`:** the CLI command runnable; required binaries in PATH.
- **`tdd`:** test runner available; baseline suite passes.
- **`post-hoc`:** no automated pre-check; note manual validation required.

If pre-flight fails: log a `blocker` deviation and stop. Surface to PM with what's missing.

### Preview-unavailable fallback

If `preview` pre-flight fails:
- `supervised` / `auto`: pause. Surface to PM: "Preview unavailable. Proceed with manual validation, or switch deliverable to TDD?"
- `yolo`: auto-escalate to TDD. Log an `auto-escalation` deviation. Write a minimal acceptance test before building.

### Step 2b — Build

Implement the deliverable per its steps. Rules:

- **Only files named in the deliverable.** Unrelated touches = deviation.
- **TDD where declared.** If validation is `tdd`: test first, then implementation, then test passes.
- **Code discipline:**
  - Write the minimum that passes validation. No speculative abstractions.
  - Match existing conventions (style, naming, error handling).
  - Clean up only code YOUR changes made unused — leave pre-existing dead code alone.
  - Do not "improve" adjacent code.

### Step 2c — Validate

Run the declared validation:
- **preview:** start preview, capture the observable behavior, confirm against the deliverable's expected behavior.
- **cli:** run the command, assert expected output.
- **tdd:** run the test written in 2b; must pass. Also run the full suite — no new failures.
- **post-hoc:** surface to PM with what to inspect. In `yolo`, skip inspection, log `yolo-skip`.

If validation fails: apply **Failure Protocol** below.

### Step 2d — Commit

Atomic commit per deliverable:

```
D<n>: <one-sentence outcome>
```

Example: `D3: add product-brief revision loop`.

Only the files named in this deliverable are staged.

### Step 2e — Mark complete

In `execution-plan.md`, update deliverable status: `pending` → `complete`.

---

## Failure Protocol

On validation failure:

**Classify:**
- **Determinate** (clear root cause): fix → re-validate. If that fails, treat as assumption-based.
- **Assumption-based** (must infer): state the assumption explicitly before any fix.

**Attempt 1:**
1. State assumption / root cause in one sentence.
2. Fix. Re-validate.
3. Success → log `retry` deviation, continue.
4. Failure → revert changes. Confirm baseline restored.

**Re-examine:**
- List all assumptions. Rate each `high` / `medium` / `low`.
- If all `high`: **EXIT** (see Exit Report).
- Else: revise the lowest-confidence assumption.

**Attempt 2** (only if revision yields a distinct fix):
1. State revised assumption.
2. Fix. Re-validate.
3. Success → log deviation, continue.
4. Failure → revert. **EXIT.**

### Exit Report

```
## Execution Blocked

**Deliverable:** D<n> — <name>
**Failure:** <exact error / test output>

**Confirmed facts:**
- ...

**Assumptions held:**
- <assumption> — confidence: high/med/low
- ...

**Attempts:**
1. <what> → <outcome>
2. <what> → <outcome> (if applicable)

**Most suspect assumption:** <one sentence>

**Blocked on:** <what PM input or external info is needed>

All failed-attempt changes reverted. Working tree at baseline.
```

Do not mark complete. Do not proceed to next deliverable. Await PM direction.

---

## Deviation logging

A deviation exists on any of: blocker, retry, user-correction, reversal, ambiguity-decision, auto-escalation, yolo-skip, branch-risk.

Append to `validation-log.md`:

```markdown
## DEV-NNN
**Type:** blocker | retry | user-correction | reversal | ambiguity-decision | auto-escalation | yolo-skip | branch-risk
**Deliverable:** D<n>
**Plan said:** <verbatim>
**Actually:** <what happened>
**Resolution:** <how resolved>
**Downstream impact?** yes | no — <if yes: one sentence on what changes for later deliverables>
**Agent category:** alignment | boundaries | runtime-risk | tests | frontend | technical | simplify
```

If `downstream impact: yes` and a later deliverable is affected: prepend `⚠️ REVISION NEEDED — <one sentence>` to that deliverable's block in `execution-plan.md`. Surface flagged deliverables to the PM before starting them.

---

## Step 3 — All-deliverables checkpoint

When all deliverables are marked complete:

1. Announce: "All deliverables complete. Running regression check."
2. Invoke `strategic-implementation:post-execution` in `regression-check` mode with the feature folder path.
3. `post-execution` writes `post-execution-report.md` and reports back.
4. If the report status is `PASS`: announce feature complete.
5. If `FLAG` or `BLOCK`: surface to PM; do not declare complete until resolved.

### Learnings trigger

If `validation-log.md` has ≥2 meaningful deviations (judgment — typo-fixes don't count), offer the PM:

> "N meaningful deviations logged. Run learnings synthesis? (yes/skip)"

On yes: invoke `post-execution` in `learnings-synthesis` mode.

---

## Constraints

- No execution on `main`/`master` without explicit consent.
- No deliverable skipped without explicit PM decision.
- One commit per deliverable. No batching, no amending prior deliverable commits.
- No LOC budget — fitness is the gate, not size.
- Deviation log is append-only. Never rewrite.
- Hard decisions in the brief and plan are immutable during execution.
