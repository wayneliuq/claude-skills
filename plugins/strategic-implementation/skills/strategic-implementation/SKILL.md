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

Announce: "Starting clarification."
Use the `strategic-implementation:clarify` skill.

List assumptions. Ask only what would change the approach. Wait for user confirmation before proceeding.

---

## Step 2 — Scope Assessment

After clarification, assess scope against ALL THREE criteria:

**Fast-path if all three are true:**
1. Deliverable describable in one sentence
2. Change contained to one area (one component, file group, or feature)
3. No new architectural patterns or dependencies introduced

**If fast-path:**
1. Create `implementation-guide.md` at `docs/strategic-implementation/<date>-<slug>/implementation-guide.md` (derive date as `YYYY-MM-DD`, derive slug from the one-sentence description).
2. Populate it with the approved spec content — a concise implementation plan covering the goal, steps, deliverables, and any relevant constraints.
3. Announce: "Starting execution." then invoke `strategic-implementation:executing-plans`, passing:
   - Implementation guide path: `docs/strategic-implementation/<date>-<slug>/implementation-guide.md`
   - Feature folder path: `docs/strategic-implementation/<date>-<slug>/`

This skill ends here.

**Otherwise:** continue to Step 3.

---

## Step 3 — Draft Specification Document

Announce: "Drafting specification document."
Use the `strategic-implementation:implementation-drafter` skill.

Pass:
- The clarified request

The drafter produces a specification document using the 8-section framework with feedback slots.

Store the feature folder path returned by implementation-drafter. Pass it to:
- the post-spec review agents in Step 3a
- implementation-reviser in Step 5 (as spec file path: `<feature-folder-path>/spec.md`)
- sessionize in Step 6
- session-plan when the user triggers session planning
Do not re-derive it from the spec title.

---

## Step 3a — Post-Spec Review Gate

After the spec is drafted, collect document references before launching the review agents.

Ask the user:
1. **Architecture document** — "Where is the architecture document for this project? Is it current?" (Required — architecture review will BLOCK without it)
2. **UX/PMF document** — "Is there a UX or product-market fit document for this area?" (Only ask if the change has any user-facing impact; skip for purely backend changes)

Store both locations. They are passed to their respective agents and to the reviser in Step 5 — do not re-ask for them later.

Then announce: "Running architecture review and UX/PMF review against the spec." and launch both agents in parallel using the Agent tool:

- `strategic-implementation:architecture-review` (pass: spec content, architecture document location)
- `strategic-implementation:ux-pmf-review` (pass: spec content, UX/PMF document location, if applicable)

Wait for both to return.

**If either returns STATUS: BLOCK:** surface the blocking issue with the agent's recommended next step. Do not proceed to revision until resolved.

Present both review outputs to the user under a `## Spec Review` heading before entering the revision loop. Frame them as: "These reviews flagged the following before you start revising."

If the architecture review found that the change requires new architectural components or significant adaptation not yet documented: inform the user this must be resolved before revision begins.

---

## Step 5 — Iterative Revision

The user reviews the spec and provides feedback. When the user says "revise it" (with feedback in the message, in the feedback slots, or both):

Announce: "Revising spec."
Use the `strategic-implementation:implementation-reviser` skill.

Pass:
- The current spec document
- All user feedback
- Architecture document location (from Step 3a)
- UX/PMF document location (from Step 3a, if applicable)
- Spec file path: `<feature-folder-path>/spec.md` (from Step 3)

The reviser evaluates, refines, logs, and re-presents. Repeat this step as many times as the user needs.

**The revision loop continues until the user says "sessionize it" or equivalent.** Do not prompt the user to move on — let them decide when the spec is ready.

---

## Step 6 — Sessionize

When the user triggers sessionization:

Announce: "Sessionizing implementation plan."
Use the `strategic-implementation:sessionize` skill.

Pass:
- The finalized spec document
- The feature folder path (stored in Step 3)

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

When the user triggers session planning, announce: "Building session plan." then invoke `strategic-implementation:session-plan` passing:
- Implementation guide path: `<feature-folder-path>/implementation-guide.md`
- Feature folder path: `<feature-folder-path>/`
- Which session to plan (from the user)

---

## Constraints (apply throughout)

- No code before spec. This workflow is a gate, not a shortcut.
- Architecture and UX/PMF review outputs are presented to the user after the spec is drafted (Step 3a) — they serve as a visible review gate, not silent inputs to the drafter.
- The spec document is not divided into sessions until the user approves and triggers sessionization.
- Hard decisions in the spec are locked — they carry through to sessions unchanged.
- The full agent review runs once on the sessionized plan — not on the spec document.
- Session planning is a separate invocation — this skill does not trigger it.
