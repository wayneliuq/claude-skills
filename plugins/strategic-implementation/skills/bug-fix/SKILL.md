---
name: bug-fix
description: Investigates and fixes behavioral discrepancies reported after session execution. Gathers reproducible details, triages reports into tickets, checks for shared root causes, fixes with TDD, and logs each resolution as a session deviation.
---

# Bug Fix

Investigates and resolves behavioral issues reported after a session's steps have completed — cases where execution appeared to succeed but the result doesn't behave as expected.

**Announce at start:** "Starting bug-fix investigation for Session N."

---

## Step 0 — Receive Context

**If invoked by executing-plans:** receive as parameters:
- Feature folder path
- Session number N
- Session plan path
- Implementation guide path
- Deviation log path (or `none` if no log exists)

**If invoked standalone:** ask:
1. "What is the feature folder path?"
2. "What session number are you fixing?"
3. "What is the session plan path?"
4. "What is the implementation guide path?"
5. "Does a deviation log exist? If so, what is its path?"

Load the session plan, implementation guide, and any existing deviation log before proceeding.

**Determine the starting deviation counter:** if a deviation log exists, read it and find the highest `DEV-NNN` number present. The next deviation ID is `DEV-(NNN+1)`. If no log exists, start at `DEV-001`.

---

## Step 1 — Intake Gate

Ask the user to describe what isn't working. For **each reported issue**, require all four of these before proceeding:

1. **Steps to reproduce** — exact sequence of actions to trigger the problem
2. **Expected behavior** — what should happen
3. **Actual behavior** — what happens instead (include exact error messages, stack traces, or screenshots if applicable)
4. **Affected area** — which feature, screen, or API endpoint; which session step is most likely responsible

If any of the four is missing for any report: ask specifically for the missing item. Do not infer or assume. Do not proceed to Step 2 until all reports are complete.

> "I need the following before I can investigate: [list missing items]. Please provide these so I can reproduce the issue exactly."

Once intake is complete, read back a concise summary of each report and confirm with the user before proceeding.

---

## Step 2 — Triage

List all confirmed reports as candidate issues:

```
Issue 1: [one-line description]
Issue 2: [one-line description]
...
```

**Correlation check — investigate before assigning separate fixes:**
- Read the relevant source files and session plan steps for each issue.
- Ask: could two or more issues share a single root cause?
  - **Yes (likely shared root cause):** group them. Label as `Issue 1+2: [shared root cause hypothesis]`. A single fix resolves the group.
  - **No (independent):** treat each separately.

Announce the triage result:
> "Triage complete. [N issues → M tickets]. Ticket 1: [description]. Ticket 2: ..."

Prioritize tickets by severity: issues that block core functionality first, cosmetic or edge-case issues last.

---

## Step 3 — Fix Per Ticket

For each ticket, in priority order:

### 3a — Reproduce Before Fixing

Using the reproduction steps from intake: confirm you can reproduce the issue in the code without any changes. If you cannot reproduce it:
- State what you observed.
- Ask the user: "I cannot reproduce this with the provided steps. Can you clarify [specific gap]?"
- Do not attempt a fix for an issue you cannot reproduce.

### 3b — Write a Failing Test

Write a test that captures the bug — it must fail in the current state and pass once the bug is fixed.

- If a suitable test already exists and is passing: stop. Surface this to the user. The issue may be environmental or require manual verification. Do not fabricate a fix.
- If the bug is in infrastructure or configuration with no testable behavior: describe why in the deviation log entry, and skip to 3c.

### 3c — Fix

Implement the minimal change that resolves the ticket. Do not refactor surrounding code or address issues outside the ticket scope.

Run the full test suite. Confirm: new test passes AND no regressions.
- If regressions: fix before committing.

### 3d — Commit

Commit atomically per ticket:

```
bug-fix session-N: [what was wrong and what fixed it]
```

Example: `bug-fix session-2: auth token not invalidated on logout — missing cache clear`

### 3e — Log as Deviation

Append to the session deviation log (`session-N-log.md`). Create the file if it doesn't exist (use the deviation log format from `executing-plans`).

```markdown
## DEV-NNN
**Type:** `retry` | `user-correction` | `blocker` | `reversal`
  — use `user-correction` if the bug reflects a misunderstood requirement or spec gap
  — use `blocker` if the behavior was completely broken (not a partial or edge-case failure)
  — use `reversal` if any code was reverted as part of the fix
  — use `retry` for all other implementation misses
**Ticket:** [ticket number from triage — e.g., Ticket 1; or "ungrouped" if only one report]
**Reports resolved:** [which user reports from Step 1 intake this ticket addresses — e.g., "Issue 1, Issue 2"]
**Step:** [step number from session plan most responsible for this bug]
**What the plan said:** [what the plan described this step would produce]
**User reported:** [verbatim or close paraphrase of the user's description — their words, their experience]
**Observed during reproduction:** [what the agent confirmed when reproducing the issue — technical facts only, no interpretation]
**Root cause:** [why the bug existed — one or two sentences on the underlying cause, not just what was changed]
**Resolution:** [what code changed and how it fixes the root cause]
**Reproduction steps:** [the exact steps used to reproduce — copied from intake]
**Plan gap?** `yes` | `no` — [if yes: what the plan failed to specify or anticipate]
**Downstream impact?** `yes` | `no`
**Agent category:** [future-proofing | security | data-model | api-contract | test-coverage | performance | dependency | frontend | scope | technical]
```

If the session log already exists, append. If not, create it with the standard header from `executing-plans`.
_saved to docs/strategic-implementation/[path]/session-N-log.md_

---

## Step 4 — Downstream Impact Check

After all tickets are resolved: read the implementation guide (path received in Step 0). For each deviation logged in this session, assess:
- Would a future session agent make wrong assumptions based on this bug and its fix?
- If yes: prepend `⚠️ REVISION NEEDED — [one sentence: what changed and why it matters]` to that session's block in the implementation guide.
- If no: leave unchanged.

Surface any flagged downstream sessions to the user.

---

## Step 5 — Close

Confirm each original report from Step 1 is addressed. Present a close summary:

```
Bug-fix complete. Session N.

Tickets resolved: [N]
  ✓ Ticket 1: [description] → [fix summary]
  ✓ Ticket 2: [description] → [fix summary]

Deviations logged: DEV-NNN through DEV-MMM
Downstream flags: [none | sessions X, Y flagged for revision]
```

Return control to the user. If this skill was invoked from `executing-plans`, inform the user:
> "All reported issues are resolved. Please confirm everything is working as expected so the session can be marked complete."

---

## Constraints

- Never attempt a fix for an issue you cannot reproduce. Ask for clarification instead.
- Never fix more than the ticket scope — no opportunistic refactors.
- Never skip the failing test step without documenting why in the deviation log.
- Never commit multiple tickets in one commit.
- Do not mark any ticket resolved without a passing test (or documented exception).
- Do not call back into `executing-plans` — return control to the user directly.
