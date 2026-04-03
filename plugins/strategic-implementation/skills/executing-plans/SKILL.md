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

---

## Step 1 — Mark Session In-Progress

In the implementation guide, update Session N's Status field:
`**Status:** \`pending\`` → `**Status:** \`in-progress\``

Announce: "Implementation guide updated to `in-progress`."

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

### TDD Protocol (apply to every step, sequential or parallel)

1. Write the failing test. Run it. Confirm it fails for the expected reason.
   - If the test passes before any implementation: stop and surface this to the user. Do not proceed.
2. Write the minimal implementation to make the test pass.
3. Run the full test suite (not just the new test). Confirm: new test passes AND no regressions.
   - If regressions: fix before committing.
4. Commit atomically — one commit per deliverable (not per step). If multiple steps together complete one deliverable, commit after the deliverable is complete.
   - Commit message format: `session-N step M: [what was done]`
   - Example: `session-1 step 3: add user auth middleware`

_Exception: steps involving infrastructure or configuration only (no testable behavior) may skip the test-first step. Describe why in the deviation log if skipped._

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
**Agent category:** [one of: architecture | security | data-model | api-contract | test-coverage | performance | dependency | frontend | scope | technical]
```

---

## Step 4 — End Checkpoint

After all steps complete, ask:

> "All steps executed. Is everything working as expected?"

**If yes:**
1. Update implementation guide Session N: `**Status:** \`in-progress\`` → `**Status:** \`complete\``
2. If a deviation log was created: finalize by updating `_Total deviations: N_` header line.
3. Announce: "Session N complete. Implementation guide updated."
4. Offer: "Would you like to run a post-mortem on this session? It reviews deviations and updates the project learning log. Say 'run post-mortem' or 'skip'."
   - **Run post-mortem:** invoke `strategic-implementation:post-mortem` with: feature folder path, session number N, session plan path, deviation log path (or `none` if no log exists), implementation guide path.
   - **Skip:** announce "Skipping post-mortem." Then invoke `superpowers:finishing-a-development-branch`.

**If no:**
Ask: "What isn't working? I'll resume from the failing step."
Resume execution. Log a new deviation entry for the failure. Do not mark complete until the user confirms.

---

## Constraints

- Never start implementation on main/master branch without explicit user consent.
- Never skip a test step. If a deliverable has no described test in the session plan: stop and ask how to verify correctness before implementing.
- Never commit multiple deliverables in one commit.
- Never proceed past a failed parallel subagent — surface failures immediately.
- Stop and ask rather than guess on any ambiguous instruction.
