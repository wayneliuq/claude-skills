---
name: end-of-implementation
description: End-of-implementation validation skill. Triggered automatically when all sessions in the implementation guide are marked complete. Writes E2E tests for the full feature, verifies the existing test suite for regressions, and checks that modified files have not cross-contaminated dependents.
---

# End of Implementation

Triggered automatically by `executing-plans` when all sessions in the implementation guide are marked complete. Validates the full implementation end-to-end before the branch is finalized.

**Announce at start:** "Starting end-of-implementation validation for [feature folder name]."

---

## You Receive

**When invoked by executing-plans:**
- Feature folder path (e.g., `docs/strategic-implementation/2026-04-02-auth-redesign/`)
- Implementation guide path (e.g., `docs/strategic-implementation/2026-04-02-auth-redesign/implementation-guide.md`)

**When invoked manually:** ask the user for each of the above.

---

## Step 1 — Load Context

Read in full:
- Implementation guide (`implementation-guide.md`)
- All session plans in the feature folder (`session-*-plan.md`)
- All deviation logs in the feature folder (`session-*-log.md`)
- Spec (`spec.md`) if present

From these, extract:
- The complete list of features and behaviors delivered across all sessions (not session-by-session — the unified feature as a whole)
- The full set of files touched across all sessions (from session plan steps and deviation logs)

---

## Step 2 — Discover Modified Files

Determine the canonical set of files modified during this implementation using two sources cross-validated against each other:

**Source A — Implementation guide session steps:** For every session, extract every file path mentioned in steps and deliverables.

**Source B — Git history:** Run `git log --oneline --name-only` filtered to commits referencing the feature (match the feature folder name slug, `session-N`, or the feature branch name if on a branch). Collect the set of changed files.

Union both sets. Deduplicate. This is the **modified file set**.

Announce: "Modified file set: [count] files identified."

---

## Step 3 — Cross-Contamination Check

For each file in the modified file set, identify its **dependents** — files that import, require, call, or otherwise depend on it:

- Use `grep` / code search to find all import/require/use statements referencing each modified file.
- Build a dependent map: `modified file → [list of dependent files]`.

For each dependent file found:
1. Check whether the dependent is itself in the modified file set (expected — deliberate change).
2. If the dependent is **not** in the modified file set: flag it as a **potential cross-contamination candidate** — a file we did not intend to affect but which depends on something we changed.

For each cross-contamination candidate:
- Read the file.
- Determine whether the dependency interface (function signature, export shape, type contract) changed in a way that could break the dependent.
- If no breaking interface change: note "dependency stable — no action needed."
- If a breaking or uncertain interface change: flag as **contamination risk** with a one-sentence description of what changed and why the dependent may be affected.

---

## Step 4 — Run Existing Test Suite

Run the full existing test suite (use the test command from the session plan's Deliverables & Tests, or ask the user if not determinable).

Report results:
```
## Existing Test Suite
Command: [command run]
Result: [passed N / failed M / N total]
Failures: [list failing tests, or "none"]
```

If failures exist: check whether each failure is in a file from the modified file set or a cross-contamination candidate.
- **In modified set:** likely a regression introduced by this implementation.
- **In dependent/candidate:** likely a cross-contamination breakage.
- **Unrelated file:** flag as pre-existing (do not block on it, but surface it).

---

## Step 5 — Write E2E Tests

From the implementation guide and spec, identify the **complete user-facing or integration-level feature flows** — behaviors that span multiple components or sessions and cannot be verified by unit tests alone.

For each identified flow:
1. Write an E2E or integration test that exercises the flow end-to-end.
2. Run the test. Confirm it passes.
3. If it fails: classify as either a regression (the feature is broken) or a test authoring issue (the test itself is wrong). Fix test authoring issues immediately. Flag regressions.

E2E tests must:
- Exercise the full flow, not just one component in isolation.
- Cover the success path and at least one error/edge case per flow.
- Be placed in the appropriate test directory for this project (infer from existing test structure; ask if unclear).

Announce: "E2E tests written: [count] flows covered."

---

## Step 6 — Surface Issues to User

Collect all issues found across Steps 3–5:

```
## End-of-Implementation Validation Report
_Feature: [feature folder name]_
_Date: YYYY-MM-DD_

### Modified Files
[count] files changed across [N] sessions. (list if ≤ 10; summarize by directory if more)

### Cross-Contamination Check
- [file]: [status — stable / contamination risk: reason]
- ...
(or "No contamination risks found.")

### Existing Test Suite
[passed / failed summary]
Failures:
- [test name]: [classification — regression / cross-contamination / pre-existing]

### E2E Tests
[count] flows written and passing.
Failures:
- [flow name]: [regression description]
```

**If no issues:** announce "Validation complete — no issues found. Invoking `superpowers:finishing-a-development-branch` to finalize the branch." then invoke `superpowers:finishing-a-development-branch`.

**If issues exist:**

Present the report to the user and ask:

> "Validation found [N] issue(s) above. Would you like me to investigate and fix them now? I'll invoke `strategic-implementation:bug-fix` for each. Reply `fix`, `fix [specific issue]`, or `skip` to finalize the branch without fixing."

- **`fix` or `fix [issue]`:** announce "Invoking `strategic-implementation:bug-fix` to address the issue." then invoke `strategic-implementation:bug-fix`, passing: feature folder path, implementation guide path, a description of the specific issue. When bug-fix returns, re-run the affected test(s) to confirm resolution. Re-present the updated report. Repeat until no issues remain or the user skips.
- **`skip`:** announce "Skipping remaining issues. Invoking `superpowers:finishing-a-development-branch` to finalize the branch." then invoke `superpowers:finishing-a-development-branch`.

---

## Constraints

- Do not mark the implementation complete until Step 6 is resolved.
- Do not write E2E tests that duplicate existing unit tests — focus on cross-session and cross-component flows.
- If the project has no existing test suite: note this in the report and skip Step 4. Do not fail.
- If a modified file has no dependents: note "no dependents found" and move on. Do not treat the absence of dependents as an error.
- Pre-existing test failures (in files unrelated to this implementation) are reported but do not block finalization — surface them and let the user decide.
