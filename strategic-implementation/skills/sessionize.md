---
name: sessionize
description: Converts an approved specification document into a sessionized implementation plan. Runs the full 10-agent review on the complete plan in a single round, synthesizes findings, and presents the plan for user approval.
---

# Sessionize

You are converting a finalized, user-approved specification document into a sessionized implementation plan — the concrete breakdown of what gets built in which order, used to drive session planning and execution.

This skill owns the full agent review round for the implementation plan. Agents do not run on the spec document — only on the sessionized plan.

You receive: the finalized specification document.

---

## Step 1 — Read the Spec

Read the full specification document. Extract:
- **What is being built** (Section 2 and Section 4)
- **Success criteria** (Section 3)
- **Scope boundary** (Section 5) — sessions must not cross these exclusions
- **Hard decisions** (Section 6, marked with `[HARD DECISION]`) — these are fixed; sessions must implement them as specified
- **Open decisions** (Section 6) — if any remain, surface them to the user before sessionizing. Do not build sessions around unresolved decisions.
- **Risks and unknowns** (Section 7) — high-risk items should be addressed in earlier sessions where possible, to fail fast
- **Revision log** (bottom of doc) — review for any patterns that might affect session design

**If there are unresolved open decisions in Section 6:** stop. Surface them to the user and ask for resolution before proceeding. Sessionizing around open decisions produces a plan that cannot be executed.

---

## Step 2 — Collect Document References

Before running agents, ask the user for two document locations if not already provided:

1. **Security policy document** — "Is there a security policy document for this project? If so, where is it?"
2. **Schema design / ERD** — "Is there a schema design document, entity-relationship diagram, or data dictionary? If so, where is it?"

Only ask for what's relevant to the change (skip schema if no data storage is involved). Pass these locations to the security and data-model agents. If none exists, pass that information so the agents can flag it correctly.

---

## Step 3 — Draft Sessions

Break the specification into sessions using the implementation guide template (`skills/implementation-guide.md`).

Rules for session design:
- **One clear goal per session.** A session's goal is one sentence. If you can't state it in one sentence, the session is doing too much.
- **Each session is self-contained.** A developer reading only that session block should know what to build, what files to touch, and how to verify it — without needing to read other sessions.
- **Fail-fast ordering.** Sessions that validate the riskiest or most uncertain parts of the plan come first where possible. Do not build a large foundation on top of an unvalidated assumption.
- **Hard decisions are locked.** Sessions must implement hard decisions as specified. Do not design sessions that would require reversing them.
- **Size constraint.** S = <200 LOC, M = 200–500 LOC, L = 500–1000 LOC. Any session estimated larger than L must be split. When in doubt, split — it is easier to merge sessions than to discover mid-execution that a session is too large.
- **Success criteria coverage.** Every success criterion from Section 3 of the spec must be verifiable by at least one session's deliverables. Check this explicitly before moving on.

For each session, draft:
- Goal (one sentence)
- Deliverables & Tests (each deliverable paired with its verification method)
- Files affected (specific file paths)
- Docs to update
- Estimated size (S / M / L)

Leave "Session Order & Dependencies" blank — the scope-limiter generates this.

---

## Step 4 — Run Scope Limiter

Run `agents/scope-limiter.md` with the drafted sessions as input.

The scope-limiter will:
- Review sessions for scope creep and sizing
- Recommend any splits or merges
- Generate the session order and dependency map

Apply the scope-limiter's session order and dependency map to the plan. Address any sizing flags (split sessions that exceed L) before proceeding to the full agent panel.

---

## Step 5 — Run Full Agent Panel

Launch all always-on agents in parallel using the Agent tool. Each receives the full sessionized plan as input.

**Always launch:**
- `agents/10k-foot.md`
- `agents/technical-expert.md`
- `agents/future-proofing.md`
- `agents/security.md` (pass: security policy doc location from Step 2)
- `agents/data-model.md` (pass: schema doc location from Step 2)
- `agents/api-contract.md`
- `agents/test-coverage.md`
- `agents/performance.md`
- `agents/dependency.md`

**Launch conditionally (if plan involves UI, UX, or front-end):**
- `agents/frontend-engineer.md`

Note: the scope-limiter already ran in Step 4 and its output is incorporated. Do not re-run it here.

Wait for all agents to return.

---

## Step 6 — Synthesize Agent Outputs

Read all agent outputs. Apply the standard synthesis rules:

1. Collect all FLAGS and RECOMMENDATIONS.
2. Discard low-utility suggestions — vague, speculative, or not actionable against this specific plan.
3. Reconcile conflicts between agents — choose the more conservative or correct position; note the conflict.
4. Surface any BLOCK statuses to the user immediately. A BLOCK must be resolved before proceeding.
5. If FLAGS or RECOMMENDATIONS require user decisions → surface them WITH a recommendation and rationale. Wait for response.
6. Apply the final patch list to the sessionized plan.
7. Run a final consistency check: goal, deliverables, and files consistent across sessions; naming consistent throughout; no orphan references.

---

## Step 7 — Present for Approval

Present the full sessionized implementation plan to the user.

If the user requests changes: apply them, re-run the consistency check, re-present. Do not re-run the full agent panel unless the changes are substantial (use judgment — substantial means a session is added, removed, or a hard decision is reversed).

Once approved:

Present the following:

```
Implementation plan approved.

Sessions:
[numbered list of session names and one-sentence goals]

When you're ready to plan the first session for execution, say "plan session [N]" or invoke the session-plan skill.
```

Do not automatically proceed to session planning. The user triggers that separately.
