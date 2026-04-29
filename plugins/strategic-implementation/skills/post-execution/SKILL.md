---
name: post-execution
description: Consolidated post-execution skill replacing v1's bug-fix + post-mortem + end-of-implementation. Three modes — regression-check (auto after all deliverables complete), triage (PM-reported behavioral issue), learnings-synthesis (validation-log accumulation).
---

# post-execution

One skill, three modes. Selected by the caller based on context.

You receive:
- `mode`: `regression-check` | `triage` | `learnings-synthesis`
- Feature folder path
- For `triage`: the PM's issue report
- For `learnings-synthesis`: (no extra input — reads validation-log)

---

## Mode: regression-check

Triggered automatically by `executing-plans` when the final deliverable is marked complete.

### Steps

1. **Discover modified file set.** Union of:
   - Files listed across all deliverables in `execution-plan.md`
   - Files touched in git history since the feature branch diverged (`git diff --name-only <base>..HEAD`)
2. **Cross-contamination check.** For each modified file, grep the rest of the repo for imports/references. For each dependent, decide: is its behavior potentially affected? Flag dependents whose tests should be rerun.
3. **Run the existing test suite.** Use the project's test command (detect from `package.json` / `pyproject.toml` / `Makefile`). Record failures. A test that was passing before this feature and fails now is a regression.
4. **Author acceptance tests for feature flows.** For every acceptance criterion in the brief that was not validated via TDD during execution, author an E2E or integration test now. Run it.
5. **Goal-backward claim verification.** Build the suspect-set: deliverables whose `Validation` is `post-hoc` OR which carry a `FLAG (mocked-seam)` entry in `validation-log.md`. Take the first **3 matches**. If none, skip this step.

   For each matched deliverable, read its expected outcome from `execution-plan.md` (not from any commit message, summary, or validation-log narrative). For each named artifact (function / route / consumer / config key / file path), run a single grep and record yes/no — does it exist in the codebase as the plan claims? Use the acceptance test authored in Step 4 (if any) as one of the yes/no signals.

   Append findings to the report under `## Goal-backward verification` as one block per deliverable: `D<n>: <artifact> — yes|no`. Any `no` → status BLOCK.

6. **Write** `<feature-folder>/post-execution-report.md`:

```markdown
# Post-execution report
_Date: <date> · Feature: <slug>_

## Modified files
<bulleted, with "touched by deliverable D<n>" annotations>

## Cross-contamination
<dependents examined; regressions flagged>

## Test suite run
- Command: <...>
- Result: <n passed, m failed>
- Regressions: <list or "none">

## Acceptance tests authored
<list — which criteria, which test files>

## Goal-backward verification
<one block per matched deliverable, or "skipped — no post-hoc or mocked-seam matches">

## Status
<PASS / FLAG / BLOCK — BLOCK if regressions unresolved or any goal-backward `no`>
```

7. If any regression is unresolved or any goal-backward verification returns `no`: surface to PM. Otherwise announce completion.

---

## Mode: triage

Triggered when PM reports a behavioral issue after execution completed (bug, unexpected behavior, missing edge case).

### Steps

1. Read the PM's report. Identify: what surface, what the expected behavior was, what was observed.
2. Reproduce. Use the validation method from the relevant deliverable (preview, cli, etc.) to confirm.
3. **TDD the fix.** Write an acceptance test that captures the bug (fails currently). Then write the minimum code to make it pass.
4. Run the full test suite to confirm no new regressions.
5. Append to `<feature-folder>/validation-log.md`:

```markdown
## Triage · <date>
**Reported:** <PM's words>
**Repro:** <how reproduced>
**Root cause:** <one sentence>
**Fix:** <one sentence + files touched>
**Test added:** <path>
**Status:** resolved | deferred | escalated
```

6. Report back to PM.

---

## Mode: learnings-synthesis

Triggered when `validation-log.md` accumulates ≥2 meaningful deviations (judgment call — a typo fix does not count; a non-obvious gotcha does).

### Steps

1. Read `<feature-folder>/validation-log.md`.
2. For each deviation, ask: **what general rule, applied in future features, would have prevented this?** If the rule is feature-specific, skip. If the rule is broadly applicable, draft a learning.
3. Each draft learning has:
   - **ID:** next `L-NNN`
   - **Title:** short imperative
   - **WHEN:** trigger condition in plan / code
   - **DO:** guidance
   - **Tags:** `#<agent>` tags, plus `#single-feature` or `#multi-feature`
4. Surface drafts to the PM. For each: accept, revise, or reject.
5. Append accepted learnings to `docs/strategic-implementation/project-learnings.md`. Deduplicate against existing entries — if a similar learning exists, merge rather than duplicate.
6. Report: "N learnings added, M merged, K rejected."

---

## Cross-mode rules

- Never rewrite history. Fixes land as new commits.
- Never modify the brief. The brief is a frozen approval artifact. If a fix proves the brief was wrong, note it in the report but do not rewrite the brief.
- Validation log is append-only.
