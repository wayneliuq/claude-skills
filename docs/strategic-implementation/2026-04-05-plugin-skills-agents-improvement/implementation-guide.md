# Implementation Plan: Plugin Skills and Agents Improvement
_Derived from: Implementation Spec — Plugin Skills and Agents Improvement_
_Status: Draft | Last updated: 2026-04-05_

---

## Overview
- **What:** A targeted, research-informed improvement pass over every skill and agent in the `strategic-implementation` plugin — fixing portability bugs, standardizing file surfacing, trimming low-signal agent review steps, adding explicit scope boundaries to agents, and applying best-practice additions to skills.
- **Why:** Hardcoded absolute paths break portability; a mismatched learning category tag cross-contaminates two agents' learnings; review agents have accumulated steps that dilute output and inflate tokens; file operations are inconsistently surfaced to the user.
- **Out of scope:** Adding new agents or skills; changing how skills connect to each other (workflow logic); restructuring the implementation-guide template format; adding learning categories beyond `future-proofing`; extending the 5 already-in-progress files beyond their baseline state (except where Tier 1 fixes require touching the same file).
- **Key decisions:**
  - Tier 1 fixes before Tier 2/3 — correctness before optimization
  - Absolute paths → registered agent type names (`strategic-implementation:X`) — more robust than relative paths, resolved by Claude Code plugin registry
  - "Processing Project Learnings" boilerplate stays unchanged in all agents
  - BLOCK criteria specificity not reduced in any agent
  - 5 in-progress files (frontend-engineer, test-coverage, executing-plans, implementation-drafter, session-plan) accepted as baseline
  - `future-proofing` tag change is a clean break — no migration [HARD DECISION]
  - File surfacing is uniform for all creates and edits — no silent writes [HARD DECISION]
  - Research phase covers agents only, not skills
  - Integration Gaps concern migrates from `technical-expert` to `api-contract` via the "Not in scope" line — this is the explicit handoff, not a silent removal

---

## Sessions

### Session 1: Research Phase
**Status:** `complete`
**Goal:** Gather and synthesize current best practices for all 10 review agent domains via parallel web research, producing a prioritized findings document.

**Deliverables & Tests:**
- [ ] Deliverable: `docs/strategic-implementation/2026-04-05-plugin-skills-agents-improvement/research-findings.md` exists with a section for each of the 10 agent domains
  Test: File exists; `grep -c "###" research-findings.md` returns 10 (one `###` heading per domain); each section contains ≥1 and ≤5 numbered findings; no finding entry is shorter than 20 words (filters out placeholder stubs)

**Files affected:**
- `docs/strategic-implementation/2026-04-05-plugin-skills-agents-improvement/research-findings.md` (new)

**Docs to update:** none
**Estimated size:** S (<200 LOC)
**Hard decisions applied:** Research phase covers agents only, not skills
**Review agents:** none
**Contextual notes:** This session produces a research artifact that Session 3 reads before beginning any agent edits. research-findings.md is organized with one `###` section per agent domain, each containing ranked findings. Session 3 treats this file as a required pre-read.

#### Meaningful Deviations
_None — session not yet executed_

---

### Session 2: Tier 1 — Portability, Correctness, and File Surfacing
**Status:** `complete`
**Goal:** Fix all 6 correctness and portability issues in the plugin's orchestration skills and standardize file surfacing across all skills that create or edit files.

**Pre-conditions:**
- Read `plugins/strategic-implementation/.claude-plugin/plugin.json` and confirm the registered agent type names match the replacement strings before any path substitution begins
- Read `plugins/strategic-implementation/skills/sessionize/SKILL.md` and `session-plan/SKILL.md` learning injection logic (Steps 2a) to confirm they read the agent's category tag dynamically from the agent file — not from a hardcoded enum — before changing `future-proofing.md`'s tag
- Run `grep -r "superpowers:writing-plans" plugins/strategic-implementation/` and confirm all occurrences are in `strategic-implementation/SKILL.md` only; note any other files that contain the reference

**Deliverables & Tests:**
- [ ] Deliverable: All absolute paths removed from `sessionize/SKILL.md` and `session-plan/SKILL.md`; each agent reference replaced with its registered type name; an inline comment added to each file noting "Agent type names are resolved by the Claude Code plugin registry — see .claude-plugin/plugin.json"
  Test: `grep -r "/Users/" plugins/strategic-implementation/skills/sessionize/ plugins/strategic-implementation/skills/session-plan/` returns no results; `grep "strategic-implementation:" plugins/strategic-implementation/skills/sessionize/SKILL.md` returns ≥9 matches

- [ ] Deliverable: `future-proofing` learning tag corrected; deviation category enum updated in all three consuming files
  Test: `grep "#architecture" plugins/strategic-implementation/agents/future-proofing.md` returns no results; `grep "future-proofing" plugins/strategic-implementation/skills/executing-plans/SKILL.md` returns a match; same grep in `post-mortem/SKILL.md` returns a match; same grep in `bug-fix/SKILL.md` returns a match (all three category enum consumers updated)

- [ ] Deliverable: Branch check added to `executing-plans` Step 0
  Test: Read `executing-plans/SKILL.md` Step 0 — contains `git branch --show-current`, names `main` and `master` as branches requiring user confirmation, and waits for explicit confirmation before proceeding to Step 1

- [ ] Deliverable: Glob verification added to `session-plan` rule 9
  Test: Read `session-plan/SKILL.md` Step 2 rule 9 — contains the phrase "Glob tool"; describes the `[PATH NOT FOUND]` annotation for unverified paths

- [ ] Deliverable: `superpowers:writing-plans` removed from `strategic-implementation/SKILL.md` fast-path; replaced with inline implementation guide creation
  Test: `grep "superpowers:writing-plans" plugins/strategic-implementation/skills/strategic-implementation/SKILL.md` returns no results; fast-path block contains instructions to create and save `implementation-guide.md` at the standard path and invoke `executing-plans`

- [ ] Deliverable: File surfacing announcements added to `executing-plans`, `post-mortem`, and `bug-fix`
  Test: Read `executing-plans/SKILL.md` — Step 3 deviation log creation block contains `_saved to docs/strategic-implementation/..._` format; implementation guide status update steps contain `_updated —_` format. Read `post-mortem/SKILL.md` — Step 10 write blocks each contain `_saved to_` announcement. Read `bug-fix/SKILL.md` — Step 3e deviation log creation contains `_saved to_` announcement

**Files affected:**
- `plugins/strategic-implementation/skills/sessionize/SKILL.md`
- `plugins/strategic-implementation/skills/session-plan/SKILL.md`
- `plugins/strategic-implementation/agents/future-proofing.md`
- `plugins/strategic-implementation/skills/executing-plans/SKILL.md`
- `plugins/strategic-implementation/skills/post-mortem/SKILL.md`
- `plugins/strategic-implementation/skills/bug-fix/SKILL.md`
- `plugins/strategic-implementation/skills/strategic-implementation/SKILL.md`

**Docs to update:** none
**Estimated size:** M (200–500 LOC)
**Hard decisions applied:**
- `future-proofing` tag change is a clean break [HARD DECISION]
- File surfacing is uniform for all creates and edits [HARD DECISION]
**Review agents:** none
**Contextual notes:** Session touches 7 files but each edit is surgical. The `future-proofing` tag fix only needs the agent file and the three enum consumers (executing-plans, post-mortem, bug-fix) — sessionize and session-plan read the tag dynamically from the agent file, so no filter logic change is required in them. Confirm this pre-condition before editing.

#### Meaningful Deviations
_None — session not yet executed_

---

### Session 3: Agent Scope Boundaries and Signal Trimming
**Status:** `complete`
**Goal:** Improve all 11 review agents by adding explicit scope boundaries and trimming low-signal review steps in 10 of them, incorporating the highest-impact findings from the research phase.

**Pre-conditions:**
- Session 1 complete: `research-findings.md` exists and contains exactly 10 `###` sections. Read the full file before beginning any agent edits.
- Confirm research-findings.md structure: for each agent domain, note the ≤5 findings and decide before touching the file whether each is incorporated (added to agent) or rejected (logged in deviation log with reason).

**Deliverables & Tests:**
- [ ] Deliverable: All 11 agent files contain a "Not in scope" line immediately after the opening description paragraph
  Test: `grep -c "Not in scope" plugins/strategic-implementation/agents/10k-foot.md plugins/strategic-implementation/agents/technical-expert.md plugins/strategic-implementation/agents/scope-limiter.md plugins/strategic-implementation/agents/test-coverage.md plugins/strategic-implementation/agents/security.md plugins/strategic-implementation/agents/data-model.md plugins/strategic-implementation/agents/api-contract.md plugins/strategic-implementation/agents/performance.md plugins/strategic-implementation/agents/dependency.md plugins/strategic-implementation/agents/future-proofing.md plugins/strategic-implementation/agents/frontend-engineer.md` — each returns ≥1

- [ ] Deliverable: 10 agents (all except frontend-engineer, which already has in-progress changes) have review task sections trimmed to ≤50 lines each
  Test: For each of the 10 agents, count lines from the first `###` heading in the Review Tasks section to the line immediately before `## Processing Project Learnings` — all ≤50. (frontend-engineer is excluded from this count.)

- [ ] Deliverable: Per-agent trimming targets from spec applied
  Test: `grep -c "Integration Gaps" plugins/strategic-implementation/agents/technical-expert.md` returns 0; `grep -c "Contract Capture" plugins/strategic-implementation/agents/api-contract.md` returns 0; other merges verified by reading each affected file

- [ ] Deliverable: Research findings incorporated or explicitly rejected
  Test: Deviation log entries exist for each research finding that was rejected (type: `ambiguity-decision`, describing the finding and rejection reason); OR the finding is traceable to a specific line change in an agent file

**Files affected:**
- `plugins/strategic-implementation/agents/10k-foot.md`
- `plugins/strategic-implementation/agents/technical-expert.md`
- `plugins/strategic-implementation/agents/scope-limiter.md`
- `plugins/strategic-implementation/agents/test-coverage.md`
- `plugins/strategic-implementation/agents/security.md`
- `plugins/strategic-implementation/agents/data-model.md`
- `plugins/strategic-implementation/agents/api-contract.md`
- `plugins/strategic-implementation/agents/performance.md`
- `plugins/strategic-implementation/agents/dependency.md`
- `plugins/strategic-implementation/agents/future-proofing.md`
- `plugins/strategic-implementation/agents/frontend-engineer.md` (scope boundary line only — no trimming)

**Docs to update:** none
**Estimated size:** M (200–500 LOC)
**Hard decisions applied:** Integration Gaps removed from `technical-expert`; concern assigned to `api-contract` via "Not in scope" line — this is the explicit handoff, not a silent removal
**Review agents:** none
**Contextual notes:** All edits are plain-text markdown prompt files. The "Not in scope" lines for each agent are specified in the spec (Section 4.2.2). Per-agent trimming targets are specified in the spec (Section 4.2.1). frontend-engineer gets only the scope boundary line, not trimming, because it is one of the 5 baseline-accepted in-progress files.

#### Meaningful Deviations
_None — session not yet executed_

---

### Session 4: Skill Best-Practice Additions
**Status:** `pending`
**Goal:** Apply four targeted best-practice improvements to skills: clarify fast-skip, reviser trigger precision, post-mortem Step 7 compression, and implementation-drafter subsection feedback format.

**Pre-conditions:**
- Session 2 complete: `post-mortem/SKILL.md` already has file surfacing changes from Session 2 (Step 10 write blocks). This session edits only Step 7. Do not disturb the Session 2 changes.

**Deliverables & Tests:**
- [ ] Deliverable: `clarify/SKILL.md` has explicit fast-skip path
  Test: Read `clarify/SKILL.md` — text immediately before Step 2 contains a condition: if the request leaves nothing ambiguous, skip to Step 4 and announce "The request is fully specified. Proceeding to scope assessment." The word "fabricate" or equivalent appears in the instruction.

- [ ] Deliverable: `implementation-reviser/SKILL.md` Step 11 leads directly with the count-based trigger
  Test: Read Step 11 — the opening sentence of Step 11 is "If two or more of the following are true in this revision round:" (or equivalent count-first phrasing). The vague phrase "significantly restructure" does not appear in Step 11.

- [ ] Deliverable: `post-mortem/SKILL.md` Step 7 is ≤5 lines
  Test: Count lines in the Step 7 block (from `## Step 7` heading to the next `## Step` heading) — ≤5 lines of content (excluding the heading line itself). Step 10 file surfacing block (added in Session 2) is unchanged.

- [ ] Deliverable: `implementation-drafter/SKILL.md` document format includes `> **Feedback:**` slot after each `####` subsection example in Section 4
  Test: Read the document format template in `implementation-drafter/SKILL.md` — every `####` example heading within the Section 4 template block is followed by a `> **Feedback:** _(leave blank...)_` line before the next `####` or `---`; count of `####` headings matches count of `> **Feedback:**` slots within that template block

**Files affected:**
- `plugins/strategic-implementation/skills/clarify/SKILL.md`
- `plugins/strategic-implementation/skills/implementation-reviser/SKILL.md`
- `plugins/strategic-implementation/skills/post-mortem/SKILL.md` _(Step 7 only — Session 2 already modified Step 10 file surfacing in this file)_
- `plugins/strategic-implementation/skills/implementation-drafter/SKILL.md`

**Docs to update:** none
**Estimated size:** S (<200 LOC)
**Hard decisions applied:** none
**Review agents:** none
**Contextual notes:** `post-mortem/SKILL.md` was modified in Session 2 for file surfacing (Step 10). This session modifies only Step 7. Read the current state of the file before editing to avoid regressing the Session 2 changes.

#### Meaningful Deviations
_None — session not yet executed_

---

## Session Order & Dependencies

- **Session order:** Sessions 1 and 2 in parallel → Session 3 (after Session 1 completes) → Session 4 (after Session 2 completes)
- **Blocking dependencies:**
  - Session 3 requires Session 1 complete: Session 3 reads `research-findings.md` as a required pre-condition before editing any agent file
  - Session 4 requires Session 2 complete: both sessions modify `post-mortem/SKILL.md`; Session 2 must establish the file-surfacing baseline before Session 4 applies the Step 7 compression to avoid conflicting edits
- **Sessions that can run in parallel:** Sessions 1 and 2 share no files and have no logical dependency — start both simultaneously. The convergence point is: Session 1's output unblocks Session 3; Session 2's completion unblocks Session 4. In practice the critical path is `1 → 3` (research must complete before 10 agent files are edited).

---

## Open Questions

None — all decisions resolved.
