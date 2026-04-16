---
name: executing-plans
description: Executes a single session plan from the strategic-implementation workflow. Marks session progress in the implementation guide, enforces TDD with atomic commits, logs deviations, updates the living document with meaningful deviations and downstream flags, and offers post-mortem on completion.
---

# Executing Plans

Executes one session from an approved session plan. Invoked automatically by `session-plan` (which passes all paths), or manually by the user.

**Announce at start:** "Starting execution of Session N: [session name]."

---

## Step 0 — Receive Context

**If invoked by session-plan:** receive as parameters:
- Session plan path (e.g., `docs/strategic-implementation/2026-04-02-auth-redesign/session-1-plan.md`)
- Implementation guide path (e.g., `docs/strategic-implementation/2026-04-02-auth-redesign/implementation-guide.md`)
- Feature folder path (e.g., `docs/strategic-implementation/2026-04-02-auth-redesign/`)
- Session number N

**If invoked standalone (user invokes directly):** ask:
1. "What is the path to the session plan file?"
2. "What is the path to the implementation guide?"

Derive feature folder path and session number N from the session plan path.

Load and read both files completely before proceeding. Initialize deviation counter at `DEV-001`.

**Branch check:** Run `git branch --show-current`. If the result is `main` or `master`, display the following warning and require explicit user confirmation before proceeding to Step 1:

> ⚠️ **Warning: you are on the `[branch name]` branch.** Executing a session plan directly on `main`/`master` is strongly discouraged. Please confirm you want to proceed on this branch, or switch to a feature branch first.

Wait for explicit user confirmation (e.g., "yes, proceed", "confirmed", or equivalent) before continuing. If the user does not confirm, stop here.

---

## Step 1 — Mark Session In-Progress

In the implementation guide, update Session N's Status field:
`**Status:** \`pending\`` → `**Status:** \`in-progress\``

Announce: "Implementation guide updated to `in-progress`."
_updated — docs/strategic-implementation/[path]/implementation-guide.md_

---

## Step 2 — Analyze Parallelism

Read the Steps list in the session plan. Group steps by `[parallel group: X]` annotation — all steps sharing the same letter run concurrently. Steps with no annotation are sequential.

Produce and announce an execution schedule before starting:
> "Execution schedule: Group A (steps 1, 2) → Step 3 → Group B (steps 4, 5) → Step 6."

---

## Step 3 — Execute Steps

For each unit in the execution schedule:

**Sequential step:** execute inline.

**Parallel group:** dispatch one subagent per step using the Agent tool. Each subagent receives the step description, file paths, and the TDD protocol below. Wait for all subagents to return before proceeding to the next unit. If any subagent returns failure: stop and surface the failure to the user — do not proceed to downstream sequential steps.

### Execution Failure Protocol (triggered on any step failure — classification below determines approach)

**Classify the failure first:**
- **Determinate** — root cause is directly visible (wrong import path, syntax error, missing env var): fix it. If the fix fails, treat as assumption-based and continue below.
- **Assumption-based** — cause must be inferred from behavior: state the assumption explicitly before attempting any fix.

**Attempt 1:**
1. State the assumption (assumption-based) or root cause (determinate) in one sentence before touching any code.
2. Implement the fix. Run tests.
3. **Success:** log a `blocker` or `retry` deviation, continue execution.
4. **Failure:** revert all changes from this attempt (`git revert` or manual rollback). Confirm the error/test state returns to baseline before proceeding.

**After Attempt 1 failure — re-examine assumptions:**
- List ALL assumptions that informed Attempt 1.
- Rate each: `high` / `medium` / `low` confidence.
- If no assumption is rated `medium` or `low`: **EXIT** (see Exit Report below).
- If one or more assumptions are `medium` or `low`: identify the single lowest-confidence assumption. Revise it. Determine if a distinct fix follows from this revision.

**Attempt 2 (only if a distinct fix is identified from revised assumptions):**
1. State the revised assumption explicitly.
2. Implement. Run tests.
3. **Success:** log deviation, continue.
4. **Failure:** revert all changes from this attempt. Confirm baseline restored. **EXIT.**

**Exit Report — format and surface to user:**
```
## Execution Blocked

**Step:** [step number and description]
**Error:** [exact error message or test output — no paraphrasing]

**Observations (confirmed facts):**
- [fact 1]
- [fact 2]

**Assumptions held:**
- [assumption] — confidence: high / medium / low
- ...

**Attempts made:**
1. [what was tried] → [outcome]
2. [what was tried] → [outcome] _(if applicable)_

**Most suspect assumption:** [single statement of the assumption most likely to be wrong]

**Blocked on:** [what human input, external access, or information is needed to proceed]

All changes from failed attempts have been reverted. Codebase is at baseline.
```

Do not mark the session complete. Do not proceed to Step 4. Await user direction.

### TDD Protocol (apply to every step, sequential or parallel)

**TDD ordering correction:** Before executing, check whether the plan places a test step after its paired implementation step — or defers a test step to a later parallel group. If so: reorder locally so the test precedes the implementation, treat both as sequential, and log an `ambiguity-decision` deviation. Do not execute implementation before test.

1. Write the failing test. Run it. Confirm it fails for the expected reason.
   - If the test passes before any implementation: stop and surface this to the user. Do not proceed.
2. Write the minimal implementation to make the test pass.
3. Run the full test suite (not just the new test). Confirm: new test passes AND no regressions.
   - If regressions: fix before committing.
4. Commit atomically — one commit per deliverable (not per step). If multiple steps together complete one deliverable, commit after the deliverable is complete.
   - Commit message format: `session-N step M: [what was done]`
   - Example: `session-1 step 3: add user auth middleware`

_Exception: steps involving infrastructure or configuration only (no testable behavior) may skip the test-first step. Describe why in the deviation log if skipped._

### Code Discipline (apply to every step, alongside TDD)

**Simplicity:** Write the minimum code that passes the test and satisfies the step. No abstractions for single-use code, no speculative features, no "flexibility" or "configurability" beyond what the step describes. If you wrote 200 lines and it could be 50, rewrite before committing.

**Surgical changes:** Touch only what the step requires. Do not "improve" adjacent code, comments, formatting, type hints, or docstrings. Do not refactor things that aren't broken. Every changed line should trace directly to the step's deliverable.

**Style matching:** Match the existing codebase's conventions — quote style, spacing, naming patterns, error handling idioms. Even if you'd do it differently, consistency with surrounding code takes priority.

**Clean only your mess:** Remove imports, variables, and functions that YOUR changes made unused. Do not remove pre-existing dead code or unused items — mention them in the deviation log if noticed, but leave them untouched.

### Deviation Detection

After each step, assess: did this step execute exactly as the plan described?

A deviation exists when any of these occurred:
- A **blocker** was hit (dependency missing, test fails unexpectedly, instruction impossible as written)
- A **retry** was needed (first attempt failed, approach changed)
- A **user correction** occurred mid-step
- A **reversal** — a step was undone
- An **ambiguity decision** — an unclear instruction required a judgment call

**If no deviation:** continue.

**If deviation:** log it immediately (see Deviation Log below), then assess:

> Is this a **meaningful deviation** — would a future session agent make wrong assumptions if they didn't know this? Test: "Does this change what was actually built relative to what the plan describes?"

- **Yes (meaningful):** update the implementation guide's `#### Meaningful Deviations` block for Session N immediately. Then run Step 3a.
- **No:** log only. Do not touch the implementation guide.

---

## Step 3a — Downstream Impact Assessment (run when a meaningful deviation is logged)

Read the implementation guide. For each session after Session N:
- Would this deviation cause a downstream session agent to make wrong assumptions?
- If yes: prepend `⚠️ REVISION NEEDED — [one sentence: what changed and why it matters for this session]` to that session's block.
- If no: leave unchanged.

Run inline. Surface flagged sessions to the user in the next user-facing message.

---

## Deviation Log Format

File: `<feature-folder-path>/session-N-log.md`
Create only when at least one deviation is logged. Do not create an empty file.
When the file is first created, announce: _saved to docs/strategic-implementation/[path]/session-N-log.md_

**File header:**
```markdown
# Session N Deviation Log
_Feature: [feature folder name]_
_Session: N — [session name]_
_Date: YYYY-MM-DD_
_Total deviations: [update this count when session completes]_

---
```

**Each entry:**
```markdown
## DEV-NNN
**Type:** `blocker` | `retry` | `user-correction` | `reversal` | `ambiguity-decision`
**Step:** [step number from session plan]
**What the plan said:** [verbatim or close paraphrase of the planned step]
**What actually happened:** [what was done instead, and why]
**Resolution:** [how it was resolved]
**Plan gap?** `yes` | `no` — [if yes: one sentence on what the plan failed to anticipate]
**Downstream impact?** `yes` | `no`
**Agent category:** [one of: future-proofing | security | data-model | api-contract | test-coverage | performance | dependency | frontend | scope | technical]
```

---

## Step 4 — End Checkpoint

After all steps complete, ask:

> "All steps executed. Is everything working as expected?"

**If yes:**
1. Update implementation guide Session N: `**Status:** \`in-progress\`` → `**Status:** \`complete\``
2. If a deviation log was created: finalize by updating `_Total deviations: N_` header line.
3. Announce: "Session N complete. Implementation guide updated."
   _updated — docs/strategic-implementation/[path]/implementation-guide.md_
4. Offer: "Would you like to run a post-mortem on this session? It reviews deviations and updates the project learning log. Say 'run post-mortem' or 'skip'."
   - **Run post-mortem:** announce "Invoking `strategic-implementation:post-mortem` to review session deviations." then invoke `strategic-implementation:post-mortem` with: feature folder path, session number N, session plan path, deviation log path (or `none` if no log exists), implementation guide path.
   - **Skip:** announce "Skipping post-mortem."
5. **All-sessions check:** Re-read the implementation guide. Count all sessions and their statuses.
   - If **all sessions are now marked `complete`:** announce "All sessions complete. Invoking `strategic-implementation:end-of-implementation` for end-to-end validation." then invoke `strategic-implementation:end-of-implementation`, passing: feature folder path, implementation guide path.
   - If **sessions remain pending or in-progress:** this skill ends here. The user will invoke `strategic-implementation:session-plan` for the next session.

**If no, or if the response is ambiguous** ("sort of", "mostly", "there's one small thing", or any answer that is not a clear yes):
Announce: "Invoking `strategic-implementation:bug-fix` to investigate and resolve the issue."
Invoke `strategic-implementation:bug-fix`, passing:
- Feature folder path
- Session number N
- Session plan path
- Implementation guide path
- Deviation log path (or `none` if no log exists)

The bug-fix skill owns the investigation and fix. It will return a summary of what was resolved. When it returns, re-ask: "Is everything working as expected now?"
- **Yes:** proceed to mark complete (steps 1–5 of the "If yes" path above, in order).
- **No or ambiguous:** re-invoke `strategic-implementation:bug-fix` with the same parameters. Repeat until the user confirms yes. Do not mark Session N complete until confirmed.

---

## Constraints

- Never start implementation on main/master branch without explicit user consent.
- Never skip a test step. If a deliverable has no described test in the session plan: stop and ask how to verify correctness before implementing.
- Never commit multiple deliverables in one commit.
- Never proceed past a failed parallel subagent — surface failures immediately.
- Stop and ask rather than guess on any ambiguous instruction.
