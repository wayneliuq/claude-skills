---
name: session-plan
description: Template and authoring rules for the session plan — a concrete, bounded execution plan for the next implementation session only, derived from the approved implementation guide.
---

# Session Plan

The session plan covers **one session only** — the next session in the approved implementation guide. It is built after the implementation guide is approved and reviewed by the same agent panel before being presented to the user.

---

## Authoring Rules

1. **One session only.** Do not plan beyond the current session. Do not reference future sessions except in pre-conditions.
2. **Goal must match the implementation guide verbatim.** Copy it directly — do not rephrase.
3. **Steps must be concrete.** Each step names the exact file(s) to change and what to write or modify. No vague directives like "implement the feature."
4. **Deliverables & Tests are copied from the implementation guide** and expanded with implementation-specific detail.
5. **≤ ~1000 LOC constraint is hard.** If following the implementation guide session would exceed this, split the session and note it. Flag to the user.
6. **Do not implement anything from the next session.** If a step is "out of session scope," mark it explicitly and stop.
7. **Pre-conditions must be checkable.** Every item in Pre-conditions must be something that can be verified before starting.

---

## Template

```markdown
## Session Plan: [Session Name]
_Implements: Implementation Guide § Session N_
_Date: [date]_

### Goal
(one sentence — copied verbatim from the implementation guide)

### Pre-conditions
- [ ] Prior sessions complete: [list session names, or "none" if this is Session 1]
- [ ] Docs available: architecture doc, UX/PMF doc (if applicable), implementation guide
- [ ] [Any other specific pre-condition: e.g., "staging environment running", "dependency X installed"]

### Steps
1. [Concrete step]
   - Files: [exact file paths]
   - What: [what to write, add, change, or delete — specific enough to execute without guessing]

2. [Next step]
   - Files: ...
   - What: ...

[...continue until all deliverables are covered...]

### Deliverables & Tests
(Copied from implementation guide, expanded with implementation specifics)
- [ ] Deliverable: [what is produced]
  Test: [specific verification — command to run, behavior to observe, or check to perform]

### Constraints
- Target: ≤ ~1000 LOC edited or written this session
- Do not implement anything from Session [N+1]
- Flag any unexpected scope expansion to user before proceeding
- If a step reveals that a pre-condition was not met, stop and surface to user
```

---

## Quality Checks (orchestrator applies before presenting to user)

- [ ] Goal is copied verbatim from the implementation guide
- [ ] All pre-conditions are checkable (no vague pre-conditions)
- [ ] Every step names exact files
- [ ] Every deliverable has a specific, runnable or observable test
- [ ] Estimated LOC total is within ~1000
- [ ] No step implements work from a future session
- [ ] Constraints section is present and complete
