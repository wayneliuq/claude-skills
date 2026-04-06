# Session 3 Post-Mortem: Agent Scope Boundaries and Signal Trimming
_Feature: 2026-04-05-plugin-skills-agents-improvement_
_Date: 2026-04-06_
_Deviations reviewed: 6_

## Learning Application
No prior `project-learnings.md` — no existing learnings to apply.

## Approved Learning Updates

**L-001 (scope)** — New, from DEV-001 + DEV-002
WHEN a research finding recommends a check functionally equivalent to one the spec explicitly removed (even in different framing), DO reject the finding and cite the spec's removal decision.

**L-002 (security/scope)** — New, from DEV-003
WHEN a research finding recommends flagging the absence of a prerequisite activity (threat modeling, abuse-case analysis) that happens before plan creation, DO reject it from plan-level review agents.

**L-003 (scope)** — New, from DEV-005
WHEN specifying a line-count budget for agents using `## Step N` format with `---` separators, DO add ~18 lines per agent to the budget or use `### Task` format instead.

**L-004 (technical)** — New, from DEV-006
WHEN writing session plan verification greps for incorporated research findings where implementation wording hasn't been decided, DO use 2–3 semantic keywords rather than a specific phrase.

## Rejected Candidates
None.

## Cross-Session Patterns
Not applicable — fewer than 3 sessions logged.

## Implementation Guide Updates
Session 3 Meaningful Deviations block updated from "_None — session not yet executed_" to "_None_" (all 6 deviations had downstream impact: no).
