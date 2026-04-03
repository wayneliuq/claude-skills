# Plan-Execution, Post-Mortem, and Learning System — Implementation Plan

> **Destination:** Once the feature folder exists, copy this plan to
> `docs/strategic-implementation/2026-04-02-plan-execution-postmortem/implementation-guide.md`

**Goal:** Replace the copied executing-plans skill with a first-class version, add a post-mortem learning system, make all artifacts file-persistent in a canonical folder structure, and wire project learnings into every agent review.

**Architecture:** All strategic-implementation artifacts land under `docs/strategic-implementation/<feature>/`. An executing-plans skill replaces the generic copy, enforces TDD and atomic commits, logs deviations, and keeps the implementation guide current. A post-mortem skill converts deviation logs into structured learnings in `project-learnings.md`. All 11 review agents receive filtered learnings before producing output.

**Tech Stack:** Markdown skill files only. No code. Verification is manual review of skill logic and internal consistency.

---

## File Map

### New Files
| Path | Task |
|------|------|
| `plugins/strategic-implementation/skills/executing-plans/SKILL.md` | Task 6 |
| `plugins/strategic-implementation/skills/post-mortem/SKILL.md` | Task 7 |

### Modified Files
| Path | Task |
|------|------|
| `plugins/strategic-implementation/skills/implementation-guide/SKILL.md` | Task 1 |
| `plugins/strategic-implementation/skills/implementation-drafter/SKILL.md` | Task 2 |
| `plugins/strategic-implementation/skills/implementation-reviser/SKILL.md` | Task 3 |
| `plugins/strategic-implementation/skills/sessionize/SKILL.md` | Task 4 |
| `plugins/strategic-implementation/skills/session-plan/SKILL.md` | Task 5 |
| `plugins/strategic-implementation/skills/strategic-implementation/SKILL.md` | Task 8 |
| `plugins/strategic-implementation/agents/10k-foot.md` | Task 9 |
| `plugins/strategic-implementation/agents/technical-expert.md` | Task 9 |
| `plugins/strategic-implementation/agents/scope-limiter.md` | Task 9 |
| `plugins/strategic-implementation/agents/future-proofing.md` | Task 9 |
| `plugins/strategic-implementation/agents/security.md` | Task 9 |
| `plugins/strategic-implementation/agents/data-model.md` | Task 9 |
| `plugins/strategic-implementation/agents/api-contract.md` | Task 9 |
| `plugins/strategic-implementation/agents/test-coverage.md` | Task 9 |
| `plugins/strategic-implementation/agents/performance.md` | Task 9 |
| `plugins/strategic-implementation/agents/dependency.md` | Task 9 |
| `plugins/strategic-implementation/agents/frontend-engineer.md` | Task 9 |

### Unchanged (with one annotation)
| Path | Reason |
|------|--------|
| `_copied-skills/executing-plans.md` | Superseded — add deprecation header, keep as archived reference (see Task 6 Step 2) |
| `_copied-skills/writing-plans.md` | Fast-path uses superpowers:writing-plans; path override via instruction |
| `_copied-skills/plan-document-reviewer-prompt.md` | No changes needed |
| `skills/clarify/SKILL.md` | No changes needed |
| `skills/architecture-review/SKILL.md` | No changes needed |
| `skills/ux-pmf-review/SKILL.md` | No changes needed |

---

## Execution Order

```
Task 1 (implementation-guide template) → Tasks 2, 6 depend on it
Task 2 (implementation-drafter: save spec) → Task 4 depends on it (feature folder path)
Task 3 (implementation-reviser: save revised spec) → independent, do after Task 2
Task 4 (sessionize: save guide + inject learnings) → Task 5 depends on it
Task 5 (session-plan: save plan + inject learnings + parallelism + REVISION check) → Task 6 depends on it
Task 6 (executing-plans: new skill) → Task 7 depends on it
Task 7 (post-mortem: new skill) → independent after Task 6
Task 8 (strategic-implementation orchestrator: path passing) → after all above
Task 9 (all 11 agents: learning injection) → independent, do last
```

**Recommended order:** 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9

---

## Tasks

---

### Task 1 — Update `implementation-guide/SKILL.md`: living document template

**File:** `plugins/strategic-implementation/skills/implementation-guide/SKILL.md`

- [ ] **Step 1: Update the session block in the Template section**

  Replace the session block from `### Session N: [Name]` through `**Hard decisions applied:**` with the following:

  ```markdown
  ### Session N: [Name]
  **Status:** `pending`
  **Goal:** [one sentence — what is achieved by the end of this session]

  **Deliverables & Tests:**
  - [ ] Deliverable: [what is produced]
    Test: [how it is verified — specific enough to run or observe]

  **Files affected:** [specific file paths to be created or modified]
  **Docs to update:** [docs that must be updated after this session, or "none"]
  **Estimated size:** S (<200 LOC) | M (200–500) | L (500–1000)
  **Hard decisions applied:** [any [HARD DECISION] items this session implements, or "none"]

  #### Meaningful Deviations
  _None — session not yet executed_
  ```

  Valid Status values: `` `pending` `` | `` `in-progress` `` | `` `complete` ``

- [ ] **Step 2: Add Authoring Rule 10 — REVISION NEEDED flag**

  Append after rule 9 in the Authoring Rules section:

  ```
  10. **`⚠️ REVISION NEEDED` flag.** When executing-plans determines that a meaningful deviation from a prior session affects a downstream session, it prepends the following to that session's header block (before `**Status:**`):

      > `⚠️ REVISION NEEDED — [reason: what changed and why it matters for this session]`

      Session-plan checks for this flag in Step 1. The flag is removed manually by the user (or by session-plan with user confirmation) once the session block is updated to reflect the corrected assumptions.
  ```

- [ ] **Step 3: Add Authoring Rule 11 — Meaningful Deviations**

  Append after rule 10:

  ```
  11. **Meaningful Deviations field.** Populated by `executing-plans` after session execution if any meaningful deviations occurred. A meaningful deviation is a change that altered what was actually built such that a future session agent might make wrong assumptions. Test: "Would a future session agent be wrong if it didn't know this?" If no meaningful deviations occurred, the field reads `_None — session executed cleanly_`. Never pre-populate before execution.
  ```

- [ ] **Step 4: Add quality check item**

  Add to the Quality Checks list:
  ```
  - [ ] Every session block has a **Status** field set to `pending`
  ```

- [ ] **Step 5: Commit**

  ```bash
  git add plugins/strategic-implementation/skills/implementation-guide/SKILL.md
  git commit -m "feat(implementation-guide): add Status, Meaningful Deviations, REVISION NEEDED to session template"
  ```

- [ ] **Verify:** Status field present in template; Meaningful Deviations block present; rules 10 and 11 present; quality check updated.

---

### Task 2 — Update `implementation-drafter/SKILL.md`: save spec and create feature folder

**File:** `plugins/strategic-implementation/skills/implementation-drafter/SKILL.md`

- [ ] **Step 1: Add Step 4 — Save Artifact**

  Insert after the closing ` ``` ` of the "Document Format" template section, before the "Drafting Standards" section:

  ```markdown
  ## Step 4 — Save Artifact

  After completing the draft (before presenting to the user):

  1. **Derive the feature folder name.**
     - Take the spec title from `# Implementation Spec: [Feature / Change Name]`
     - Convert the feature name to kebab-case: lowercase, spaces and special characters → hyphens
     - Prefix with today's date: `YYYY-MM-DD`
     - Example: `# Implementation Spec: Auth Redesign` → `2026-04-02-auth-redesign`

  2. **Create the feature folder and save the spec.**
     - Folder: `docs/strategic-implementation/YYYY-MM-DD-<feature-name>/`
     - File: `docs/strategic-implementation/YYYY-MM-DD-<feature-name>/spec.md`
     - Create the folder if it does not exist.

  3. **Add a saved-path line** after presenting the spec:
     > _Spec saved to `docs/strategic-implementation/YYYY-MM-DD-<feature-name>/spec.md`_

  4. **Pass the feature folder path to the orchestrator.**
     The path `docs/strategic-implementation/YYYY-MM-DD-<feature-name>/` is canonical for this feature. Store it and pass it to all downstream skills. Do not re-derive from the title later — the path established here is authoritative.
  ```

- [ ] **Step 2: Commit**

  ```bash
  git add plugins/strategic-implementation/skills/implementation-drafter/SKILL.md
  git commit -m "feat(implementation-drafter): save spec.md to feature folder on draft"
  ```

- [ ] **Verify:** Step 4 present between Document Format and Drafting Standards; kebab-case derivation logic described; folder path format is `docs/strategic-implementation/YYYY-MM-DD-<feature-name>/`; step says to pass path to orchestrator.

---

### Task 3 — Update `implementation-reviser/SKILL.md`: save revised spec

**File:** `plugins/strategic-implementation/skills/implementation-reviser/SKILL.md`

- [ ] **Step 1: Update "You receive" section**

  The current "You receive" list includes: current spec document, user feedback, architecture doc location, UX/PMF doc location. Add:

  ```
  - Spec file path (e.g., `docs/strategic-implementation/2026-04-02-auth-redesign/spec.md`) — passed by the orchestrator; this is where the revised spec is saved after each round
  ```

- [ ] **Step 2: Add save step to Step 12 — Present**

  At the end of Step 12 (after "Clear the feedback slots"), add:

  ```
  **Save the revised spec.** Overwrite the spec file at the path received from the orchestrator with the full revised document. Confirm: `_Spec updated at <spec-file-path>_`.
  ```

- [ ] **Step 3: Commit**

  ```bash
  git add plugins/strategic-implementation/skills/implementation-reviser/SKILL.md
  git commit -m "feat(implementation-reviser): save revised spec back to spec.md after each revision round"
  ```

- [ ] **Verify:** Spec file path present in "You receive"; Step 12 includes save step; save overwrites the existing file (not a new file).

---

### Task 4 — Update `sessionize/SKILL.md`: accept feature folder path, save guide, inject multi-session learnings

**File:** `plugins/strategic-implementation/skills/sessionize/SKILL.md`

- [ ] **Step 1: Update "You receive" section**

  After "the finalized specification document", add:
  ```
  - The feature folder path (e.g., `docs/strategic-implementation/2026-04-02-auth-redesign/`) — passed by the orchestrator, established by implementation-drafter
  ```

- [ ] **Step 2: Add Step 2a — Load Project Learnings**

  Insert after Step 2 (Collect Document References), before Step 3 (Draft Sessions):

  ```markdown
  ## Step 2a — Load Project Learnings

  1. Check if `docs/strategic-implementation/project-learnings.md` exists. If not: skip this step entirely.
  2. Read the file. For each agent in the panel (Step 5), identify:
     - The agent's category tag (see agent files — each lists its category)
     - Filter learnings to those tagged with that agent's category AND tagged `#multi-session`
       (sessionize context applies multi-session learnings only — single-session learnings are not yet proven broadly)
  3. If filtered learnings exist for an agent, prepare a "Project Learnings" block to inject into that agent's prompt in Step 5:

  ```
  ## Project Learnings (apply per your "Processing Project Learnings" section)
  Context: implementation guide review — apply #multi-session learnings only.

  [paste each applicable L-NNN entry in full]
  ```

  Store these blocks; inject them in Step 5 when launching agents.
  ```

- [ ] **Step 3: Update Step 7 (Present for Approval) — add save step**

  Add at the end of Step 7, after the "Do not automatically proceed" line:

  ```markdown
  **Save the implementation guide.** Once the user approves:
  - Save to `<feature-folder-path>/implementation-guide.md`
  - Confirm: _Implementation guide saved to `<feature-folder-path>/implementation-guide.md`_
  - Pass this path (and the feature folder path) to the orchestrator for forwarding to session-plan.
  ```

- [ ] **Step 4: Update Step 5 agent launch instructions** — add "inject Project Learnings block if prepared in Step 2a" after the agent list. Specifically, add this line after "Wait for all agents to return":

  ```
  Pass each agent's prepared "Project Learnings" block (from Step 2a) as additional context in its prompt, if one was prepared. Agents with no applicable learnings receive no block.
  ```

- [ ] **Step 5: Commit**

  ```bash
  git add plugins/strategic-implementation/skills/sessionize/SKILL.md
  git commit -m "feat(sessionize): save implementation-guide.md, accept feature folder path, inject multi-session learnings"
  ```

- [ ] **Verify:** "You receive" includes feature folder path; Step 2a present with `#multi-session` filter; Step 5 notes injecting learning blocks; Step 7 includes save logic with path confirmation.

---

### Task 5 — Update `session-plan/SKILL.md`: REVISION check, parallelism, save plan, inject learnings, update auto-invoke

**File:** `plugins/strategic-implementation/skills/session-plan/SKILL.md`

- [ ] **Step 1: Update "You receive" section**

  After existing inputs, add:
  ```
  - Implementation guide path (e.g., `docs/strategic-implementation/2026-04-02-auth-redesign/implementation-guide.md`)
  - Feature folder path (e.g., `docs/strategic-implementation/2026-04-02-auth-redesign/`)
  ```

- [ ] **Step 2: Add REVISION NEEDED check to Step 1**

  After the existing "Verify pre-conditions" block in Step 1, add:

  ```markdown
  **REVISION NEEDED check:**
  Read the target session block in the implementation guide. If the session's header contains `⚠️ REVISION NEEDED — [reason]`, surface it to the user immediately:

  > "Session N is flagged: ⚠️ REVISION NEEDED — [reason]. A prior session's deviation may affect this session. Do you want to: (a) update the implementation guide to address this first, or (b) proceed acknowledging this flag?"

  Wait for the user's response before building the plan. Do not proceed automatically.
  ```

- [ ] **Step 3: Add Authoring Rule 7 — parallelism annotations — to Step 2**

  Add after existing rule 6 (`≤ ~1000 LOC`):

  ```
  7. **Annotate parallel steps.** Identify steps that can run concurrently: no overlapping file writes, and no output-to-input dependency between them. Annotate eligible steps with `[parallel group: X]` (X = a letter: A, B, C...). Steps sharing the same letter run concurrently. Sequential steps need no annotation.
  ```

  Also update the Steps template to show the syntax:

  ```markdown
  ### Steps
  1. [Step that can run concurrently with step 2] [parallel group: A]
     - Files: [exact file paths]
     - What: [specific enough to execute without guessing]
  2. [Another step with no dependency on step 1] [parallel group: A]
     - Files: ...
     - What: ...
  3. [Step that must follow steps 1 and 2] _(sequential)_
     - Files: ...
     - What: ...
  ```

- [ ] **Step 4: Add Step 2a — Load Project Learnings**

  Insert after Step 2 (Build the Session Plan), before Step 3 (Run Agent Panel):

  ```markdown
  ## Step 2a — Load Project Learnings

  1. Check if `docs/strategic-implementation/project-learnings.md` exists. If not: skip this step.
  2. Read the file. For each agent in the panel (Step 3), filter learnings by:
     - Agent's category tag AND
     - Tagged `#single-session` OR `#multi-session` (session-plan context applies both)
  3. Prepare a "Project Learnings" block for each agent that has applicable learnings:

  ```
  ## Project Learnings (apply per your "Processing Project Learnings" section)
  Context: session plan review — apply both #single-session and #multi-session learnings.

  [paste each applicable L-NNN entry in full]
  ```

  Inject these blocks into agent prompts in Step 3.
  ```

- [ ] **Step 5: Update Step 3 (Run Agent Panel)** — add injection note after the agent list:

  ```
  Pass each agent's prepared "Project Learnings" block (from Step 2a) as additional context in its prompt, if one was prepared.
  ```

- [ ] **Step 6: Add Step 5a — Save Session Plan**

  Insert between Step 5 (Present for Approval) and the auto-invoke block:

  ```markdown
  ## Step 5a — Save Session Plan

  Once the user approves:

  1. Save to `<feature-folder-path>/session-N-plan.md`
     Example: `docs/strategic-implementation/2026-04-02-auth-redesign/session-1-plan.md`
  2. Confirm: _Session N plan saved to `<feature-folder-path>/session-N-plan.md`_
  3. When invoking `strategic-implementation:executing-plans`, pass:
     - Session plan path: `<feature-folder-path>/session-N-plan.md`
     - Implementation guide path: `<feature-folder-path>/implementation-guide.md`
     - Feature folder path: `<feature-folder-path>/`
     - Session number: N
  ```

- [ ] **Step 7: Update auto-invoke reference**

  Change: `Automatically invoke superpowers:executing-plans. No manual step needed.`
  To: `Automatically invoke strategic-implementation:executing-plans, passing the paths from Step 5a. No manual step needed.`

- [ ] **Step 8: Commit**

  ```bash
  git add plugins/strategic-implementation/skills/session-plan/SKILL.md
  git commit -m "feat(session-plan): REVISION check, parallelism annotations, save plan, learning injection, update executing-plans invoke"
  ```

- [ ] **Verify:** "You receive" includes both paths; REVISION check in Step 1; rule 7 in Step 2; Steps template shows `[parallel group: X]`; Step 2a present with both-tags filter; Step 5a present; auto-invoke says `strategic-implementation:executing-plans`.

---

### Task 6 — Create `executing-plans/SKILL.md`: new first-class execution skill

**File:** `plugins/strategic-implementation/skills/executing-plans/SKILL.md` _(new)_

- [ ] **Step 1: Write the complete skill file**

  Full structure:

  ```markdown
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

  Run inline. Do not surface to the user unless flagging sessions (flagging is surfaced automatically by mentioning it in the next user-facing message).

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
  ```

- [ ] **Step 2: Add deprecation header to `_copied-skills/executing-plans.md`**

  Prepend to the top of `_copied-skills/executing-plans.md` (before the existing `<!--` comment):

  ```
  <!-- ⚠️ DEPRECATED — superseded by strategic-implementation:executing-plans
       (plugins/strategic-implementation/skills/executing-plans/SKILL.md)
       Kept for reference only. Do not invoke. -->
  ```

- [ ] **Step 3: Commit**

  ```bash
  git add plugins/strategic-implementation/skills/executing-plans/SKILL.md
  git add plugins/strategic-implementation/_copied-skills/executing-plans.md
  git commit -m "feat(executing-plans): new first-class execution skill; deprecate copied version"
  ```

- [ ] **Verify:** Step 0 handles both invocation paths; Step 1 marks in-progress; Step 2 announces execution schedule; TDD protocol lists all 4 sub-steps; deviation detection lists all 5 types; Step 3a downstream impact check present; deviation log format includes all 7 fields including `agent-category`; Step 4 offers post-mortem and invokes `strategic-implementation:` (not `superpowers:`).

---

### Task 7 — Create `post-mortem/SKILL.md`: new post-mortem skill

**File:** `plugins/strategic-implementation/skills/post-mortem/SKILL.md` _(new)_

- [ ] **Step 1: Write the complete skill file**

  Full structure:

  ```markdown
  ---
  name: post-mortem
  description: Reviews deviation logs from a completed session, synthesizes learnings, updates project-learnings.md, and writes a session post-mortem artifact. Triggered by executing-plans or manually by the user.
  ---

  # Post-Mortem

  Reviews the deviation log for a completed session, cross-references existing learnings, synthesizes new or expanded learning candidates, presents them for user approval, then writes `session-N-postmortem.md` and updates `project-learnings.md`.

  ---

  ## You Receive

  When invoked by executing-plans:
  - Feature folder path
  - Session number N
  - Session plan path
  - Deviation log path (or `none` if clean execution)
  - Implementation guide path

  When invoked manually: ask the user for each of the above.

  ---

  ## Step 1 — Check for Deviation Log

  If deviation log path is `none` or the file does not exist:
  > "Session N: clean execution — no deviations logged. No post-mortem needed."
  Exit. Do not continue.

  Load the deviation log.

  ---

  ## Step 2 — Load All Context

  Read in full:
  - Session plan
  - Implementation guide
  - `<feature-folder-path>/spec.md`
  - `docs/strategic-implementation/project-learnings.md` — if absent, note "no prior learnings" and treat as empty

  ---

  ## Step 3 — Count Total Session Logs

  Count all `session-*-log.md` files across all feature folders:
  `docs/strategic-implementation/*/session-*-log.md`

  Store the count. If count < 3: skip Step 7 (cross-session grep). If count ≥ 3: Step 7 runs.

  ---

  ## Step 4 — Per-Deviation Analysis

  For each `DEV-NNN` entry in the deviation log, note:
  - Agent category tag
  - Plan gap? value
  - Downstream impact? value
  - One-sentence summary of what this deviation reveals about planning or execution

  ---

  ## Step 5 — Review Existing Learnings

  From `project-learnings.md`, extract learnings whose agent category matches any category from Step 4.

  For each applicable learning, check: was the WHEN condition present in this session plan?
  - **Yes, DO guidance followed:** record as `[L-NNN] ✓ applied — [brief note]`
  - **Yes, DO guidance absent or violated:** record as `[L-NNN] not applied — [what happened instead]`
  - **No (WHEN condition not present):** skip

  ---

  ## Step 6 — Synthesize Learning Candidates

  For each deviation (or cluster of related deviations), determine:

  **a) New learning candidate**
  - Situation not covered by any existing learning
  - Format: `WHEN [specific situation], DO [specific action]`
  - Tag: `#single-session` (new learnings always start here)
  - Evidence: this deviation

  **b) Expansion candidate**
  - An existing learning this deviation extends
  - **Expansion rule:** change WHEN (broader situation) OR DO (refined action) — NEVER both simultaneously
  - Valid only when this deviation is a second concrete case (the original learning had one; this is the second)
  - Show: existing learning, proposed change (exactly which part changes), both evidence references

  **c) Conflict candidate**
  - This deviation's evidence contradicts an existing learning
  - Show: existing learning text, contradicting evidence, recommendation (keep / modify / retire)
  - User decides — do not pre-apply

  If a deviation is a pure execution error (typo, environment issue, nothing recurring): note "no learning candidate — [reason]"

  ---

  ## Step 7 — Cross-Session Grep (only if total log count ≥ 3)

  From each deviation in this log, extract 2–3 keywords from "What actually happened".
  Search for those keywords across all other `session-*-log.md` files.

  If a keyword pattern appears in 2+ other sessions: flag it as a potential multi-session pattern with the matching sessions listed. This is advisory — it does not automatically promote a learning to `#multi-session`. Promotion requires explicit user confirmation.

  ---

  ## Step 8 — Check Implementation Guide for Missed Updates

  Re-read Session N's `#### Meaningful Deviations` block.
  Compare against deviation log entries where `**Downstream impact?** yes`.

  If any `downstream-impact=yes` deviation is not in the Meaningful Deviations block: add it now.
  If any downstream session is missing a `⚠️ REVISION NEEDED` flag it should have: add it now.

  ---

  ## Step 9 — Present to User

  Present before writing anything to disk:

  ```
  ## Post-Mortem: Session N — [session name]
  Date: YYYY-MM-DD

  ### Existing Learning Application
  [L-NNN ✓ applied / not applied notes, or "No applicable existing learnings."]

  ### Proposed Learning Updates
  [For each candidate — New / Expansion / Conflict — show learning text, evidence, and for expansions: before/after]

  ### Cross-Session Patterns (if Step 7 ran)
  [Pattern and session references, or "None identified."]
  ```

  Ask: "Approve these updates? You can approve all, individually, or reject any. Conflicts require a decision."

  Wait for response before writing.

  ---

  ## Step 10 — Write Artifacts

  **Write `<feature-folder-path>/session-N-postmortem.md`:**

  ```markdown
  # Session N Post-Mortem: [session name]
  _Feature: [feature folder name]_
  _Date: YYYY-MM-DD_
  _Deviations reviewed: [count]_

  ## Learning Application
  [From Step 5]

  ## Approved Learning Updates
  [Each approved candidate with L-NNN reference]

  ## Rejected Candidates
  [Any rejected, with reason if given]

  ## Cross-Session Patterns
  [From Step 7, or "Not applicable — fewer than 3 sessions logged."]

  ## Implementation Guide Updates
  [Meaningful Deviations or REVISION NEEDED flags added in Step 8]
  ```

  **Update `docs/strategic-implementation/project-learnings.md`:**

  If file does not exist, create it with this header:
  ```markdown
  # Project Learnings
  _Last updated: YYYY-MM-DD_
  _Sessions tracked: 1_

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
  ```

  For each approved **new** learning: append under the appropriate `## [category] Learnings` heading. If no section for this category exists yet, create it first:
  ```markdown
  ## [category] Learnings
  ```
  Then append the entry:
  ```markdown
  ### L-NNN: [Short title]
  **WHEN** [specific situation], **DO** [specific action]
  **Tags:** `#[agent-category]` `#single-session`
  **Source:** [feature folder name, session N]
  **Evidence:** [1–2 sentences on what deviation led to this]
  **Last reviewed:** YYYY-MM-DD
  **Application notes:**
  ```

  For each approved **expansion**: update the existing entry's WHEN or DO (not both); append new evidence to Evidence field; update `**Last reviewed:**`. If user confirmed it's now `#multi-session`, update the tag.

  For each approved **conflict resolution**: apply user's decision (keep / modify / retire).

  Update `_Sessions tracked: N_` and `_Last updated: YYYY-MM-DD_` at top.

  ---

  ## After Step 10

  Invoke `superpowers:finishing-a-development-branch`.
  ```

- [ ] **Step 2: Commit**

  ```bash
  git add plugins/strategic-implementation/skills/post-mortem/SKILL.md
  git commit -m "feat(post-mortem): new skill for session post-mortems and project-learnings.md lifecycle"
  ```

- [ ] **Verify:** Step 1 exits cleanly if no log; Step 3 counts total logs conditionally; Step 6 all three candidate types present; expansion rule states "WHEN OR DO, never both"; Step 7 runs only if ≥3 sessions; Step 9 presents before writing; Step 10 writes both postmortem and project-learnings; entry format includes all fields; tag semantics and expansion/pruning rules documented in file header.

---

### Task 8 — Update `strategic-implementation/SKILL.md`: path passing and fast-path override

**File:** `plugins/strategic-implementation/skills/strategic-implementation/SKILL.md`

- [ ] **Step 1: Update Step 2 fast-path block**

  Replace:
  > `If fast-path: invoke superpowers:writing-plans, then superpowers:executing-plans. This skill ends here.`

  With:
  > `If fast-path: invoke superpowers:writing-plans, explicitly instructing it to save the plan to docs/strategic-implementation/YYYY-MM-DD-<feature-name>/implementation-guide.md (derive feature name from the one-sentence description; writing-plans supports path overrides via user instruction). Then invoke strategic-implementation:executing-plans. This skill ends here.`

- [ ] **Step 2: Update Step 4 — store and pass feature folder path**

  After "Present the completed spec to the user.", add:
  ```
  Store the feature folder path returned by implementation-drafter. Pass it to:
  - implementation-reviser in Step 5 (as spec file path: <feature-folder-path>/spec.md)
  - sessionize in Step 6
  - session-plan when the user triggers session planning
  Do not re-derive it from the spec title.
  ```

- [ ] **Step 3: Update Step 6 — pass feature folder path to sessionize**

  Change "Pass: The finalized spec document" to:
  ```
  Pass: the finalized spec document AND the feature folder path (stored in Step 4).
  ```

- [ ] **Step 4: Update End State — add path-passing instruction for session-plan**

  After the current closing text, add:
  ```
  When the user triggers session planning, invoke strategic-implementation:session-plan passing:
  - Implementation guide path: <feature-folder-path>/implementation-guide.md
  - Feature folder path: <feature-folder-path>/
  - Which session to plan (from the user)
  ```

- [ ] **Step 5: Commit**

  ```bash
  git add plugins/strategic-implementation/skills/strategic-implementation/SKILL.md
  git commit -m "feat(strategic-implementation): wire feature folder path through workflow, update fast-path and executing-plans references"
  ```

- [ ] **Verify:** Fast-path saves to `docs/strategic-implementation/` path; fast-path uses `strategic-implementation:executing-plans`; Step 4 mentions storing feature folder path; Step 6 passes it to sessionize; End State describes passing paths to session-plan.

---

### Task 9 — Update all 11 agent files: add "Processing Project Learnings" section

**Files:** all 11 agents in `plugins/strategic-implementation/agents/`

**Agent category tags:**

| Agent file | Category tag |
|---|---|
| `10k-foot.md` | `architecture` |
| `technical-expert.md` | `technical` |
| `scope-limiter.md` | `scope` |
| `future-proofing.md` | `architecture` |
| `security.md` | `security` |
| `data-model.md` | `data-model` |
| `api-contract.md` | `api-contract` |
| `test-coverage.md` | `test-coverage` |
| `performance.md` | `performance` |
| `dependency.md` | `dependency` |
| `frontend-engineer.md` | `frontend` |

Note: `10k-foot` and `future-proofing` both use `#architecture` — both review architectural concerns.

- [ ] **Step 1: For each of the 11 agent files, insert this section**

  **Placement:** between the last Review Task (or Step) section and the Output Format section — so learning checks run after domain review but before producing output.

  **Content (identical for all 11 agents, except substitute the correct `[agent-category]` value):**

  ```markdown
  ---

  ## Processing Project Learnings

  _This section is only active when the orchestrating skill injects a "Project Learnings" block into this prompt. If no such block was injected: skip this section entirely._

  **How learnings are injected:** The orchestrating skill reads `docs/strategic-implementation/project-learnings.md`, filters learnings tagged `#[agent-category]`, and injects them with context:
  - `sessionize` context → `#multi-session` learnings only
  - `session-plan` context → both `#single-session` and `#multi-session` learnings
  (Filtering is already applied before injection — you receive only what's relevant.)

  **For each injected learning:**
  1. Check: is the **WHEN** condition clearly present in the current plan?
     - **Yes, and the DO guidance is followed:**
       Note in RECOMMENDATIONS as `[L-NNN] ✓ applied — [one phrase]`
     - **Yes, but the DO guidance is absent or violated:**
       Add to FLAGS as `[L-NNN] condition met — guidance not followed: [one sentence on the gap]`
     - **No (WHEN condition not present in this plan):**
       Skip this learning — it does not apply here.
  2. Do not invent a WHEN condition where none exists. Only flag when the condition is clearly and specifically met.
  ```

  Replace `[agent-category]` with the correct value from the table above for each file.

- [ ] **Step 2: Commit all 11 agent files together**

  ```bash
  git add plugins/strategic-implementation/agents/
  git commit -m "feat(agents): add Project Learnings injection section to all 11 agents"
  ```

- [ ] **Verify (spot-check 3 agents):** Section present between last review step and Output Format; correct `[agent-category]` tag for that agent; `[L-NNN] condition met — guidance not followed` FLAG syntax present; `[L-NNN] ✓ applied` RECOMMENDATIONS syntax present; explicit note that section is skipped if no block injected.

---

## Verification: End-to-End Consistency Check

After all tasks complete, perform this pass:

- [ ] Trace the feature folder path from `implementation-drafter` (creates it) through `implementation-reviser` (receives spec file path), `sessionize`, `session-plan`, `executing-plans`, and `post-mortem` — the path variable must be received and passed at every handoff.
- [ ] Confirm `session-plan` auto-invoke says `strategic-implementation:executing-plans` (not `superpowers:`).
- [ ] Confirm `executing-plans` end checkpoint invokes `strategic-implementation:post-mortem` (not `superpowers:`).
- [ ] Confirm `post-mortem` Step 10 invokes `superpowers:finishing-a-development-branch`.
- [ ] Confirm all 11 agent files use the correct category tag from the table.
- [ ] Confirm `sessionize` Step 2a filters to `#multi-session` only; `session-plan` Step 2a filters to both.
- [ ] Confirm `implementation-guide` template's session block has `**Status:** \`pending\`` and `#### Meaningful Deviations`.
- [ ] Confirm `project-learnings.md` format in post-mortem includes: WHEN/DO, Tags (both category and session tag), Source, Evidence, Last reviewed, Application notes.

---

## Key Design Decisions

**Implementation-drafter saves spec before user reviews it (not after approval):** The feature folder path must be canonical from the moment of drafting. Saving after approval would risk re-drafts in new sessions creating new folders. Simpler: one folder, established once.

**Deviation log only created when deviations exist:** An empty log is ambiguous (was it executed cleanly, or not at all?). Absence = clean execution. Post-mortem Step 1 exploits this.

**New learnings always start as `#single-session`:** One data point is not enough to apply a learning at the implementation-guide level. It must prove out across two sessions before being elevated.

**`⚠️ REVISION NEEDED` flag is removed by the user, not automatically:** Automated removal would require the skill to determine "sufficiently updated" — a judgment call. The human removes it.

**`10k-foot` and `future-proofing` share `#architecture` tag:** Both review architectural concerns. Learnings about architectural patterns are equally relevant to both.
