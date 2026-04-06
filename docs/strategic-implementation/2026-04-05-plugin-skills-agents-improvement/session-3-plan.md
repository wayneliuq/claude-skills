## Session Plan: Agent Scope Boundaries and Signal Trimming
_Implements: Implementation Plan § Session 3_
_Date: 2026-04-06_

### Goal
Improve all 11 review agents by adding explicit scope boundaries and trimming low-signal review steps in 10 of them, incorporating the highest-impact findings from the research phase.

### Pre-conditions
- [x] Session 1 complete: `docs/strategic-implementation/2026-04-05-plugin-skills-agents-improvement/research-findings.md` exists with 11 `###` sections (spec says 10; file has 11 including frontend-engineer — all domains covered, no blocker)
- [x] Session 2 complete: `future-proofing.md` learning tag already corrected; no overlapping files with Session 3
- [ ] Read `research-findings.md` in full before beginning any agent edits
- [ ] Spec reference: `docs/strategic-implementation/2026-04-05-plugin-skills-agents-improvement/spec.md` — "Not in scope" lines from §4.2.2, trimming targets from §4.2.1

### Research Finding Decisions (pre-determined)

| Agent | Finding | Decision |
|---|---|---|
| 10k-foot | All 4 findings | INCORPORATE — strengthen sections 1 and 2 |
| technical-expert | Low 1 (initialization order) | INCORPORATE → Step 3 |
| technical-expert | Low 2 (fallible ops without error handling) | INCORPORATE → Step 3 |
| technical-expert | High 1 (trace data flow / integration gaps) | REJECT — this is the Integration Gaps concern being explicitly removed from technical-expert and handed to api-contract per spec §4.2.1 |
| technical-expert | High 2 (unstated assumptions as bugs) | INCORPORATE → Step 2 |
| scope-limiter | All 4 findings | INCORPORATE — strengthen Task 1 |
| test-coverage | All 4 findings | INCORPORATE — merged Step 4, Steps 2 and 3 |
| security | Low 1 (UI-layer-only enforcement) | INCORPORATE → Step 3 |
| security | Low 2 (credentials in code BLOCK) | INCORPORATE → merged Step 5 |
| security | High 1 (entry points missing 4 requirements) | INCORPORATE → new Step 6 |
| security | High 2 (deferred threat modeling) | REJECT — not actionable at plan-review level; flags nearly every plan without specific guidance |
| data-model | All 5 findings | INCORPORATE — sharpen Steps 2, 3, 4 |
| api-contract | Low 1 (naming inconsistencies) | INCORPORATE → Step 6 |
| api-contract | Low 2 (error envelope format) | INCORPORATE → Step 4 |
| api-contract | High 1 (BLOCK breaking changes without consumers) | INCORPORATE → Steps 3+5 |
| api-contract | High 2 (interfaces without contract tests) | REJECT — substantively restates Step 7 (contract capture) which is explicitly removed per spec §4.2.1 |
| performance | All findings | INCORPORATE — sharpen Steps 2–6 |
| dependency | All 4 findings | INCORPORATE — sharpen Steps 2, merged 3 |
| future-proofing | All 4 findings | INCORPORATE — sharpen Tasks 1–4 |
| frontend-engineer | All 5 findings | REJECT — in-progress baseline file; Session 3 adds scope boundary line only |

### Steps

**Step 1 — Read `research-findings.md`** _(sequential, pre-step)_
- Files: `docs/strategic-implementation/2026-04-05-plugin-skills-agents-improvement/research-findings.md`
- What: Read in full; confirm 11 sections present; apply incorporate/reject decisions from table above; proceed to parallel group A

**Steps 2a–2k — Edit all 11 agent files** `[parallel group: A]`
All files are independent — all can run concurrently. For each agent in a single edit: (1) add "Not in scope" line, (2) apply per-spec trimming, (3) incorporate applicable research findings.

**Step 2a — `plugins/strategic-implementation/agents/10k-foot.md`** `[parallel group: A]`
- What:
  1. Add after opening paragraph: `**Not in scope:** Implementation details, library choices, test strategy (owned by technical-expert, test-coverage). Naming and structural quality (owned by future-proofing).`
  2. Merge `### 3. Gaps and Misalignment` into `### 2. Alignment with Desired End-Product` — rename merged section `### 2. Alignment with Desired End-Product and Gaps`; preserve all three flag conditions from section 3 verbatim in the merged section's "Look for:" list
  3. Renumber `### 4. Architectural or UX Drift` → `### 3. Architectural or UX Drift`
  4. Add to section 1 "Look for:": flag if plan omits downstream consumers for new components; flag if session goal cannot be mapped to an architectural component; flag cross-cutting concerns added per-component instead of a shared layer; flag shared component modifications without naming affected dependents

**Step 2b — `plugins/strategic-implementation/agents/technical-expert.md`** `[parallel group: A]`
- What:
  1. Add after opening paragraph: `**Not in scope:** Test correctness or coverage strategy (owned by test-coverage). Interface completeness between components — integration gaps (owned by api-contract).`
  2. Remove `### 4. Integration Gaps` section entirely
  3. Strengthen Step 3 "Review for Implementation Errors": add flag for steps that depend on a resource (database connection, cache, external service) initialized in a later step; add flag for fallible operations (network call, file read, DB write) without error handling specified
  4. Add to Step 2 "Research Known Pitfalls": flag any step where the implementer must make an unstated assumption (input ranges, call ordering, concurrency safety)

**Step 2c — `plugins/strategic-implementation/agents/scope-limiter.md`** `[parallel group: A]`
- What:
  1. Add after opening paragraph: `**Not in scope:** Whether the feature is the right feature to build (owned by 10k-foot). Whether the approach is technically sound (owned by technical-expert).`
  2. Trim prose across all 5 tasks — reduce verbose list items to 1–2 sentences each without removing flag conditions
  3. Strengthen Task 1 (Scope Creep): name the specific offending file for out-of-goal edits; flag drive-by refactoring by specific change name; flag deliverables absent from the spec; flag sessions bundling two logically independent deliverables

**Step 2d — `plugins/strategic-implementation/agents/test-coverage.md`** `[parallel group: A]`
- What:
  1. Add after opening paragraph: `**Not in scope:** Whether code is technically correct (owned by technical-expert). File and folder placement decisions (owned by future-proofing).`
  2. Merge `## Step 4 — Individual Test Correctness` and `## Step 5 — Test Fragility` into `## Step 4 — Test Quality: Correctness and Fragility`; renumber old Step 6→5, old Step 7→6, old Step 8→7; rename `## Step 8a — Transitive and Isolation Risks` → `## Step 8 — Transitive and Isolation Risks` (standalone independent step — not a sub-step; all three subsections within it preserved in full)
  3. Strengthen merged Step 4: add flag for abstract test descriptions using language like "verify it works" or "ensure correct behavior" without specifying input/state/expected output; strengthen Step 2: add flag for behaviors with no error-path test; strengthen Step 3: add flag if >3 unit-testable behaviors are described only as E2E tests; add flag if two components share a boundary with no integration test described

**Step 2e — `plugins/strategic-implementation/agents/security.md`** `[parallel group: A]`
- What:
  1. Add after opening paragraph: `**Not in scope:** Authorization UI patterns (owned by frontend-engineer). Business-logic validation unrelated to trust boundaries (owned by technical-expert).`
  2. Merge `## Step 5 — Input Trust` and `## Step 6 — Secrets Handling` into `## Step 5 — Untrusted Inputs and Secrets` (per spec §4.2.1); renumber old Step 7→Step 6. Preserve all BLOCK criteria from both source steps verbatim
  3. Strengthen Step 3 (Authorization Boundaries): add flag for privileged actions enforced only at the UI layer with no server-side check
  4. Strengthen merged Step 5: add BLOCK for credentials/API keys/tokens stored in code or version-controlled config
  5. Strengthen new Step 6 (was Step 7): for each new entry point, verify all four are specified — authentication, authorization, rate limiting, input validation

**Step 2f — `plugins/strategic-implementation/agents/data-model.md`** `[parallel group: A]`
- What:
  1. Add after opening paragraph: `**Not in scope:** Query performance optimization (owned by performance). API response shape and serialization format (owned by api-contract).`
  2. Trim prose in all 6 steps — condense flag list items; all 6 steps kept (high-stakes domain)
  3. Strengthen Step 4 (Schema Correctness): BLOCK monetary/financial fields described as floating-point; flag query patterns (filter, sort, join, range scan) without a named supporting index
  4. Strengthen Step 2 (Backwards Compatibility): BLOCK column drops or renames without expand-contract migration; BLOCK NOT NULL constraint additions without a backfill migration
  5. Strengthen Step 3 (Migration Safety): flag any migration not verified safe when old and new code run simultaneously

**Step 2g — `plugins/strategic-implementation/agents/api-contract.md`** `[parallel group: A]`
- What:
  1. Add after opening paragraph: `**Not in scope:** Database schema or storage format (owned by data-model). Technical implementability of the interface (owned by technical-expert).`
  2. Remove `## Step 7 — Contract Capture` entirely (per spec §4.2.1 — intentional scope reduction; logged in session-3-log.md)
  3. Strengthen Step 6 (Internal Consistency): add flag for naming inconsistencies across interfaces in the same plan (camelCase vs snake_case, different terms for the same concept)
  4. Strengthen Step 4 (Error Contract): add flag if plan introduces new interfaces without specifying the error envelope format
  5. Sharpen Steps 3+5 BLOCK framing: BLOCK if plan modifies an existing interface in a breaking way and known consumers are not named

**Step 2h — `plugins/strategic-implementation/agents/performance.md`** `[parallel group: A]`
- What:
  1. Add after opening paragraph: `**Not in scope:** Database schema decisions (owned by data-model). Dependency bundle size (owned by dependency).`
  2. Merge `## Step 6 — Performance Targets` and `## Step 7 — Concurrency and Load` into `## Step 6 — Targets, Concurrency, and Load`
  3. Sharpen existing Steps 1–6 with research findings: add performance targets for sensitive features; sharpen N+1 pattern; sharpen synchronous blocking op flags; sharpen caching strategy omission flags

**Step 2i — `plugins/strategic-implementation/agents/dependency.md`** `[parallel group: A]`
- What:
  1. Add after opening paragraph: `**Not in scope:** Architectural appropriateness of a dependency's use case (owned by 10k-foot). Runtime security of how the dependency's API is used (owned by security).`
  2. Merge `## Step 3 — License Compatibility` and `## Step 4 — Maintenance Health` into `## Step 3 — Risk Assessment: License and Maintenance Health`; renumber old Step 5→4, old Step 6→5, old Step 7→6. Preserve all flag conditions from both source steps verbatim — only the section header and transitional prose are merged; no flag items removed
  3. Sharpen Step 2 (Necessity) and merged Step 3 with research findings

**Step 2j — `plugins/strategic-implementation/agents/future-proofing.md`** `[parallel group: A]`
- What:
  1. Add after opening paragraph: `**Not in scope:** Feature completeness or architectural correctness (owned by 10k-foot). Code-level implementation correctness (owned by technical-expert).`
  2. Add specificity to Task 4 (Documentation Coverage): flag if a non-obvious decision lacks a 'why' explanation (not just 'what changed'); the flag must name the specific decision and the docs file that should record it
  3. Incorporate all 4 research findings to sharpen Tasks 1–4

**Step 2k — `plugins/strategic-implementation/agents/frontend-engineer.md`** `[parallel group: A]`
- What:
  1. Add after opening skip condition block: `**Not in scope:** Backend API contracts (owned by api-contract). General UX patterns not specific to this plan's front-end changes.`
  2. NO trimming (in-progress baseline file)
  3. NO research findings incorporated (all rejected — see Step 3)

**Step 3 — Create `session-3-log.md`** _(sequential, after parallel group A)_
- Files: `docs/strategic-implementation/2026-04-05-plugin-skills-agents-improvement/session-3-log.md` (new)
- What: After all 11 agent edits are complete, create the deviation log. Record each rejected research finding as an `ambiguity-decision` entry.

### Deliverables & Tests

- [ ] All 11 agent files contain a "Not in scope" line immediately after the opening description paragraph (or opening skip condition for frontend-engineer)
  Test: `grep -c "Not in scope"` in each of 11 files returns ≥1

- [ ] 10 agents have review task sections trimmed to ≤50 lines (frontend-engineer excluded)
  Test: Count from the first review-task heading to the line before `## Processing Project Learnings` — all ≤50. Per-agent anchors: `10k-foot`, `technical-expert`, `scope-limiter`, `future-proofing` → first `###` heading; `test-coverage`, `security`, `data-model`, `api-contract`, `performance`, `dependency` → `## Step 1` heading

- [ ] Per-agent trimming targets applied
  Test: `grep "Integration Gaps" plugins/strategic-implementation/agents/technical-expert.md` → 0 results; `grep "Contract Capture" plugins/strategic-implementation/agents/api-contract.md` → 0 results; `grep "Step 4 — Individual Test Correctness" plugins/strategic-implementation/agents/test-coverage.md` → 0 results; `grep "Step 4 — Test Quality" plugins/strategic-implementation/agents/test-coverage.md` → 1 result; `grep "Step 8a" plugins/strategic-implementation/agents/test-coverage.md` → 0 results; `grep "New runtime dependencies" plugins/strategic-implementation/agents/test-coverage.md` → 1 result; `grep "Step 5 — Input Trust" plugins/strategic-implementation/agents/security.md` → 0 results; `grep "Step 5 — Untrusted" plugins/strategic-implementation/agents/security.md` → 1 result; `grep "Step 3 — License Compatibility" plugins/strategic-implementation/agents/dependency.md` → 0 results; `grep "Step 3 — Risk Assessment" plugins/strategic-implementation/agents/dependency.md` → 1 result

- [ ] Research findings incorporated or explicitly rejected
  Test: `session-3-log.md` exists with one `ambiguity-decision` entry per rejected finding; sample incorporation checks: `grep -i "downstream consumer" plugins/strategic-implementation/agents/10k-foot.md` → ≥1; `grep -i "initialization order" plugins/strategic-implementation/agents/technical-expert.md` → ≥1

- [ ] "Processing Project Learnings" boilerplate unchanged
  Test: `grep -c "Processing Project Learnings" plugins/strategic-implementation/agents/*.md` — each returns ≥1

### Constraints
- Target: ≤ ~1000 LOC edited or written this session
- Do NOT touch: `clarify/SKILL.md`, `implementation-reviser/SKILL.md`, `post-mortem/SKILL.md`, `implementation-drafter/SKILL.md` (Session 4)
- `frontend-engineer.md`: "Not in scope" line only — no trimming, no research
- `test-coverage.md`: old `## Step 8a` content (three subsections) must be preserved in full; renamed to `## Step 8`
- `security.md`: all BLOCK criteria must survive the Steps 5+6 merge unchanged
- `dependency.md`: all flag conditions from Steps 3 and 4 must be preserved verbatim in the merged step
- "Processing Project Learnings" boilerplate unchanged in all 11 agents
- "Output Format" sections unchanged in all 11 agents
- Step 3 (session-3-log.md) created after all parallel edits complete
