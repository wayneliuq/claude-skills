---
name: execution-plan
description: Drafts the execution plan for an approved product brief inside Claude Code plan mode, invokes the review skill to critique the draft, patches the plan with review findings, and exits plan mode on PM approval. The execution plan — not the brief — is what the agent panel reviews.
---

# execution-plan

You convert an approved product brief into a concrete, file-level execution plan. The plan is drafted, reviewed, and approved inside **Claude Code plan mode** — plan mode's native UI is the approval gate, and Claude Code's optimized plan-mode prompting runs implicitly.

You receive:
- Brief path (`.../product-brief_<slug>.md`)
- Feature folder path
- Integration-risk dependencies (from clarify; may be empty)
- Autonomy level (`supervised` | `auto` | `yolo`)

---

## Step 1 — Enter plan mode

Your **first tool call** is `EnterPlanMode`. Do not do any work before entering plan mode — subsequent work benefits from plan mode's prompting.

If the environment does not support `EnterPlanMode` in this context, fall back: draft outside plan mode, but still present the final plan as the approval gate (see Step 5 fallback).

---

## Step 2 — Read brief + survey repo

Inside plan mode:

1. Read the brief end-to-end. Extract: deliverables (D1…Dn), acceptance criteria, scope boundary, hard decisions, document references.
2. For each deliverable, identify the concrete files likely to change. Use **Glob** and **Grep** to verify file paths exist before citing them. Unverified paths get `[PATH NOT FOUND]` annotations.
3. **Library-lifecycle doc pass.** For each integration-risk dependency from clarify, locate the canonical persistence / lifecycle doc (project README, vendor docs, RFC, or in-repo notes). Read the relevant section. Capture: what state persists across what boundaries (per-connection / per-session / per-process / per-deployment), known gotchas, and the doc URL/path. Time-box: aim for 15–30 minutes total across all libraries; if a library has no good docs, note that explicitly. Empty audit is acceptable only if clarify declared `none`.
4. Load `docs/strategic-implementation/project-learnings.md` if it exists. Filter entries for relevance to this brief's deliverables. Inject matching entries when invoking `review`.

---

## Step 3 — Draft execution plan

Draft the plan using the template below. The plan is structured as a **DAG of deliverables**, not a sequence of sessions.

```markdown
# Execution Plan: <feature name>
_Implements: product-brief_<slug>.md · Date: <date>_

## Context
<2–3 sentences restating what this plan delivers, tying each deliverable back to the brief.>

## Library lifecycle audit
<One subsection per integration-risk dependency from clarify. Omit the section entirely only if clarify declared `none`. A generic "we'll handle errors gracefully" is not an audit — concrete persistence/scope semantics are.>

### <library / runtime / external system name>
- **State that persists:** <what state, scoped to what boundary — e.g. "TEMP TABLE rows live for the lifetime of one DB connection; dropped on disconnect">
- **Quirks / gotchas:** <known surprises — e.g. "persisted DB on disk and runtime VFS are not auto-synced; explicit flush required">
- **Doc consulted:** <URL or in-repo path>

## Deliverables (DAG)

### D1 — <name>
- **Integration-risk class:** <a | b | c | d>
  - `a` — depends on a third-party runtime / SDK with non-trivial lifecycle
  - `b` — depends on real browser / network behavior
  - `c` — depends on cross-component reactive state coordination
  - `d` — none of the above
- **Validation:** <preview | cli | tdd | integration-test | post-hoc> — <exact command / exact behavior to observe / exact test to write>
- **Files:** <specific paths; use [PATH NOT FOUND] if unverified>
- **Steps:** <numbered; each names file(s) and what to write/change/delete>
- **Deps:** <other D-ids, or "none">
- **Pre-flight env check:** <what must be available to run the validation — e.g. dev server, DB migration applied, credentials present>
- **Consumer audit:** <required iff this deliverable changes a data shape — interface / type / schema / payload / return type / function signature. Otherwise: "n/a — no shape change.">
  - <consumer file:symbol> — `updated-in-this-deliverable` | `updated-in-D<n>` | `unaffected-because-<reason>` | `explicit-skip-because-<reason>`
  - ...

### D2 — <name>
...

## Parallel groups & order
<textual DAG — which groups run in parallel, which are sequential>

## Reused existing patterns
<bulleted — point to existing repo primitives being reused. Prevents duplicate abstractions.>

## Risks & contingencies
<bulleted — what could go wrong, and the fallback>

## Out of scope for this plan
<bulleted — explicit exclusions from the brief's scope boundary>
```

### Authoring rules

1. **One deliverable = one user-observable outcome.** Do not create deliverables for "internal plumbing" unless the plumbing is itself a validation gate.
2. **No LOC budgets.** Size is not a gate in v2. Fitness is a gate.
3. **Validation method honesty.** If the brief claims `preview` validation but the deliverable is invisible in a screenshot, escalate the deliverable to TDD and note it.
4. **Preview-unavailable fallback.** For `preview`-validated deliverables: in `supervised`/`auto`, pause for PM manual validation if the preview tool can't run; in `yolo`, auto-escalate to TDD and proceed.
5. **Verify paths.** Every file path must be confirmed via Glob before the draft is presented for review.
6. **Reuse before creating.** Grep for existing primitives; cite them in "Reused existing patterns."
7. **Validation honesty per integration-risk class.** Class `a`/`b`/`c` deliverables MUST declare validation as `integration-test`, `preview`, or `post-hoc`. They MUST NOT declare `tdd` if the proposed test would mock the very dependency the deliverable's correctness depends on. Class `d` may use any method. A green unit-test suite that mocks the integration point is not validation — it is orthogonal-to-correctness coverage.
8. **Consumer audit on shape change.** Any deliverable that changes a data shape (interface / type / schema / payload / return type / function signature) MUST grep its consumers and list every one with a status (`updated-in-this-deliverable`, `updated-in-D<n>`, `unaffected-because-<reason>`, `explicit-skip-because-<reason>`). Hand-wavy enumeration is rejected by review.

---

## Step 4 — Invoke review

Still inside plan mode, invoke `strategic-implementation:review` with:
- The full plan text
- The brief path
- The document reference locations from the brief
- The filtered project-learnings block (if any)
- Autonomy level

The `review` skill runs tiered: `alignment` + `simplify` first, then specialists on flags. It returns a consolidated JSON patch list and status.

### Handling review output

- **BLOCK:** Surface the block to the PM inside plan mode. Do not patch. Ask: "resolve by revising brief, or override?"
- **FLAGs + RECOMMENDATIONs:** Apply high-severity patches silently. Present medium/low patches as a numbered list — PM can accept all / reject all / pick.
- **ALTERNATIVE (from simplify):** Present the alternative path. Ask PM whether to rewrite or proceed.

After patches applied, re-run the consistency check (every acceptance criterion still covered; no orphan deliverables; no broken DAG edges).

---

## Step 5 — Present for approval

Present the patched plan via plan mode's native UI. The plan must end with an explicit final step so that, if the PM approves via plan-mode's button, the hand-off is committed:

```
Final steps on approval:
1. Save execution plan → <feature-folder>/execution-plan.md
2. Exit plan mode
3. Invoke strategic-implementation:executing-plans
   - Execution plan path: <feature-folder>/execution-plan.md
   - Feature folder path: <feature-folder>/
   - Autonomy level: <level>
```

### Fallback (plan mode not entered)

If Step 1's `EnterPlanMode` call was not supported, present the plan as a normal inline message with this exact trigger callout:

> **Ready to execute.** Reply `go`, `execute`, or `start` to begin. Describe changes to revise.

---

## Step 6 — On approval

1. Save to `<feature-folder>/execution-plan.md`.
2. Call `ExitPlanMode` (if in plan mode).
3. Invoke `strategic-implementation:executing-plans`, passing execution plan path, feature folder path, autonomy level.

---

## Revision loop

If the PM rejects or requests changes: stay in plan mode, apply changes, re-run consistency check, re-present. Only re-invoke `review` if the changes are substantial (new deliverable added, dep introduced, hard decision touched).
