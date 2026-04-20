# strategic-implementation v2.0 — Redesign Spec

_Date: 2026-04-20_
_Author: Claude (Opus 4.7) in collaboration with Wayne_
_Target version: 2.0.0 (major — breaking)_

---

## 1. Context & Motivation

strategic-implementation v1.4.0 was built around human-supervised planning-and-execution: multi-gate approvals, 10-agent panels run twice (sessionize + session-plan), LOC-based session sizing, per-step TDD with atomic commits, and a spec-document framework optimized for engineer review.

Three things have shifted since v1.0:

1. **Opus 4.7 is meaningfully more autonomous.** SWE-bench Verified 87.6%, 1M context, self-verifies before reporting, most consistent long-context performance of any model. The model no longer needs the distillation that sub-agents historically provided.
2. **The sole user of this skill is a non-coder product manager** (Wayne) — long-term vision, cost, risk, reliability, and UX are the load-bearing concerns. Implementation mechanics matter only insofar as they affect those dimensions.
3. **Token cost and friction are the current bottlenecks.** The v1 review architecture runs roughly the same 10-agent panel twice per feature and re-reads the full plan N times per round. On mid-sized features this is millions of tokens with diminishing quality returns.

v2.0 restructures the workflow around a PM-approvable product brief, gate-based (not session-based) execution, tiered/escalated review (not upfront parallel panel), and validation methods matched to deliverable type (preview, CLI, TDD, post-hoc).

---

## 2. North Star

One skill that takes a PM-level product idea from "I want X" to "X is built, validated, and shipped" with:
- **One PM-facing document** — the product brief — as the only artifact the PM reviews and approves.
- **Autonomous derivation** of the implementation guide from the approved brief.
- **Plan-mode approval** as the single pre-execution gate.
- **Deliverable-gated execution** with validation method chosen per deliverable.
- **Tiered review** (generalist first, specialists only if flagged) — target ≥70% reduction in review-phase tokens vs. v1.4.0.

---

## 3. Users

**Primary user: non-coder product manager.**
- Evaluates features by cost, risk, reliability, UX impact, long-term vision alignment.
- Cannot review code. Can review preview screenshots, CLI outputs, plain-language tradeoff tables.
- Needs jargon translated. Needs alternatives presented. Needs cost/risk front-and-center, not buried.

**Secondary user: Claude Code orchestrator (the agent).**
- Executes autonomously under auto mode unless blocked.
- Follows instructions more literally than prior Claude generations — prompts must be unambiguous.

---

## 4. Success Criteria

A feature is successfully delivered under v2.0 when:

1. PM approves exactly one product brief per feature. No spec.md / implementation-guide.md / session-plan.md approval chain.
2. Implementation guide is auto-derived from the approved brief without PM intervention (PM may inspect on request).
3. Execution plan is presented in plan mode; PM approves once.
4. Every deliverable passes its declared validation gate before the next deliverable starts.
5. Review-phase token usage is ≤30% of v1.4.0 on an equivalent-scope feature.
6. No approval gate exists for routine progress — only for BLOCKs and PM-decision-required items.
7. Pre-GA features can undergo a prune-tests step at an explicit GA-prep milestone with a preview diff before deletion.

---

## 5. Scope & Exclusions

### In scope
- Full replacement of the current workflow: clarify → drafter → reviser → sessionize → session-plan → executing-plans → bug-fix → post-mortem → end-of-implementation.
- New artifact: `product-brief.md`.
- New skill: `product-brief-drafter`.
- Consolidation: merge related skills (bug-fix + post-mortem + end-of-implementation → `post-execution`).
- Agent panel consolidation (10 → ~4).
- Tiered / escalated review model.
- Validation taxonomy (preview / CLI / TDD / post-hoc).
- Prune-tests command for pre-GA test cleanup.
- Plan-mode execution plan as primary approval surface.
- Autonomy levels: `supervised` / `auto` / `yolo`.

### Out of scope
- Migration tooling for in-flight v1 feature folders. v1 continues to work for already-started features; new features use v2.
- Multi-feature coordination (roadmap-level planning). One feature at a time.
- Post-GA release management (CI/CD, deployment orchestration).
- Architecture or UX/PMF document authoring. v2 still requires these as inputs.

---

## 6. Key Decisions — Locked

These were settled through the design discussion preceding this spec. They are `[HARD DECISION]` and are not re-evaluated in revision.

1. **[HARD DECISION] One PM-facing artifact: the product brief.** No spec / implementation-guide / session-plan chain for PM approval. PM approves the brief; everything downstream is agent-derived.
2. **[HARD DECISION] Sessions and LOC gates are removed.** Replaced by deliverable gates defined in the product brief. Deliverable validation method (preview / CLI / TDD / post-hoc) is declared per deliverable at brief time.
3. **[HARD DECISION] Plan mode is BOTH the drafting environment and the approval gate.** The execution-plan skill invokes EnterPlanMode so that Claude Code's built-in plan-mode optimized prompting is the one doing the drafting. Review agents run inside plan mode (Agent tool is callable there). Approval occurs via plan mode's native UI. Inline `go`/`start` retained as fallback only. Plan-mode reliability confirmed fixed during design.
4. **[HARD DECISION] Review is tiered, not parallel-all-upfront.** A generalist reviewer runs first. Specialists run only for dimensions flagged by the generalist or triggered by plan-content pre-filter.
5. **[HARD DECISION] Agent panel consolidates to ~4 always-on agents:** `alignment` (merges 10k-foot + architecture-review + future-proofing), `boundaries` (merges security + data-model + api-contract), `runtime-risk` (merges performance + dependency), `tests`. Plus `simplify` (highest yield). Plus `frontend-engineer` as contextual.
6. **[HARD DECISION] Unit tests deleted only via explicit prune-tests command at PM-initiated GA-prep milestones, with preview diff and separate commit.** Never automatically. Acceptance / goal-level tests survive pruning. GA state tracked via repo-level flag (`.strategic-implementation/ga-state.json`); prune-tests blocked once repo is flagged `ga`.
7. **[HARD DECISION] Validation method declared per deliverable at brief time, not inferred at execution time.** Brief drafter classifies each deliverable into preview / CLI / TDD / post-hoc with a pre-flight env check before execution.
8. **[HARD DECISION] `_copied-skills/` deleted.** Already deprecated; removed from the plugin entirely in v2.0.

---

## 7. Workflow

```
┌──────────────────────────────────────────────────────────────┐
│                     USER INVOKES SKILL                       │
└──────────────────────────────────────────────────────────────┘
                             │
                             ▼
                         [clarify]
       Surface assumptions. Collect all doc locations
       up front (architecture, UX/PMF, security, schema).
       Ask only approach-changing questions.
                             │
                             ▼
               [product-brief-drafter]
       Produces product-brief_<slug>.md — PM-facing document.
       Sections: North Star, User-facing behavior, Scope,
       Key decisions & tradeoffs (compact rows), Effort &
       cost signal, Reliability & failure modes,
       Dependencies, Deliverable gates (with validation
       method declared), Open questions.
       No code. Jargon translated.
                             │
                             ▼
         PM reviews brief → revise (reviser) ⇄ approve
       Revision loop is PM-oriented: is the tradeoff clear,
       is the recommendation justified, is the risk accurate.
                             │
                             ▼
           [execution-plan] — enters plan mode
       The execution-plan skill enters Claude Code's plan
       mode (EnterPlanMode) to leverage CC's built-in
       plan-mode optimized prompting. Plan is drafted
       inside plan mode with live repo state (Glob/Grep
       for file paths). Structure: for each deliverable:
       files touched, validation method + rubric,
       parallel-group annotations, dependency DAG.
                             │
                             ▼
              [review] — tiered, runs on the plan
   ┌──────────────────────────────────────────────────┐
   │ 1. Pre-filter: scan plan for trigger tokens.     │
   │    Skip specialists whose domain is absent.      │
   │ 2. Generalist (`alignment`) runs single-pass,    │
   │    returns JSON: {status, flags, recs}.          │
   │ 3. simplify runs (whole-plan, single-pass).      │
   │ 4. Specialists run ONLY for dimensions flagged   │
   │    by generalist OR triggered by pre-filter.     │
   │ 5. Synthesize; patch plan; BLOCKs halt.          │
   │    If BLOCK traces to a brief decision, surface  │
   │    for brief revision.                           │
   └──────────────────────────────────────────────────┘
                             │
                             ▼
          [plan mode presents patched plan] — single PM gate
       Plan mode UI presents the patched plan + agent findings
       to PM. Subagents (Agent tool) are callable inside plan
       mode — review runs without exiting. Approve in plan mode
       → ExitPlanMode → execute. Reject or revise → back to plan
       draft (still inside plan mode, no re-entry cost).
                             │
                             ▼
                      [execute]
       Per deliverable:
       1. Pre-flight check: validation env available?
          If not, escalate to TDD-required.
       2. Implement (per-deliverable, not per-step).
       3. Validate by declared method:
          - Preview: screenshot + rubric check
          - CLI: command + regex match
          - TDD: goal-level acceptance test
          - Post-hoc: spot-read
       4. Log to validation-log.md.
       5. Commit per deliverable.
       6. Advance.
       BLOCK / validation-fail → surface, halt.
                             │
                             ▼
                   [post-execution]
       Single consolidated skill (merges bug-fix,
       post-mortem, end-of-implementation):
       - Cross-contamination check (modified files ∪ git log
         → dependents → regression risk)
       - Full test suite run
       - E2E / integration tests authored for feature flows
       - Deviation synthesis → project-learnings.md if ≥2
         meaningful deviations
       - (Optional, user-triggered) prune-tests with diff preview
```

---

## 8. Artifacts

### Per-feature folder: `docs/strategic-implementation/<YYYY-MM-DD>-<slug>/`

| File | Produced by | Reviewed by | Purpose |
|---|---|---|---|
| `product-brief_<2-3-word-slug>.md` | product-brief-drafter | PM (required) | Approval artifact |
| `execution-plan.md` | execution-plan-drafter | Agent panel + PM (in plan mode) | Reviewed technical artifact, approved via plan mode |
| `validation-log.md` | executing-plans | PM (on failure only) | Per-gate audit trail |
| `post-execution-report.md` | post-execution | PM (on summary) | E2E + regression + deviations |

Product brief filename convention: `product-brief_<2-3-word-description>.md` (e.g. `product-brief_google-login.md`, `product-brief_session-persistence.md`). Slug is lowercase, hyphen-separated, derived from the feature's North Star.

**`implementation-guide.md` is removed from the default happy path.** The execution plan is the reviewed technical artifact; no intermediate guide is materialized. A separate guide is drafted only in the conditional cases described in §7 (XL features, architectural novelty flagged by `alignment`, or `supervised` mode where PM asks for a materialized guide).

Deleted from v1: `spec.md`, `session-N-plan.md`, `session-N-log.md`, `session-N-postmortem.md`, `implementation-guide.md` (default path).

### Shared: `docs/strategic-implementation/project-learnings.md`
Retained. Injection strategy changes — see §11.

---

## 9. Product Brief — Structure

```markdown
# Product Brief: <feature name>

## 1. North Star
(3–5 sentences in plain language — what this does for the user)

## 2. User-Facing Behavior
(step-by-step walkthrough, preview screenshots where feasible,
no implementation language)

## 3. Scope
**In:** bullets
**Out:** bullets (explicit exclusions)

## 4. Key Decisions & Tradeoffs
For each decision, default to the compact form:

### Decision: <short title>
**Recommendation:** <choice>
**Why:** <one sentence, product-language>
**Alternatives considered:** <one-line dismissal per alternative>
**Jargon note:** <if any term needs translation>

> _Ask for deeper comparison if you want to explore any alternative — the full cost / risk / reliability / UX tradeoff table is generated on demand._

**Full tradeoff table is only generated when:**
- PM explicitly asks ("compare option B in detail")
- Decision has been flagged `[HARD DECISION]` in the brief (locked choices warrant full substantiation)
- `simplify` agent flags the decision as potentially over-scoped

This keeps the brief ~10× shorter on decision sections without losing PM's ability to challenge any choice.

## 5. Effort & Cost Signal
- Size: S / M / L / XL (calendar days, not LOC)
- Ongoing infra/API cost: $/month estimate
- One-time migration cost (if any)
- External dependencies introduced

## 6. Reliability & Failure Modes
- What breaks when it breaks
- Blast radius: which other features affected
- Rollback cost: easy / moderate / high

## 7. Dependencies
- External services, auth, data stores, existing systems touched

## 8. Deliverable Gates
Each row is a checkpoint the PM can verify:
| # | Deliverable (user-observable) | Validation method | Rubric |
|---|---|---|---|
| 1 | User can log in with Google | Preview | Screenshot shows dashboard post-login |
| 2 | User's session persists across reload | CLI | `curl .../me` returns 200 with user id |
| 3 | Expired sessions redirect to login | TDD | Acceptance test: POST w/ expired JWT → 401 redirect |

## 9. Open Questions for PM
- Explicit unknowns requiring PM input before approval

## 10. Revision Log
(appended by reviser — each round logged)
```

**Discipline rules enforced by product-brief-drafter:**
- Target length: 10–15 min read for S/M, 30 min for L/XL
- No code snippets
- Every technical term has a one-line translation parenthetical
- Every decision lists at least two options with explicit tradeoffs
- Success criteria (deliverable gates) written in user-observable terms

---

## 10. Agent Panel — v2.0

### Always-on (consolidated)
| Agent | Replaces | Role |
|---|---|---|
| `alignment` | 10k-foot + architecture-review + future-proofing | Architecture alignment, structural hygiene, product fit |
| `boundaries` | security + data-model + api-contract | All boundary-contract checks: auth, schema, interfaces |
| `runtime-risk` | performance + dependency | Non-functional risk: runtime behavior, deps, scaling |
| `tests` | test-coverage | Goal-level acceptance coverage (under v2's validation model) |
| `simplify` | (unchanged) | Highest-yield scope reduction |

### Contextual (launched only if triggered)
| Agent | Trigger | Role |
|---|---|---|
| `frontend-engineer` | Guide contains UI/preview-validated deliverables | UI/UX correctness — absorbs UX concerns from prior ux-pmf agent |

### Removed
- `10k-foot`, `architecture-review`, `future-proofing`, `security`, `data-model`, `api-contract`, `performance`, `dependency` — merged.
- `scope-limiter` — logic moved inline into guide-drafter (ordering + DAG generation).
- `ux-pmf-review` — **PMF concerns fold into `alignment`** (product-fit is an alignment dimension). **UX concerns fold into `frontend-engineer`** (UX is evaluated where the UI is reviewed).

### Review execution model
1. **Pre-filter** scans the implementation guide for domain triggers. Specialists without a domain match are skipped regardless of what follows.
2. **Generalist (`alignment`) runs single-pass** with JSON output schema. Returns `{status, flags: [{dimension, issue, fix}], recommendations}`. `max_tokens: 1500`.
3. **`simplify` runs single-pass** in parallel with the generalist.
4. **Specialists run only for flagged dimensions.** If `alignment` flags nothing in `boundaries.security`, security is not invoked.
5. **Structured output, no prose narration.** Thinking stays in thinking blocks.

---

## 11. Token-Reduction Inventory (applied)

| # | Technique | Scope |
|---|---|---|
| 1 | Panel consolidation 10 → 4 always-on + 2 contextual | All reviews |
| 2 | Tiered / escalated review (generalist → specialists on flag) | All reviews |
| 3 | Single-pass multi-perspective for generalist | Always-on |
| 4 | Pre-filter by plan-content keywords | All specialists |
| 5 | Per-agent structured extract (not full guide) | All specialists |
| 6 | JSON output schema + `max_tokens: 1500` cap | All agents |
| 7 | Thinking stays in thinking blocks; no output narration | All agents |
| 8 | Prompt cache prefix per agent (rubric cached, variables swapped) | All agents |
| 9 | Shared base system prompt across agents | All agents |
| 10 | Diff-based review in revision loop | Reviser → reviewers |
| 11 | Agent instance reuse across phases (SDK-dependent) | Feature lifecycle |
| 12 | Agent md file distillation → 80–120 lines each | All agents |
| 13 | Drop `implementation-guide` as loadable skill (inline template) | Plugin load |
| 14 | Learnings by top-K embedding similarity, not category-tag dump | All agents |
| 15 | Batch commits per deliverable, not per step | Execution |
| 16 | Regex-based CLI validation rubrics (not model-judged) | Execution |
| 17 | Review the plan once (at guide review); consistency-only check at execution-plan time | Execution plan |
| 18 | Drop post-spec review gate (folded into brief-drafter) | Brief phase |
| 19 | Remove `implementation-reviser` as distinct skill; two-mode drafter | Brief phase |
| 20 | Delete `_copied-skills/` | Plugin |
| 21 | Compact decision rows in product brief (full tradeoff table on-demand only) | Brief drafting + revision |
| 22 | Drop default `implementation-guide-drafter` phase; plan IS the reviewed technical artifact | Guide-draft phase eliminated on happy path |
| 23 | Agent panel reviews the execution plan (technical content), not the brief (PM content) | Review phase yields scale with reviewable material |

Cumulative target: **≥70% review-phase token reduction** vs. v1.4.0 on an equivalent-scope feature.

---

## 12. Validation Model

### Taxonomy
Each deliverable is classified at brief time into one of:

**Preview-validatable** — UI observable in Claude Code preview.
- Rubric: screenshot-assertion description ("dashboard visible with user name in top-right").
- Execution: invoke preview tool, capture, compare.

**CLI-validatable** — DB row, S3 object, API response, log line observable via one command.
- Rubric: command + regex pattern (not substring).
- Execution: run command, match regex, log.

**TDD-required** — silent failure modes.
Triggers: branching logic with many conditions, concurrency, error paths, pure-compute with no side effect, security invariants.
- Rubric: goal-level acceptance test (ATDD), written before code.
- Execution: test must fail pre-implementation, pass post-implementation. Test survives prune-tests.

**Post-hoc inspectable** — trivial: renames, config bumps, doc edits.
- Rubric: spot-read by orchestrator.

### Pre-flight check
Before execution starts, for each deliverable verify its validation env is available:
- Preview: dev server running, Claude Code Preview tool responsive.
- CLI: command binary installed, creds available.
- TDD: test framework configured.

**If validation env is unavailable OR validation cannot be automated** (e.g. preview produces ambiguous output, CLI command errors, TDD test framework misconfigured):
- `supervised` / `auto` mode → **pause execution and prompt PM for manual validation**. PM inspects and replies `pass` / `fail` / `escalate to TDD`.
- `yolo` mode → **auto-escalate to TDD-required**. No user prompt.

Never silently skip validation.

### Validation log
`validation-log.md` entry per deliverable: method, command/test run, output observed, pass/fail, timestamp. Feeds post-execution directly.

---

## 13. Autonomy Levels

Set once per feature at clarify time. Default: `auto`.

| Level | Brief approval | Guide approval | Plan approval | Execution gates |
|---|---|---|---|---|
| `supervised` | Required | Required | Required (plan mode) | Prompt on every deliverable |
| `auto` | Required | Auto (skip to plan) | Required (plan mode) | Prompt only on BLOCK / decision-required |
| `yolo` | Required | Auto | Auto | Prompt only on BLOCK |

PM can step up or down between features. `yolo` reserved for well-understood, low-risk features.

---

## 14. Prune-Tests Command

Triggered only by explicit PM invocation at a GA-prep milestone.

**GA signal: repo-level flag.** A file at `.strategic-implementation/ga-state.json` holds the current GA state for the repo:

```json
{
  "ga_state": "pre-ga" | "ga-prep" | "ga",
  "last_updated": "2026-04-20",
  "updated_by": "wayne"
}
```

- `pre-ga` (default): prune-tests available, unit tests may be deleted.
- `ga-prep`: prune-tests still available, but with an additional confirmation prompt ("Repo is flagged ga-prep — is this prune the final pre-GA cleanup?").
- `ga`: prune-tests **blocked**. Unit tests are load-bearing regression safety; can only be removed via normal code review / PR process.

PM changes the flag via a single CLI invocation or direct file edit; the skill never changes it automatically.

Steps:
1. Read `.strategic-implementation/ga-state.json`. If `ga`, refuse with explanation. If absent, default to `pre-ga`.
2. Identify all tests in the repo by classification:
   - Acceptance / goal-level → survive
   - Unit / line-level → candidate for deletion
3. Present preview diff: file-by-file, line-count-by-line-count.
4. Require explicit PM confirmation per batch (not per file, not per run — per batch).
5. Delete in a separate commit (titled `prune: remove pre-GA unit tests`).
6. Run surviving test suite post-prune to confirm acceptance coverage intact.

Never automatic. Never bundled with feature commits. Always reversible via git revert of the prune commit.

---

## 15. Plugin Structure — v2.0

```
strategic-implementation/
│
├── package.json                      # version 2.0.0
├── README.md
│
├── skills/
│   ├── strategic-implementation/SKILL.md     # Orchestrator (unchanged role, new flow)
│   ├── clarify/SKILL.md                      # Collects all docs up front
│   ├── product-brief-drafter/SKILL.md        # NEW — produces PM-facing brief (two modes: draft / revise)
│   ├── execution-plan/SKILL.md               # Drafts plan from approved brief + live repo state, invokes review, opens plan mode
│   ├── review/SKILL.md                       # NEW — orchestrates tiered review against the execution plan
│   ├── implementation-guide-drafter/SKILL.md # OPTIONAL — invoked only for XL features or when PM explicitly asks
│   ├── executing-plans/SKILL.md              # Deliverable-gated execution
│   ├── post-execution/SKILL.md               # NEW — merges bug-fix + post-mortem + end-of-implementation
│   └── prune-tests/SKILL.md                  # NEW — explicit pre-GA cleanup
│
└── agents/
    ├── alignment.md          # NEW — merged (now includes PMF)
    ├── boundaries.md         # NEW — merged
    ├── runtime-risk.md       # NEW — merged
    ├── tests.md              # renamed from test-coverage
    ├── simplify.md
    └── frontend-engineer.md  # contextual (now absorbs UX concerns)

# Removed:
# _copied-skills/, sessionize/, session-plan/, implementation-drafter/,
# implementation-reviser/, architecture-review/, ux-pmf-review/,
# bug-fix/, post-mortem/, end-of-implementation/, implementation-guide/
# Agents: 10k-foot, architecture-review, future-proofing, security,
# data-model, api-contract, performance, dependency, scope-limiter
```

---

## 16. Risks & Unknowns

### Risks
1. **Opus 4.7's literal instruction-following** means every new skill prompt needs unambiguous phrasing. Loose phrasing that worked on 4.6 may execute unexpectedly. Mitigation: distillation pass with explicit unambiguous language review.
2. **Tiered review misses cross-domain issues** the generalist doesn't notice. Mitigation: simplify runs unconditionally; pre-filter triggers are conservative (include on any domain token match, not strict).
3. **Preview / CLI validation env fragility.** Dev server crashes, DB seed wrong, preview tool flaky. Mitigation: pre-flight check auto-escalates to TDD.
4. **Deletion of unit tests is irreversible after squash-merge.** Mitigation: separate commit, per-batch confirmation, never bundled.
5. **Plan-mode reliability regressions in future Claude Code versions.** Mitigation: retain inline `go`/`start` fallback in execution-plan skill.

### Unknowns
- Exact token reduction achievable — 70% target is based on component-level estimates; needs validation on a real v2 run.
- Whether agent-instance reuse across phases is supportable in Claude Agent SDK as currently shipped. May require staging or fall back to stateless re-invocation.
- Whether PM will want to inspect auto-derived implementation guides in practice, or trust the derivation. Default is silent; adjustable if PM asks to see.

---

## 17. Open Questions for PM

_All open questions resolved in Round 1. See Revision Log §18._

---

## 18. Revision Log
_(appended by reviser)_

- **Round 0 (2026-04-20):** Initial draft.
- **Round 4 (2026-04-20):** Plan mode is the drafting environment, not just the approval gate.
  - §7 workflow: execution-plan skill calls EnterPlanMode; drafting happens inside plan mode to leverage CC's hidden plan-mode prompting. Review subagents run inside plan mode. Approval via plan mode native UI.
  - §6 HARD DECISION 3 rewritten accordingly.
  - Rationale: Claude Code's plan mode has proprietary prompt optimizations tuned for planning tasks; using it as the drafting environment (not just the approval surface) inherits those gains for free.
- **Round 3 (2026-04-20):** Workflow restructure — review targets the execution plan, not the brief.
  - §7 workflow diagram updated: execution-plan drafted silently → tiered review runs on the plan → patched plan opens in plan mode for PM. Single PM gate for plan + agent findings.
  - §8 artifacts: `execution-plan.md` replaces `implementation-guide.md` as the reviewed technical artifact. Guide removed from default happy path; retained as optional conditional phase.
  - §15 plugin structure: `execution-plan` skill repositioned as default path; `implementation-guide-drafter` marked OPTIONAL.
  - §11 rows 22–23 added.
  - Rationale: agents reviewing the brief (PM-facing, jargon-translated, technical-detail-light) have minimal material to flag. Agents reviewing the plan (concrete file paths, OAuth flows, schema deltas, dependency calls) have real attack surface and real errors to catch. The brief was already reviewed — by the PM. Running the agent panel on it duplicates approval. Plan-time review also benefits from live repo state discovered at plan draft, catching file-path drift the brief couldn't surface.
- **Round 2 (2026-04-20):** Token-efficiency edit — compact decision rows in product brief.
  - §9 Section 4: default to Recommendation + one-sentence Why + one-line alternative dismissals. Full tradeoff table (cost / risk / reliability / UX) generated on demand only, or automatically for `[HARD DECISION]` items and simplify-flagged decisions.
  - §11 row 21 added.
  - Rationale: eager alternatives-exhaustion is ~2–5k tokens per brief × N revision rounds, with ~95%+ of recommendations shipping unchanged and most "alternatives" being straw-man filler. Lazy generation preserves PM's ability to challenge without paying the eager cost.
- **Round 1 (2026-04-20):** PM answered all 6 open questions. Resolutions folded into spec:
  1. **Brief filename convention** → `product-brief_<2-3-word-description>.md` (e.g. `product-brief_google-login.md`). Applied in §8.
  2. **Default autonomy level** → `auto` confirmed. No change to §13 defaults.
  3. **Preview fallback behavior** → When preview unavailable or validation non-automatable: pause for PM manual validation in `supervised`/`auto` mode; auto-escalate to TDD in `yolo`. Applied in §12 Pre-flight check.
  4. **GA milestone signaling** → Repo-level flag at `.strategic-implementation/ga-state.json` with `pre-ga`/`ga-prep`/`ga` states. Prune-tests blocked once `ga`. Applied in §14.
  5. **Revision loop presentation** → Inline markdown in-conversation, grep-friendly section headers preserved so PM feedback can reference specific sections directly.
  6. **UX/PMF agent disposition** → PMF folds into `alignment`; UX folds into `frontend-engineer`. No standalone `ux-pmf` agent. Applied in §10 and §15.
