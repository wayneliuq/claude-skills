# Implementation Spec: Plugin Skills and Agents Improvement
_Status: Draft — Decisions Resolved | Last updated: 2026-04-05_

---

## 1. Context

The `strategic-implementation` plugin contains 12 skills and 11 agents forming a structured planning workflow — from clarification through spec drafting, sessionization, agent review, execution, and post-mortem. The plugin has matured, but a detailed review reveals three categories of problems.

First, correctness and portability bugs: hardcoded absolute paths, a mismatched learning category tag causing cross-contamination between two agents, a missing branch safety check in the execution skill, an external skill dependency in the fast-path, and inconsistent file-surfacing behavior (some skills announce what they wrote, others silently create files).

Second, review agents have accumulated steps over time without pruning — several now spend 40–80 lines on checks where only the first 3–4 produce high-signal findings. Improving them using only existing analysis has limits; a research pass using parallel web-search agents can identify current best practices per domain that aren't captured in the current prompts.

Third, small gaps in best practices: the clarify skill always asks questions even when none are warranted, agents don't declare their scope boundaries (causing duplicate flags), and one agent's learning category is wrong.

Five files already have in-progress improvements (frontend-engineer, test-coverage, executing-plans, implementation-drafter, session-plan) that are additive and correct — they are the starting baseline.

> **Feedback:** _(leave blank, or type your thoughts, corrections, or questions about this section)_

---

## 2. What We're Building

A targeted improvement pass over every skill and agent in the plugin, in three phases: (1) fix correctness and portability bugs first, including making all file creation and edit events explicitly surface the path to the user; (2) run parallel research agents — one per review agent domain — to identify the highest-impact best practices from current agentic/LLM reviewer patterns, then incorporate the filtered findings into each agent's prompts; (3) apply targeted best-practice additions to skills (clarify fast-skip, reviser trigger sharpening, post-mortem compression, subsection feedback slots in the drafter). The result is a portable, consistent, well-scoped plugin where every file operation is visible to the user and every review agent focuses on its highest-signal checks.

> **Feedback:** _(leave blank, or type your thoughts, corrections, or questions about this section)_

---

## 3. Success Criteria

- [ ] `grep -r "/Users/" plugins/strategic-implementation/` returns no results
- [ ] `future-proofing` agent's learning filter tag is `#future-proofing`; the deviation category enum in `executing-plans` and `post-mortem` includes `future-proofing`
- [ ] `executing-plans` Step 0 includes an explicit git branch check that surfaces the current branch before execution if on `main` or `master`
- [ ] `session-plan` rule 9 specifies `Glob` as the verification mechanism for file paths
- [ ] `strategic-implementation` fast-path does not reference `superpowers:writing-plans`; produces a valid implementation guide at the standard path
- [ ] Every file *creation* event in any skill is immediately followed by: `_[filename] saved to docs/strategic-implementation/[feature-folder]/[filename]_`
- [ ] Every file *edit* event in any skill is immediately followed by: `_docs/strategic-implementation/[path] updated — [one-line description of what changed]_`
- [ ] Before agent edits begin, parallel research agents produce ≤5 candidate improvements per agent domain, filtered to the highest-impact 20%; each finding is incorporated or explicitly rejected with a reason
- [ ] Every agent file contains a "Not in scope" line naming at least one adjacent agent that owns that domain
- [ ] Agent review task sections are at most 50 lines each (first `##` review task heading to the Processing Project Learnings section)
- [ ] `clarify` skill has an explicit fast-skip path when nothing is ambiguous
- [ ] `implementation-reviser` Step 11 uses count-based trigger criteria with no subjective language
- [ ] `implementation-drafter` document format includes a `> **Feedback:**` slot after each `####` subsection within Section 4
- [ ] All 5 already-modified files are in consistent final state

> **Feedback:** _(leave blank, or type your thoughts, corrections, or questions about this section)_

---

## 4. Detailed Specification

### 4.0 — Research Phase (Pre-Improvement)

**Current state:** Agent improvements are informed solely by analysis of current file content. This is bounded by existing knowledge of what high-quality review agents look like.

**After this change:** Before improving any agent file, run 10 parallel research sub-agents — one per review agent domain. Each sub-agent:

1. Web-searches for: best practices for LLM `[domain]` review agents at plan-review time (not code-review time), effective prompt patterns for agentic `[domain]` reviewers, and what experienced practitioners include in `[domain]` review checklists for software planning.
2. Filters findings to ≤5 candidate improvements that are: (a) specific and actionable — not "be thorough" but "flag X when Y condition", (b) not already covered by the current agent's checks, and (c) directly applicable to plan-level review (not post-implementation review).
3. Returns a ranked list with one-sentence rationale per finding.

The 10 domains: architecture/alignment (`10k-foot`), technical implementation (`technical-expert`), scope and sizing (`scope-limiter`), test strategy (`test-coverage`), security (`security`), data modeling (`data-model`), API contracts (`api-contract`), performance at scale (`performance`), dependency management (`dependency`), structural maintainability (`future-proofing`).

Research findings are used to validate and augment the 4.2.1 trimming decisions — findings that confirm a current check should be kept are noted; findings that identify a missing high-value check that fits within 50 lines are incorporated.

**Key details:** Research agents do not modify files — they return findings. Incorporation decisions are made in the same session that edits the agent file. Any finding that would require adding a new agent or changing workflow logic is rejected (scope boundary).

> **Feedback:** _(leave blank, or type your thoughts, corrections, or questions about this section)_

---

### 4.1 — Tier 1: Portability and Correctness Bugs

#### 4.1.1 — Absolute Paths in `sessionize/SKILL.md` and `session-plan/SKILL.md`

**Current state:** `sessionize` Steps 4 and 5 reference agents by absolute file paths (`/Users/qiangliu/...`). `session-plan` Step 3 has the same issue. These paths are hardcoded to one machine.

**After this change:** All agent path references in both files are replaced with registered plugin agent type names.

| Old path suffix | New agent type name |
|---|---|
| `agents/10k-foot.md` | `strategic-implementation:10k-foot` |
| `agents/technical-expert.md` | `strategic-implementation:technical-expert` |
| `agents/future-proofing.md` | `strategic-implementation:future-proofing` |
| `agents/security.md` | `strategic-implementation:security` |
| `agents/data-model.md` | `strategic-implementation:data-model` |
| `agents/api-contract.md` | `strategic-implementation:api-contract` |
| `agents/test-coverage.md` | `strategic-implementation:test-coverage` |
| `agents/performance.md` | `strategic-implementation:performance` |
| `agents/dependency.md` | `strategic-implementation:dependency` |
| `agents/scope-limiter.md` | `strategic-implementation:scope-limiter` |
| `agents/frontend-engineer.md` | `strategic-implementation:frontend-engineer` |

> **Feedback:** _(leave blank, or type your thoughts, corrections, or questions about this section)_

---

#### 4.1.2 — `future-proofing` Learning Category Tag

**Current state:** `future-proofing` agent filters on `#architecture` — the same tag as `10k-foot`. The deviation category enum in `executing-plans` and `post-mortem` has no `future-proofing` entry.

**After this change:**
- `future-proofing.md`: change `#architecture` → `#future-proofing` in the Processing Project Learnings section
- `executing-plans/SKILL.md`: add `future-proofing` to the agent category enum
- `post-mortem/SKILL.md`: add `future-proofing` to the category list wherever the enum appears

**Key details:** This is a clean break with no migration. [HARD DECISION — single-user project, no existing project-learnings files to migrate.]

> **Feedback:** _(leave blank, or type your thoughts, corrections, or questions about this section)_

---

#### 4.1.3 — Branch Check in `executing-plans`

**Current state:** "Never start on main/master" is a bottom-of-file constraint, not enforced at start.

**After this change:** Step 0 adds immediately after loading files:

> "Run `git branch --show-current`. If result is `main` or `master`: surface — 'You are on `[branch]`. Execution will write code to this branch. Confirm to proceed, or switch branches first.' Wait for explicit confirmation before proceeding to Step 1. If on any other branch: announce the branch name and continue."

> **Feedback:** _(leave blank, or type your thoughts, corrections, or questions about this section)_

---

#### 4.1.4 — File Path Verification Mechanism in `session-plan`

**Current state:** Rule 9 says "verify each referenced path" with no specified mechanism.

**After this change:** Rule 9 becomes: "Before finalizing the plan, verify each referenced file path using the `Glob` tool. A path is verified if Glob returns a match. If a file does not exist: remove the reference, substitute the correct path, or flag it as `[PATH NOT FOUND — verify before executing]`. Do not silently omit unverified paths."

> **Feedback:** _(leave blank, or type your thoughts, corrections, or questions about this section)_

---

#### 4.1.5 — Fast-Path External Dependency in `strategic-implementation`

**Current state:** Step 2 fast-path invokes `superpowers:writing-plans` — external to this plugin.

**After this change:** The fast-path inlines a minimal plan creation step:

> "Create an implementation guide at `docs/strategic-implementation/YYYY-MM-DD-<feature-name>/implementation-guide.md` using the single-session template from `implementation-guide/SKILL.md`. Populate: What (one paragraph from the request), Why (from the request), Out of scope (minimum two entries), Key decisions (none for fast-path), and a single Session 1 block with the deliverable as its goal, estimated size S or M, `Review agents: none`. Save the file and announce: `_implementation-guide.md saved to docs/strategic-implementation/YYYY-MM-DD-<feature-name>/implementation-guide.md_`. Then invoke `strategic-implementation:executing-plans`."

> **Feedback:** _(leave blank, or type your thoughts, corrections, or questions about this section)_

---

#### 4.1.6 — File Surfacing Consistency (Cross-Cutting) [NEW]

**Current state:** File creation/edit surfacing is inconsistent across skills:
- `implementation-drafter`, `sessionize`, `session-plan`: already have explicit confirm lines — **no change needed**
- `executing-plans`: creates `session-N-log.md` on first deviation with no surface announcement
- `post-mortem`: writes `session-N-postmortem.md` and updates `project-learnings.md` without a consolidated surface step
- `bug-fix`: creates or appends to `session-N-log.md` without surfacing
- File *edits* (implementation guide status updates in `executing-plans`, deviation additions, meaningful deviation block updates): never surfaced

**After this change:** The rule is uniform across all skills:

**File creation:** Immediately after writing any new file, announce:
> `_[filename] saved to docs/strategic-implementation/[feature-folder]/[filename]_`

**File edit:** Immediately after editing an existing file, announce:
> `_docs/strategic-implementation/[feature-folder]/[filename] updated — [one-line description of what changed]_`

Files requiring updates to add surfacing: `executing-plans/SKILL.md` (deviation log creation + implementation guide status edits + meaningful deviation block edits), `post-mortem/SKILL.md` (both artifact writes), `bug-fix/SKILL.md` (deviation log creation/append).

> **Feedback:** _(leave blank, or type your thoughts, corrections, or questions about this section)_

---

### 4.2 — Tier 2: Agent Signal/Token Ratio

#### 4.2.1 — Trim Low-Signal Review Steps (All 10 Agents)

**Current state:** Each agent has 4–8 review tasks totaling 40–80 lines. The first 3–4 checks produce the findings that result in FLAGS or BLOCKs; later checks are redundant, too generic, or covered by adjacent agents.

**After this change:** Each agent's review task section is trimmed to ≤50 lines. Trimming criteria: remove or merge any check that is (a) covered by an earlier check in the same agent, (b) generic enough to apply to nearly every plan without producing a specific finding, or (c) duplicated by another agent's primary responsibility. Research findings from 4.0 inform what is kept and whether anything is added.

Per-agent trimming targets:

| Agent | Action |
|---|---|
| `10k-foot` | Merge "Gaps and Misalignment" into "Alignment with Desired End-Product" — same question, two phrasings |
| `technical-expert` | Remove Step 4 "Integration Gaps" — covered by `api-contract`; add scope note |
| `scope-limiter` | Keep all 5 tasks; trim prose only |
| `test-coverage` | Merge Steps 4+5 (correctness + fragility) into one step; Step 8a stays in full |
| `security` | Merge Steps 5+6 (input trust + secrets) into one "untrusted inputs" step |
| `data-model` | Keep all 6 steps; trim prose only (high-stakes domain) |
| `api-contract` | Remove Step 7 (contract capture) — documentation reminder, not a review finding |
| `performance` | Merge Steps 6+7 (targets + concurrency) into one step |
| `dependency` | Merge Steps 3+4 (license + maintenance health) into one "is this safe to take on?" step |
| `future-proofing` | Keep all 4 tasks; add specificity to task 4 — "vague" flags are not actionable |

> **Feedback:** _(leave blank, or type your thoughts, corrections, or questions about this section)_

---

#### 4.2.2 — Explicit Scope Boundaries in Each Agent

**Current state:** Agents implicitly share adjacent domains — `10k-foot`/`future-proofing` overlap on structural issues; `technical-expert`/`api-contract` overlap on integration gaps.

**After this change:** Every agent adds a "Not in scope" line immediately after its opening description paragraph:

| Agent | Not in scope |
|---|---|
| `10k-foot` | "Implementation details, library choices, test strategy (`technical-expert`, `test-coverage`). Naming and structural quality (`future-proofing`)." |
| `technical-expert` | "Test correctness or coverage strategy (`test-coverage`). Interface completeness between components (`api-contract`)." |
| `scope-limiter` | "Whether the feature is the right feature (`10k-foot`). Whether the approach is technically sound (`technical-expert`)." |
| `test-coverage` | "Whether code is technically correct (`technical-expert`). File/folder placement (`future-proofing`)." |
| `security` | "Authorization UI patterns (`frontend-engineer`). Business-logic validation (`technical-expert`)." |
| `data-model` | "Query performance optimization (`performance`). API response shape (`api-contract`)." |
| `api-contract` | "Database schema or storage format (`data-model`). Technical implementability (`technical-expert`)." |
| `performance` | "Database schema decisions (`data-model`). Dependency bundle size (`dependency`)." |
| `dependency` | "Architectural appropriateness of a dependency (`10k-foot`). Runtime security of its API usage (`security`)." |
| `future-proofing` | "Feature completeness or correctness (`10k-foot`). Code-level implementation correctness (`technical-expert`)." |
| `frontend-engineer` | "Backend API contracts (`api-contract`). General UX patterns not specific to this plan." |

> **Feedback:** _(leave blank, or type your thoughts, corrections, or questions about this section)_

---

### 4.3 — Tier 3: Best Practice Additions

#### 4.3.1 — Fast-Skip in `clarify`

**Current state:** `clarify` always emits assumptions and questions, even when the request leaves nothing ambiguous.

**After this change:** Add before Step 2:

> "If the request is fully specified — every assumption you would make is explicitly confirmed in the request text, and no question would change the approach — skip to Step 4 and state: 'The request is fully specified. Proceeding to scope assessment.' Do not fabricate questions to fill the format."

> **Feedback:** _(leave blank, or type your thoughts, corrections, or questions about this section)_

---

#### 4.3.2 — Sharpen `implementation-reviser` Step 11 Trigger

**Current state:** Step 11 leads with "if this revision round made changes that significantly restructure the spec" — subjective trigger.

**After this change:** Remove the vague introductory sentence. Step 11 leads directly with the count-based rule that already exists in the file:

> "If two or more of the following are true in this revision round: (1) a new component or system was added to Section 4, (2) Section 5 Scope Boundary was substantially expanded or contracted, (3) a Key Decision in Section 6 was reversed or a new major technical decision was added, (4) the change now affects a different area of the system than originally described — then re-run architecture and UX reviews."

> **Feedback:** _(leave blank, or type your thoughts, corrections, or questions about this section)_

---

#### 4.3.3 — Compress `post-mortem` Step 7

**Current state:** Step 7 (cross-session grep) takes ~15 lines to describe a keyword search.

**After this change:** Compress Step 7 to:

> "Extract 2–3 keywords from each deviation's 'What actually happened' field. Search for those keywords across all other `session-*-log.md` files under `docs/strategic-implementation/`. If a keyword pattern appears in 2+ other sessions: note it as a cross-session pattern candidate. Promotion to `#multi-session` requires explicit user confirmation."

> **Feedback:** _(leave blank, or type your thoughts, corrections, or questions about this section)_

---

#### 4.3.4 — Subsection Feedback Slots in `implementation-drafter` [NEW]

**Current state:** The `implementation-drafter` document format places one `> **Feedback:**` slot at the end of each major section (`##`). Within Section 4, which can have many `####` subsections, there is only one slot for all of them.

**After this change:** The document format in `implementation-drafter/SKILL.md` is updated so that within Section 4, each `####` subsection ends with its own feedback slot. The section-level feedback slot at the end of Section 4 is retained for overall section feedback.

This applies to all future specs generated by the drafter. It does not affect the format of sections 1–3 or 5–8 (those keep their existing single slot).

> **Feedback:** _(leave blank, or type your thoughts, corrections, or questions about this section)_

---

> **Feedback:** _(leave blank, or type your overall thoughts on Section 4)_

---

## 5. Scope Boundary

The following are explicitly out of scope for this change:

- **Adding new agents or skills:** Improvements to existing files only — no new review agents, workflow skills, or templates.
- **Changing workflow logic:** How skills connect to each other is unchanged — only individual skill/agent prompt quality.
- **Research findings that require new agents or workflow steps:** Research in 4.0 informs improvements to existing agent content only; structural workflow changes are a separate initiative.
- **Research phase for skills (not agents):** The parallel research pass covers the 10 review agents only — skills have workflow-specific context that research wouldn't improve as reliably as targeted analysis.
- **Restructuring the implementation guide template format:** Not changed in this pass.
- **Adding learning categories beyond `future-proofing`:** Only the inconsistency fix is in scope.
- **Improving already-in-progress files beyond their current changes:** The 5 modified files are accepted as baseline except where a Tier 1 fix requires touching the same file.

> **Feedback:** _(leave blank, or type your thoughts, corrections, or questions about this section)_

---

## 6. Key Decisions

**Already decided:**
- **Tier 1 fixes before Tier 2/3:** Correctness and portability bugs addressed first.
- **Replace absolute paths with registered agent type names:** More robust than relative paths; works regardless of installation location.
- **Keep "Processing Project Learnings" boilerplate in all agents unchanged:** Required for the injection mechanism to work.
- **Do not reduce BLOCK criteria specificity:** BLOCK thresholds are intentionally narrow.
- **Accept the 5 in-progress file changes as baseline:** TDD ordering, parallel group verification, path verification, precondition-dependent behavior rules are all correct.
- **`future-proofing` tag is a clean break:** [HARD DECISION] Single-user project — no migration needed.
- **Research phase covers agents only, not skills:** Skills are improved via analysis; agents get both analysis and research-informed improvements.
- **File surfacing is uniform for all creates and edits:** [HARD DECISION] Every file operation is visible to the user — no silent writes.

**Open (must be resolved before execution):**
- None — all decisions resolved.

> **Feedback:** _(leave blank, or type your thoughts, corrections, or questions about this section)_

---

## 7. Risks & Unknowns

- **Over-trimming agent checks:** Reducing review steps risks missing real issues. Mitigation: trimming criteria are specific — only removing duplicate-coverage checks and generic-applies-to-everything checks, not domain-specific signal.
- **Research agents return generic LLM advice:** Web search may return "be thorough" rather than domain-specific reviewer patterns. Mitigation: queries are scoped to "plan-level review, not code-review" to target the right use case.
- **Research findings conflict across domains:** Two agents may receive contradictory guidance. Mitigation: each research agent is scoped to its domain; the incorporating session decides per-agent.
- **File surfacing verbosity:** Surfacing every edit increases output length. Mitigation: confirmations are single lines; the increase is acceptable given the transparency benefit.
- **Scope boundary lines create blind spots:** An agent may skip an issue it sees assuming another agent owns it. Mitigation: boundaries say "do not *review* X" — agents can still flag severe issues outside their primary scope.

> **Feedback:** _(leave blank, or type your thoughts, corrections, or questions about this section)_

---

## 8. Alternatives Considered

- **Full rewrite of each agent from scratch:** Rejected — targeted edits preserve domain calibration from real use.
- **Consolidating overlapping agents:** Rejected — parallel review redundancy is a feature; explicit scope lines remove output duplication without removing review depth.
- **Skip research phase, use analysis only:** Rejected — analysis is bounded by existing knowledge; web research adds current practitioner patterns that may not be in training data for specific agentic review domains.
- **Single-session execution of all 25 files:** Rejected — too large; sessionization with clear success verification between sessions is required.
- **Automated prompt compression (LLM pass):** Rejected — mechanical compression loses nuance; human-directed trimming guided by domain knowledge is more reliable.

> **Feedback:** _(leave blank, or type your thoughts, corrections, or questions about this section)_

---

### Revision Log

**Round 1** | 2026-04-05
- **Changes made:**
  - Added Section 4.0 (Research Phase): parallel research agents per agent domain before editing
  - Added Section 4.1.6 (File Surfacing Consistency): uniform file create/edit announcement across all skills
  - Added Section 4.3.4 (Subsection Feedback Slots): `implementation-drafter` format update
  - Added feedback slots after every `####` subsection in Section 4 (per user feedback)
  - Updated Section 2 (What We're Building) to reflect research phase and file surfacing
  - Added 3 new success criteria (research phase, file creation surfacing, file edit surfacing)
  - Updated Scope Boundary with research phase limits
  - Updated Key Decisions: added research-covers-agents-only and file-surfacing-is-uniform (Hard Decision)
  - Updated Risks and Alternatives for research phase and file surfacing
- **Input not incorporated:** None — all feedback incorporated.
- **Hard decisions recorded this round:** "File surfacing is uniform for all creates and edits"
- **Open items resolved:** none were open
- **Open items remaining:** none
