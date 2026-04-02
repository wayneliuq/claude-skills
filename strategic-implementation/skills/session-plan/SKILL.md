---
name: session-plan
description: Builds a concrete execution plan for one session from the approved implementation guide. Runs the full agent panel against it, synthesizes findings, presents for approval, then auto-invokes executing-plans. Separately invoked by the user — not triggered automatically.
---

# Session Plan

This skill plans and reviews **one session** from an approved sessionized implementation plan. It is invoked separately by the user — not automatically after implementation plan approval.

You receive:
- The approved sessionized implementation plan
- The user's indication of which session to plan (e.g., "plan session 2" or "plan the authentication session")

---

## Step 1 — Identify the Session

Confirm which session the user wants to plan. If ambiguous, list the sessions from the implementation plan and ask. Do not assume.

Verify pre-conditions:
- All sessions that this session depends on (per the Session Order & Dependencies section) are marked complete, or the user explicitly acknowledges they are proceeding out of order.
- If a required prior session is incomplete: surface this and ask how to proceed. Do not block unconditionally — the user may have a valid reason — but make the dependency explicit.

---

## Step 2 — Build the Session Plan

Draft the session plan using the template below.

**Authoring rules:**
1. **One session only.** Do not plan beyond this session. Do not include steps from future sessions.
2. **Goal must match the implementation plan verbatim.** Copy it exactly — do not rephrase.
3. **Steps must be concrete.** Each step names the exact file(s) and what to write, change, or delete. "Implement the feature" is not a step.
4. **Deliverables & Tests are copied from the implementation plan** and expanded with execution-specific detail — the exact command to run, the exact behavior to observe, or the exact check to perform.
5. **≤ ~1000 LOC.** If the session as defined in the implementation plan would exceed this, split it and note the split to the user before proceeding.
6. **Pre-conditions must be checkable.** Every pre-condition item must be something that can be verified before starting — not "understand the architecture" but "architecture doc available at [path]."

**Template:**

```markdown
## Session Plan: [Session Name]
_Implements: Implementation Plan § Session N_
_Date: [date]_

### Goal
(one sentence — copied verbatim from the implementation plan)

### Pre-conditions
- [ ] Prior sessions complete: [list, or "none — this is Session 1"]
- [ ] Docs available: architecture doc [path], implementation plan [path], UX/PMF doc [path if applicable]
- [ ] [Any specific pre-condition: environment running, dependency installed, etc.]

### Steps
1. [Concrete step]
   - Files: [exact file paths]
   - What: [what to write, add, change, or delete — specific enough to execute without guessing]
2. ...

### Deliverables & Tests
- [ ] Deliverable: [what is produced]
  Test: [exact command, behavior to observe, or check to perform]
- [ ] ...

### Constraints
- Target: ≤ ~1000 LOC edited or written this session
- Do not implement anything from Session [N+1] or later
- Flag any unexpected scope expansion to user before proceeding
- If a step reveals a pre-condition is not met: stop and surface to user before continuing
```

---

## Step 3 — Run Agent Panel

Launch all always-on agents in parallel. Each receives **both the session plan AND the full implementation plan** as input. Agents must check alignment between the two — the session plan must not contradict or diverge from the implementation plan.

**Always launch:**
- `/Users/qiangliu/Documents/Development/claude-skills/strategic-implementation/agents/10k-foot.md`
- `/Users/qiangliu/Documents/Development/claude-skills/strategic-implementation/agents/technical-expert.md`
- `/Users/qiangliu/Documents/Development/claude-skills/strategic-implementation/agents/scope-limiter.md`
- `/Users/qiangliu/Documents/Development/claude-skills/strategic-implementation/agents/future-proofing.md`
- `/Users/qiangliu/Documents/Development/claude-skills/strategic-implementation/agents/security.md`
- `/Users/qiangliu/Documents/Development/claude-skills/strategic-implementation/agents/data-model.md`
- `/Users/qiangliu/Documents/Development/claude-skills/strategic-implementation/agents/api-contract.md`
- `/Users/qiangliu/Documents/Development/claude-skills/strategic-implementation/agents/test-coverage.md`
- `/Users/qiangliu/Documents/Development/claude-skills/strategic-implementation/agents/performance.md`
- `/Users/qiangliu/Documents/Development/claude-skills/strategic-implementation/agents/dependency.md`

**Launch conditionally (if session involves UI, UX, or front-end):**
- `/Users/qiangliu/Documents/Development/claude-skills/strategic-implementation/agents/frontend-engineer.md`

Wait for all agents to return.

---

## Step 4 — Synthesize Agent Outputs

Apply standard synthesis rules:

1. Collect all FLAGS and RECOMMENDATIONS.
2. Discard low-utility suggestions — vague, speculative, or not actionable against this specific session.
3. Reconcile conflicts — choose the more conservative or correct position.
4. Surface any BLOCK statuses to the user immediately.
5. If FLAGS or RECOMMENDATIONS require user decisions → surface with a recommendation and rationale. Wait for response.
6. Apply the final patch list to the session plan.
7. Consistency check: do the session plan's steps, deliverables, and files all align with the implementation plan for this session?

---

## Step 5 — Present for Approval

Present the final session plan to the user.

If the user requests changes: apply them, re-run consistency check, re-present. Do not re-run the full agent panel unless changes are substantial (a step is added that introduces new files or libraries not in the original plan).

**Once the user approves:**

Announce: "Session plan approved. Starting execution."

Automatically invoke `superpowers:executing-plans`. No manual step needed.
