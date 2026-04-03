---
name: strategic-implementation
description: Use when starting any non-trivial feature, change, or new component — before writing any code or plan. Guides clarification, architecture review, spec drafting, iterative revision, sessionization, and agent review. Session planning is a separate invocation.
---

# strategic-implementation

A structured planning workflow for software development. No code is written until a spec is approved, sessionized, and reviewed. This skill produces an approved sessionized implementation plan — session planning and execution are handled by the `strategic-implementation:session-plan` skill, invoked separately.

---

## Entry: Three Paths

Before anything else, ask:

**"Where are you in the process for this work?"**

- **Sessionized implementation plan exists:** You don't need this skill. Invoke `strategic-implementation:session-plan` directly with your plan.
- **Spec document in progress (not yet sessionized):** Ask — "Do you want to continue revising, or is it ready to sessionize?" → revision: go to Step 5 with the existing spec; sessionize: go to Step 6 with the finalized spec.
- **Nothing yet:** Proceed to Step 1 below.

---

## Step 1 — Clarify

Use the `strategic-implementation:clarify` skill.

List assumptions. Ask only what would change the approach. Wait for user confirmation before proceeding.

---

## Step 2 — Scope Assessment

After clarification, assess scope against ALL THREE criteria:

**Fast-path if all three are true:**
1. Deliverable describable in one sentence
2. Change contained to one area (one component, file group, or feature)
3. No new architectural patterns or dependencies introduced

**If fast-path:** invoke `superpowers:writing-plans`, explicitly instructing it to save the plan to `docs/strategic-implementation/YYYY-MM-DD-<feature-name>/implementation-guide.md` (derive feature name from the one-sentence description; writing-plans supports path overrides via user instruction). Then invoke `strategic-implementation:executing-plans`. This skill ends here.

**Otherwise:** continue to Step 3.

---

## Step 3 — Parallel Review: Architecture + UX/PMF

### 3a — Collect Document References First

Before launching agents, ask the user for document locations:

1. **Architecture document** — "Where is the architecture document for this project? Is it current?" (Required — architecture review will BLOCK without it)
2. **UX/PMF document** — "Is there a UX or product-market fit document for this area?" (Only ask if the change has any user-facing impact; skip for purely backend changes)

Store both locations. They are passed to their respective agents and to the reviser in Step 5 — do not re-ask for them later.

### 3b — Launch Agents in Parallel

Launch both agents in parallel using the Agent tool, passing the document locations collected above:

- `strategic-implementation:architecture-review` (pass: architecture document location)
- `strategic-implementation:ux-pmf-review` (pass: UX/PMF document location, if applicable)

Wait for both to return.

**If either returns STATUS: BLOCK:** surface the blocking issue with the agent's recommended next step. Do not proceed until resolved.

Store both outputs. They are passed silently to the drafter in Step 4 — do not present them to the user.

---

## Step 4 — Draft Specification Document

Use the `strategic-implementation:implementation-drafter` skill.

Pass:
- The clarified request
- The architecture review output
- The UX/PMF review output

The drafter produces a specification document using the 8-section framework with feedback slots. Present the completed spec to the user.

Store the feature folder path returned by implementation-drafter. Pass it to:
- implementation-reviser in Step 5 (as spec file path: `<feature-folder-path>/spec.md`)
- sessionize in Step 6
- session-plan when the user triggers session planning
Do not re-derive it from the spec title.

**If the architecture review found that the change requires new architectural components or significant adaptation that are not yet documented:**
→ Pause before presenting the spec. Inform the user: "This change requires architectural decisions not yet captured in the architecture document. Please update the architecture doc first, then we can proceed."
Do not present the spec until resolved.

---

## Step 5 — Iterative Revision

The user reviews the spec and provides feedback. When the user says "revise it" (with feedback in the message, in the feedback slots, or both):

Use the `strategic-implementation:implementation-reviser` skill.

Pass:
- The current spec document
- All user feedback
- Architecture document location (from Step 3a)
- UX/PMF document location (from Step 3a, if applicable)
- Spec file path: `<feature-folder-path>/spec.md` (from Step 4)

The reviser evaluates, refines, logs, and re-presents. Repeat this step as many times as the user needs.

**The revision loop continues until the user says "sessionize it" or equivalent.** Do not prompt the user to move on — let them decide when the spec is ready.

---

## Step 6 — Sessionize

When the user triggers sessionization:

Use the `strategic-implementation:sessionize` skill.

Pass:
- The finalized spec document
- The feature folder path (stored in Step 4)

The sessionize skill handles everything from here:
- Breaks the spec into sessions
- Runs the scope-limiter for dependency map
- Runs the full 10-agent review
- Synthesizes and patches
- Presents to the user for approval

This skill (strategic-implementation) ends when the user approves the sessionized plan inside the sessionize skill.

---

## End State

The user has an approved sessionized implementation plan.

The sessionize skill will have prompted the user:
> "When you're ready to plan a session for execution, say 'plan session [N]' or invoke the session-plan skill."

When the user triggers session planning, invoke `strategic-implementation:session-plan` passing:
- Implementation guide path: `<feature-folder-path>/implementation-guide.md`
- Feature folder path: `<feature-folder-path>/`
- Which session to plan (from the user)

---

## Constraints (apply throughout)

- No code before spec. This workflow is a gate, not a shortcut.
- Architecture and UX/PMF review outputs are embedded silently — the user sees the spec, not the review outputs.
- The spec document is not divided into sessions until the user approves and triggers sessionization.
- Hard decisions in the spec are locked — they carry through to sessions unchanged.
- The full agent review runs once on the sessionized plan — not on the spec document.
- Session planning is a separate invocation — this skill does not trigger it.
