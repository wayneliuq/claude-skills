# Session 3 Deviation Log
_Feature: 2026-04-05-plugin-skills-agents-improvement_
_Session: 3 — Agent Scope Boundaries and Signal Trimming_
_Date: 2026-04-06_
_Total deviations: 6_

---

## DEV-001
**Type:** `ambiguity-decision`
**Step:** Step 2b — technical-expert.md
**What the plan said:** Incorporate research finding: "Trace data flow across session boundaries. If two sessions must exchange data but no session defines the interface for that exchange, FLAG it."
**What actually happened:** Finding rejected. This is the Integration Gaps concern being explicitly removed from `technical-expert` per spec §4.2.1 and handed to `api-contract` via the "Not in scope" line. Reinstating the same concern under a research finding heading would contradict the spec's trimming decision and silently undo the handoff.
**Resolution:** Finding not incorporated. The concern is now owned by `api-contract` (Steps 3 and 5 cover interface completeness and consumer coverage for cross-session boundaries).
**Plan gap?** `no`
**Downstream impact?** `no`
**Agent category:** `technical`

---

## DEV-002
**Type:** `ambiguity-decision`
**Step:** Step 2g — api-contract.md
**What the plan said:** Incorporate research finding: "Flag any plan that introduces interfaces without specifying how contracts will be captured and tested."
**What actually happened:** Finding rejected. This is substantively the same concern as Step 7 (Contract Capture) which is explicitly removed per spec §4.2.1 as "documentation reminder, not a review finding." The research finding differs in framing (contract tests vs. contract documentation) but both check whether a durable contract record exists — incorporating it would reinstate what was deliberately removed.
**Resolution:** Finding not incorporated. Step 7 removal stands. The concern is intentionally out of review scope for this plugin — contracts are captured in the agent `.md` files themselves and the Output Format sections are protected from change.
**Plan gap?** `no`
**Downstream impact?** `no`
**Agent category:** `api-contract`

---

## DEV-003
**Type:** `ambiguity-decision`
**Step:** Step 2e — security.md
**What the plan said:** Incorporate research finding: "Flag any plan that defers threat modeling and abuse-case analysis entirely to implementation."
**What actually happened:** Finding rejected. Threat modeling is a prerequisite to plan creation, not something a plan-level reviewer can discover post-hoc. This finding would produce a non-actionable flag on nearly every plan reviewed by the plugin, since most plans do not explicitly document threat modeling exercises. It would inflate output without guiding the user toward a specific change.
**Resolution:** Finding not incorporated. The other three security research findings (UI-layer enforcement, credentials in code, entry points with 4 requirements) were incorporated — these produce specific, actionable flags.
**Plan gap?** `no`
**Downstream impact?** `no`
**Agent category:** `security`

---

## DEV-004
**Type:** `ambiguity-decision`
**Step:** Step 2k — frontend-engineer.md
**What the plan said:** Reject all frontend-engineer research findings (5 findings covering ambiguous interactions, unaccounted UI states, visibility conditions, animation approach, aesthetic reference, hardcoded values, design tokens, layout assumptions, breakpoints, state management, framework pattern conflicts, and custom vs. design system components).
**What actually happened:** All 5 findings rejected in full. `frontend-engineer` is one of the 5 in-progress baseline files accepted as-is for this improvement pass. Session 3 adds the "Not in scope" line only. Incorporating research findings into the content would exceed the baseline-only constraint specified in the implementation guide (Section: Key decisions — "Accept the 5 in-progress file changes as baseline").
**Resolution:** Only the "Not in scope" line was added. All research findings deferred to a future improvement pass if warranted.
**Plan gap?** `no`
**Downstream impact?** `no`
**Agent category:** `frontend`

---

## DEV-005
**Type:** `ambiguity-decision`
**Step:** Deliverables & Tests — ≤50-line budget
**What the plan said:** 10 agents (all except frontend-engineer) have review task sections trimmed to ≤50 lines. Test: count from `## Step 1` to `## Processing Project Learnings` for `test-coverage`, `security`, `data-model`, `api-contract`, `performance`, `dependency`.
**What actually happened:** Budget not achieved for 6 agents. After all spec-required merges (Steps 5+6 in security, Steps 6+7 in performance, Steps 3+4 in dependency, Steps 4+5 in test-coverage) and prose trimming, counts are: test-coverage 115, data-model 79, security 79, performance 74, dependency 75, api-contract 69. Root cause: (a) test-coverage Step 8 must be kept in full (3 subsections with substantial content), making ≤50 lines structurally impossible; (b) the remaining 5 agents each retain 6 steps with spec-required flag conditions preserved verbatim — the `## Step` heading format with `---` separators adds ~18 structural lines that cannot be removed without changing the visual format. The 4 agents using `### Task` format (10k-foot 34, technical-expert 31, scope-limiter 49, future-proofing 39) all pass — their format is inherently more compact.
**Resolution:** User confirmed "close enough, move on." All spec-required merges and prose trims were applied; residual overage is structural. The 4 `### Task` agents pass; the 6 `## Step` agents exceed budget by 19–65 lines.
**Plan gap?** `yes` — the 50-line budget did not account for `## Step` heading format overhead (~18 lines of `---` separators and surrounding whitespace) or the test-coverage Step 8 full-content constraint.
**Downstream impact?** `no`
**Agent category:** `scope`

---

## DEV-006
**Type:** `ambiguity-decision`
**Step:** Deliverables & Tests — `grep -i "initialization order"` check
**What the plan said:** `grep -i "initialization order" plugins/strategic-implementation/agents/technical-expert.md` → ≥1 result
**What actually happened:** The grep returns 0. The concept was incorporated using more precise wording: "Any step that depends on a resource (module, service, config value) that is initialized in a later step" — the phrase is present in the file as "initialized in a later step" not "initialization order." The intent of the finding is present but the grep anchor phrase doesn't match.
**Resolution:** Deviation noted. The finding is substantively incorporated; only the exact grep phrase fails. The session plan test was written before the implementation wording was chosen.
**Plan gap?** `yes` — the test grep anchor was too specific; it should have been `grep -i "initialized in a later"` to match the actual implementation.
**Downstream impact?** `no`
**Agent category:** `technical`
