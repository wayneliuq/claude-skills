# strategic-implementation

A Claude Code plugin that enforces a full planning-to-execution workflow before any code is written. It ensures every non-trivial change is grounded in architecture, reviewed for risk, and broken into bounded sessions before execution begins.

---

## What It Does

Takes a description of work to be done → produces an approved, agent-reviewed, sessionized implementation plan. Session planning and execution are handled separately.

---

## Workflow at a Glance

```
/strategic-implementation
  │
  ├─ Existing sessionized plan? → use session-plan skill directly
  ├─ Spec in progress?          → resume revision or sessionize
  └─ Nothing yet?               → full workflow ↓
  │
  ▼
[clarify] — surface assumptions, ask only what changes the approach
  │
  ▼
Scope assessment
  ├─ Small, bounded, no new patterns → fast-path (writing-plans + executing-plans)
  └─ Everything else ↓
  │
  ▼
Collect document locations (architecture doc, UX/PMF doc)
  │
  ▼
[architecture-review] ──┐
[ux-pmf-review]    ─────┘  (parallel, outputs embedded silently in draft)
  │
  ▼
[implementation-drafter] → 8-section spec document with feedback slots
  │
  ▼
User reviews spec ──→ [implementation-reviser] ──→ iterate until ready
  │                    (critical evaluation, hard decisions, revision log)
  │
  ▼  (user says "sessionize it")
[sessionize]
  ├─ Convert spec → sessions
  ├─ scope-limiter generates dependency map
  ├─ Full 10-agent review panel (single round)
  └─ Present for user approval
  │
  ▼
Implementation plan approved
  │
  ▼  (user invokes separately)
[session-plan] → build plan for one session → agent review → executing-plans
```

---

## File Structure

```
strategic-implementation/
│
├── SKILL.md                          # Master orchestrator — start here
│
├── skills/                           # Interactive skills (may ask user questions)
│   ├── clarify.md                    # Entry gate: assumptions + targeted questions
│   ├── architecture-review.md        # Locates arch doc, extracts structure, assesses impact
│   ├── ux-pmf-review.md              # User types, UX considerations, auto-skips backend changes
│   ├── implementation-drafter.md     # Produces the 8-section spec document
│   ├── implementation-reviser.md     # Revises spec based on user feedback, logs each round
│   ├── sessionize.md                 # Converts approved spec into sessionized plan + agent review
│   ├── implementation-guide.md       # Template and authoring rules for the sessionized plan
│   └── session-plan.md              # Builds and reviews a single session execution plan
│
├── agents/                           # Analytical agents (receive plan, return structured output)
│   ├── 10k-foot.md                   # Alignment with architecture and desired end-product
│   ├── technical-expert.md           # Stack-specific pitfalls, implementation step errors
│   ├── scope-limiter.md              # Session sizing, ordering, dependency map generation
│   ├── future-proofing.md            # Modularity, naming, structure, documentation coverage
│   ├── security.md                   # Attack surface, access control, policy alignment
│   ├── data-model.md                 # Schema correctness, migration safety, backwards compatibility
│   ├── api-contract.md               # Interface completeness, versioning, error contract
│   ├── test-coverage.md              # Coverage, test types, correctness, fragility, risk
│   ├── performance.md                # Query efficiency, caching, blocking ops, scaling
│   ├── dependency.md                 # Necessity, license compatibility, maintenance, versioning
│   └── frontend-engineer.md          # Conditional: UI/UX correctness (only if front-end changes)
│
└── _copied-skills/                   # Copied from superpowers plugin with attribution
    ├── writing-plans.md              # Used by fast-path only
    ├── executing-plans.md            # Auto-invoked on session plan approval
    └── plan-document-reviewer-prompt.md
```

---

## Key Concepts

**Spec document vs. sessionized plan**
The spec (produced by `implementation-drafter`, refined by `implementation-reviser`) defines *what* and *why*. It has no sessions. The sessionized plan (produced by `sessionize`) defines *what gets built in which order*. Agents review the sessionized plan, not the spec.

**Hard decisions**
Decisions the user marks as non-negotiable (tight language: "must be," "non-negotiable," etc.) are marked `[HARD DECISION]` in the spec and carried through to the sessionized plan. They are locked — agents note their implications but do not attempt to reverse them.

**Agent review rounds**
- **Sessionize:** one full 10-agent review round on the complete sessionized plan
- **Session plan:** one full 10-agent review round on the individual session plan

**Fast-path**
Small, clearly bounded changes (one sentence, one area, no new patterns) bypass the full workflow and use `writing-plans` + `executing-plans` directly.

---

## Deferred (v2)

- Architecture development sub-skill (for when no arch doc exists)
- UX/PMF development sub-skill (for when no UX/PMF doc exists)
- Mid-execution plan amendment skill
- Post-execution code review step
- Additional agents: security audit, data model deep-dive, API contract formal spec, and others
