# Project Learnings
_Last updated: 2026-05-03_
_Sessions tracked: 2_

> **Tag semantics:**
> - `#single-session`: applied only during session plan review. One session of evidence.
> - `#multi-session`: applied during both implementation guide review and session plan review.
>   Promoted from `#single-session` when expanded with evidence from a second session.
>   Requires explicit user confirmation.
>
> **Expansion rule:** Change WHEN (broader situation) OR DO (refined action) — never both simultaneously.
> An expansion requires citing a second concrete case as evidence.
>
> **Pruning rule:** Prune only if the referenced component/pattern no longer exists or has changed
> so fundamentally that the learning is misleading. Requires explicit user confirmation.

---

## scope Learnings

### L-001: Research findings that restate spec-removed checks
**WHEN** a research finding recommends a check that is functionally equivalent to a check the spec explicitly removed — even if framed with different language (e.g., "contract tests" vs. "contract documentation", "data flow tracing" vs. "integration gaps") — **DO** reject the finding and cite the spec's removal decision. Different wording is not different scope.
**Tags:** `#scope` `#single-session`
**Source:** 2026-04-05-plugin-skills-agents-improvement, Session 3
**Evidence:** DEV-001 rejected a "trace data flow" finding that reinstated Integration Gaps (explicitly removed from technical-expert per spec §4.2.1). DEV-002 rejected a "contract tests" finding that reinstated Contract Capture (also explicitly removed per spec §4.2.1). Both arrived in different language but targeted the same removed concern.
**Last reviewed:** 2026-04-06
**Application notes:**

---

### L-003: Line-count budgets for `## Step N` format agents
**WHEN** specifying a line-count budget for agents that use `## Step N` heading format with `---` separators, **DO** add ~18 lines per agent to the budget (to account for separator + surrounding whitespace overhead), or note that `### Task` format achieves the same visual structure with ~40% fewer structural lines. The `## Step` format is not compact enough to fit 6 required steps in 50 lines.
**Tags:** `#scope` `#single-session`
**Source:** 2026-04-05-plugin-skills-agents-improvement, Session 3
**Evidence:** DEV-005 — 6 agents using `## Step N` with `---` separators exceeded the ≤50-line budget after all spec-required merges and prose trimming (counts: 69–115 lines). The 4 agents using `### Task` format all passed (counts: 31–49 lines).
**Last reviewed:** 2026-04-06
**Application notes:**

---

## security Learnings

### L-002: Prerequisite-activity findings don't belong in plan-level reviewers
**WHEN** a research finding recommends flagging the absence of a prerequisite activity (threat modeling, abuse-case analysis, design review) that happens *before* plan creation, **DO** reject it from plan-level review agents — reviewers can only surface gaps in the plan itself, not activities the author should have completed beforehand. These findings produce non-actionable flags on nearly every plan.
**Tags:** `#security` `#single-session`
**Source:** 2026-04-05-plugin-skills-agents-improvement, Session 3
**Evidence:** DEV-003 — "flag any plan that defers threat modeling" was rejected because threat modeling is a prerequisite to plan creation; a plan reviewer cannot discover post-hoc whether it occurred. The finding would produce a flag on nearly every plan without guiding a specific change.
**Last reviewed:** 2026-04-06
**Application notes:**

---

## technical Learnings

### L-004: Grep anchors in session plan tests should use semantic keywords
**WHEN** writing session plan verification greps for incorporated research findings where the exact implementation wording hasn't been decided yet, **DO** use 2–3 distinctive semantic keywords from the finding's core concept rather than a specific phrase — implementation wording is chosen during execution, not during planning, and will often differ from the research finding's language.
**Tags:** `#technical` `#single-session`
**Source:** 2026-04-05-plugin-skills-agents-improvement, Session 3
**Evidence:** DEV-006 — verification grep `"initialization order"` returned 0 results because the implemented phrase was `"initialized in a later step"`. The concept was correctly incorporated; only the test anchor failed.
**Last reviewed:** 2026-04-06
**Application notes:**

---

### L-005: Plan-time validation depends on what's loaded, not what's written
**WHEN** an execution plan declares `cli` validation that depends on the runtime behavior of a plugin agent or skill that the same deliverable modifies — and the agent/skill is loaded from a plugin cache (not from the working tree) — **DO** either (a) declare validation `post-hoc` instead, (b) sequence a plugin reinstall step into the deliverable before the cli check runs, or (c) design the cli check so the proof-point is observable in the working tree (grep, file existence, content shape) rather than via a live agent invocation. Never trust that working-tree edits to a plugin's own agents are visible to in-session agent invocations without an explicit reinstall.
**Tags:** `#tests` `#technical` `#multi-feature`
**Source:** 2026-05-03-hardening-pass, DEV-002
**Evidence:** D2's cli validation (run `tests` reviewer against synthetic fixture; assert `dimension: "mock-placement"`) could not produce the canonical enum value because the reviewer agent loaded from `~/.claude/plugins/cache/.../agents/tests.md` (v3.0.0 frozen) rather than from the working-tree `plugins/strategic-implementation/agents/tests.md` (v3.1 with the new dimension). The rule fired correctly under the existing `honesty` label, proving prose-correctness, but the strict cli match was impossible without reinstall. Pre-acknowledged in plan as "plugin-cache drift risk" but the plan still declared `cli` validation rather than `post-hoc`.
**Last reviewed:** 2026-05-03
**Application notes:**
