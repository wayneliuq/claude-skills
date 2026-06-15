---
name: executing-plans
description: Executes an approved v2 execution plan, one deliverable at a time. Deliverable-gated (not session-based). Per-deliverable pre-flight env check, validation per declared method (preview / cli / tdd / post-hoc), atomic commit per deliverable, deviation log. Invokes post-execution for regression-check on completion.
---

# executing-plans

Executes one approved execution plan end-to-end. **Deliverable-gated** — each deliverable is an atomic unit with its own validation method declared at plan time.

You receive:
- Execution plan path (`<feature-folder>/execution-plan.md`)
- Feature folder path
- Autonomy level (`supervised` | `auto` | `yolo`)

Announce at start: "Starting execution: <feature slug>."

---

## Step 0 — Branch check

**Plan-mode entry-check:** if plan mode is active, call `ExitPlanMode` before writing files. (`execution-plan` is the only skill exempt from this rule.)

Run `git branch --show-current`. If result is `main` or `master`:

> ⚠️ **Warning: you are on `<branch>`.** Execution directly on main/master is strongly discouraged. Confirm to proceed, or switch to a feature branch first.

In `supervised` or `auto`: wait for explicit confirmation.
In `yolo`: proceed but log a `branch-risk` deviation.

---

## Step 1 — Read plan

**Resume check.** If `<feature-folder>/checkpoint.md` already exists (a prior session was interrupted, or context compacted): read it BEFORE the execution plan. Treat it as the source of truth for what's already done. Skip any deliverable already in the `## Done` section; pick up at the deliverable in `## In progress` (or the next `pending` one if `In progress` is empty).

Read `execution-plan.md` fully. Extract: deliverables, DAG order, parallel groups, and — per deliverable — the `Macro-deliverable` flag and its `Domains & file partition` (when `Macro-deliverable: true`). A macro-deliverable routes through Step 2-macro below; all others run the normal Step 2a–2f loop.

Initialize `validation-log.md` at `<feature-folder>/validation-log.md` with header:

```markdown
---
status: in-progress        # in-progress | complete | aborted | superseded
domains: [<domain>, ...]   # the integration-risk dependencies / areas this work touches
outcome: TBD                # one phrase; filled at post-execution from the PASS/FLAG/BLOCK verdict
supersedes: none            # <feature-slug> this work replaces, or `none`
---
# Validation log
_Feature: <slug> · Started: <date> · Autonomy: <level>_
```

The YAML frontmatter is **optional and additive** — it is the recall index's facet source (`status` / `domains` drive filtering; `supersedes` retires prior records). Older logs without it remain valid; the indexer tolerates absence. Set `status: aborted` if execution is abandoned before completion, so the work is never surfaced as proven precedent.

If `checkpoint.md` does not yet exist, initialize it at `<feature-folder>/checkpoint.md` with the four-section schema (Done / In progress / Open decisions / Unresolved deviations) — sections may start empty. See "Checkpoint schema" below.

Initialize deviation counter `DEV-001`.

### Initialize hook state (deterministic-trigger layer)

The plugin ships harness-fired hooks (`plugins/strategic-implementation/hooks/hooks.json`) that detect deliverable commits, edit-thrashing, error-loops, simplify thresholds, and validation-log additions deterministically — without depending on the agent to remember to check. Hooks are no-ops unless an active state file exists.

Write `.claude/strategic-implementation/state.json` (relative to repo root, NOT the feature folder — hooks read from a fixed location). Use the following shape:

```json
{
  "active": true,
  "feature_folder": "<feature-folder>",
  "feature_slug": "<slug>",
  "autonomy": "<level>",
  "deliverables_since_last_simplify": 0,
  "loc_since_last_simplify": 0,
  "simplify_thresholds": {"deliverables": 3, "loc": 400},
  "current_deliverable_edit_counts": {},
  "consecutive_failures": 0,
  "total_deliverables": <N>,
  "plan_path": "<feature-folder>/execution-plan.md",
  "brief_success_signal": "<verbatim success signal from brief>",
  "last_counted_sha": "",
  "pending_simplify": false,
  "pending_thrash_pause": false,
  "pending_error_loop": false,
  "pending_deviation_surface": false,
  "validation_log_last_mtime": ""
}
```

**Touched-file announcement (scope discipline).** After every Edit/Write batch within a deliverable, announce in chat:

> `touched: <comma-separated files> deliverable: D<n>`

This keeps the deliverable's file scope traceable in the conversation and makes an out-of-list edit visible to the PM. Treat it as part of the deliverable's build phase, not optional.

### Checkpoint schema (`<feature-folder>/checkpoint.md`)

A compact, compaction-survivable projection of execution state. One line per entry, no prose. Update at every atomic commit (see Step 2d).

```markdown
# Checkpoint — <feature slug>

## Done
- D1 — <name> — <commit-sha-short> — <date>

## In progress
- D<n> — <name> — started <date>

## Open decisions
- <one line; resolved by editing the line, not appending>

## Unresolved deviations
- <one line per active deviation; reference validation-log row id>

<!-- complete: <date> --> (only on final deliverable)
```

Rules:
- Same atomic commit as the deliverable's files and `validation-log.md` — never a separate edit.
- Strict projection of `validation-log.md`; if the two diverge, validation-log wins.
- On the final deliverable, append the `<!-- complete: <date> -->` marker.

---

## Step 2 — Execute DAG

For each deliverable group in DAG order (parallel groups run concurrently, sequential groups run in order). A deliverable marked `Macro-deliverable: true` runs through **Step 2-macro** instead of the per-step loop; every other deliverable runs the normal 2a–2f loop.

**Workflow-vs-sequential decision (always announced).** Emit the operator-visible decision once per run so it is observable even when no workflow is used: if the plan contains no macro-deliverable, announce `decomposable / below-threshold → sequential execution`; otherwise Step 2-macro emits its per-macro `macro-deliverable D<n>: … → workflow` line. This is the execution-time half of brief D5 — the operator always sees why the skill did (or did not) parallelize.

### Step 2-macro — Macro-deliverable execution (one workflow, one commit)

Fired only when a deliverable is `Macro-deliverable: true`. Emit the operator-visible decision line first: `macro-deliverable D<n>: <reason it qualifies> → workflow`.

**Capability gate.** If the `Workflow` tool is unavailable/disabled (`CLAUDE_CODE_DISABLE_WORKFLOWS`, older CLI) OR this is a resume after interruption → do NOT use a workflow; fall through to the sequential macro build in **Step 2-macro-fallback** (below).

**Workflow path** (capability present):
1. **Author and run a Workflow** that builds the domains with an explicit barrier — the contract/seam first, then the remaining domains in parallel against it:
   ```js
   const seam = await agent(buildContractPrompt)              // barrier: fully resolves before fan-out
   await parallel(domains.map(d => () => agent(buildDomainPrompt(d, { contract: seam }))))
   ```
   Do NOT use `pipeline()` for the seam→fan-out boundary (it has no barrier). Thread the contract artifact (`seam`) into each domain agent so the barrier is also a data handoff.
2. **Edit mechanism — shared-tree-disjoint (primary).** Per the D5/ED4a spike, workflow `agent()` edits land in the main working tree. Domain agents write their **disjoint file sets** directly in that shared tree. **Build agents run ZERO git commands** (the main thread owns all git) — this makes index.lock contention a non-issue. `agent(isolation:'worktree')` is forbidden. *Fallback only if disjointness can't be guaranteed:* detached worktree per domain + `git -C <wt> diff | git apply` (with `--3way` or sequential-rebuild on apply conflict) — never `cp`-of-output, never `isolation:'worktree'`.
3. **No nested sub-agents.** Workflow agents build only. Validation (2c), any `simplify`, and the single commit (2d) run on the **main thread after** the workflow returns. For a manual-`preview` macro-deliverable: the workflow builds + runs automatable checks, then hands back "built + checks green" for the human preview after return (workflows cannot pause mid-run).
4. **One atomic commit.** After validation passes, the main thread makes exactly ONE `D<n>:` commit touching all domain files + `checkpoint.md` + `validation-log.md`. **Invariant: no intermediate per-domain commits land on the branch** — this is what keeps the git-log hook counters correct (a macro-deliverable counts as one deliverable).
5. **Deferred concurrency proof.** Because an in-session live trial may validate cached behavior, log a `validation-honesty` deviation and surface a one-line follow-up: "Operator: in a fresh session (cache reloaded), re-run this macro-deliverable and confirm concurrent domains in `/workflows`; record the result in `validation-log.md`."

### Step 2-macro-fallback — Sequential macro build

When the capability gate routes here: build the domains **sequentially in the working tree** (contract first, then each domain), run validation, then the same single `D<n>:` atomic commit. Surface: `workflow unavailable → built sequentially`. **Resume reconciliation:** if `checkpoint.md` shows this macro-deliverable in-flight AND the working tree is dirty with its declared domain paths, `git checkout -- <those paths>` (reset to HEAD) before rebuilding — or require a clean tree and surface the discarded partial work — so a mid-workflow interruption never double-applies. This backs the "no lost work" guarantee.

After Step 2-macro (either path) completes its commit, continue to the next deliverable (skip 2a–2f for this one; 2e consumer-audit/2f simplify-trigger still apply via the post-commit hook).

### Step 2a — Pre-flight env check

**Point-of-need recall (advisory).** Before building, for a `Macro-deliverable` OR an `Integration-risk class: a|b|c` deliverable, query memory for how similar work was done before — so you reuse a proven approach instead of re-deriving it (e.g. rediscovering that an end-to-end test should run in a container first):

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/memory/recall.sh" "<deliverable name + domains>" --domains "<domains>" --k 3
```

This hot path is **BM25-only** (no embedding model is loaded per deliverable). It reads the index only — it never builds or re-embeds inline. Treat any output as advisory pre-flight context: it **informs, never dictates** the build or validation-method choice. Empty output → proceed silently (no index yet, or no good match). The command degrades to silence on any error and never blocks execution.

Then verify the prerequisites for the deliverable's validation method:

- **`preview`:** Claude Code preview tool available; dev server startable. If not available: apply preview-unavailable fallback (below).
- **`cli`:** the CLI command runnable; required binaries in PATH.
- **`tdd`:** test runner available; baseline suite passes.
- **`post-hoc`:** no automated pre-check; note manual validation required.

If pre-flight fails: log a `blocker` deviation and stop. Surface to PM with what's missing.

### Preview-unavailable fallback

If `preview` pre-flight fails:
- `supervised` / `auto`: pause. Surface to PM: "Preview unavailable. Proceed with manual validation, or switch deliverable to TDD?"
- `yolo`: auto-escalate to TDD. Log an `auto-escalation` deviation. Write a minimal acceptance test before building.

### Step 2b — Build

Implement the deliverable per its steps. Rules:

- **Only files named in the deliverable.** Unrelated touches = deviation.
- **TDD where declared (vertical-slice tracer-bullet rule).** When validation is `tdd`, write ONE failing test for the next thinnest slice of user-observable behavior, make it pass, commit-or-stage, then move to the next slice. Do **not** write all tests first then all implementation — that produces tests of imagined behavior and the shape of things, not user-facing behavior. The horizontal-slice anti-pattern (test-batch then code-batch) is rejected.
- **Code discipline:**
  - Write the minimum that passes validation. No speculative abstractions.
  - Match existing conventions (style, naming, error handling).
  - Clean up only code YOUR changes made unused — leave pre-existing dead code alone.
  - Do not "improve" adjacent code.
- **Rework guardrails (per-deliverable counters):**
  - **Edit-thrashing:** the `hook-edit-tracker.sh` hook tracks Edit/Write tool calls per file and sets `pending_thrash_pause` on the 4th edit to the same file (>3 edits). The Stop orchestrator surfaces this as injected guidance — pause, re-read the brief and the deliverable's plan block before any further Edit/Write to that file. Log a `thrash-pause` deviation. In `auto`, decide and proceed; in `supervised`, surface and pause. The agent's own in-text counter remains a fallback if hooks are disabled.
  - **Error-loop:** the `hook-error-tracker.sh` hook tracks consecutive tool failures and sets `pending_error_loop` at 3 consecutive failures. The Stop orchestrator surfaces "do not retry; escalate to triage" as injected guidance. Escalate to `post-execution:triage` with the error trace as the reported issue. Log an `error-loop-escalation` deviation. Hook is primary; in-text counter is fallback.

**Registry-tracked doc bundle.** If the deliverable's `may-invalidate` field is non-empty, after building primary changes, prompt the PM:

> "Deliverable D<n> may invalidate `<doc-paths>`. Update them now in the same commit?"

In `auto`, surface and proceed; in `supervised`, pause for explicit reply; in `yolo`, surface and proceed without waiting. Apply doc edits in the same working tree so they land in this deliverable's atomic commit. Never amend a prior deliverable's commit to add docs.

### Step 2c — Validate

Run the declared validation:
- **preview:** start preview, capture the observable behavior, confirm against the deliverable's expected behavior.
- **cli:** run the command, assert expected output.
- **tdd:** run the test written in 2b; must pass. Also run the full suite — no new failures.
- **integration-test:** run the test against the real third-party runtime / network / cross-component seam (no mocks at the integration point). Must pass. Also run the full suite — no new failures.
- **post-hoc:** surface to PM with what to inspect. In `yolo`, skip inspection, log `yolo-skip`.

**Mocked-seam flag (not a deviation; a post-execution marker).** If the deliverable's `Integration-risk class` is `a|b|c` AND validation passed only via tests that mock the dependency (e.g. `tdd` on a class-`a` deliverable that the plan slipped past review), append to `validation-log.md`:

```markdown
## FLAG (mocked-seam) — D<n>
**Class:** <a|b|c>  **Validation:** <method>
**Mocked dependency:** <name>
**Note:** validation passed via mocked tests; integration-risk seam not exercised. Surface for post-execution review.
```

Execution continues; `post-execution` regression-check reads these flags.

**Validation-approach capture (cross-domain / integration-risk deliverables).** When a deliverable is `Macro-deliverable: true` OR `Integration-risk class: a|b|c`, after validation passes append a small block to `validation-log.md` recording the validation **approach actually used** — the pipeline / infrastructure, not just the one-word method (e.g. "docker compose up → integration-test in CI → manual staging smoke"). This is what `execution-plan`'s validation-approach recall later greps so similar future work reuses it instead of re-guessing.

```markdown
## APPROACH — D<n>
**Method:** <preview | cli | tdd | integration-test | post-hoc>
**Domains:** <e.g. backend / api-contract / frontend, or the integration-risk dependency>
**Approach:** <the actual pipeline / infra used to validate the integrated outcome>
```

This block is **additive** — it does not change the header or the `DEV-NNN` deviation schema, and absence in older logs is expected (recall tolerates it).

**Gotcha capture (any deliverable that cost avoidable rework).** When a deliverable burned time on a wrong path that a prior lesson would have prevented — or that a future similar deliverable should avoid — append a `## GOTCHA` block. This is the "we lost time on X; do Y first" note, and it is the highest-signal record for point-of-need recall (it directly prevents re-derivation, e.g. rediscovering that an end-to-end test must run in a container first).

```markdown
## GOTCHA — D<n>
**Domains:** <areas / integration-risk dependency this applies to>
**Lost time on:** <the wrong path or wasted assumption>
**Do instead:** <the corrective action a future similar deliverable should take first>
```

Also additive; absence is expected in older logs.

If validation fails: apply **Failure Protocol** below.

### Step 2d — Commit

Atomic commit per deliverable:

```
D<n>: <one-sentence outcome>
```

Example: `D3: add product-brief revision loop`.

Stage only the files named in this deliverable — plus any registry-tracked docs updated in Step 2b under `may-invalidate`, plus the registry file itself with **`Last Updated` bumped to today** for each updated doc's row, plus the updated `<feature-folder>/checkpoint.md` (move the deliverable from `## In progress` to `## Done` with its short SHA), plus the updated `validation-log.md`. All in one atomic commit. Post-execution verifies these advances.

### Step 2e — Mark complete

Before flipping status: if the deliverable has a `Consumer audit` subsection, walk the list. Every entry must be `updated-in-this-deliverable`, `updated-in-D<n>` (where D<n> is already complete or scheduled), `unaffected-because-...`, or `explicit-skip-because-...`. Any entry left as TBD, missing, or contradicted by what was actually changed → log a `consumer-audit-mismatch` deviation and surface to PM before proceeding.

In `execution-plan.md`, update deliverable status: `pending` → `complete`.

### Step 2f — Maybe-invoke simplify (mid-execution trigger)

**Primary trigger:** the `hook-bash-counter.sh` hook detects the deliverable commit and sets `pending_simplify` when thresholds cross. The Stop orchestrator surfaces "invoke simplify now" as injected guidance on the next turn. The agent acts on that injected guidance — no need to compute counters in-skill.

**Fallback (hooks disabled or skipped):** compute counters via `git log` directly. Defaults: `every_n_deliverables = 3`, `loc_threshold = 400` (declared in `simplify/SKILL.md`).

**Skip rule:** if total plan deliverables ≤ 3, do NOT invoke mid-execution. The final pass in `post-execution` regression-check is sufficient.

Otherwise, derive counters from `git log` (no new state file):

```bash
# Reference point: last simplify-report-NN.md commit, or feature-folder creation if none.
LAST_REF=$(git log -1 --format=%H -- "<feature-folder>/simplify-report-*.md" 2>/dev/null \
  || git log --diff-filter=A --format=%H -- "<feature-folder>" | tail -1)

DELIVERABLES_SINCE=$(git log --oneline "$LAST_REF"..HEAD -- "<feature-folder>/checkpoint.md" | wc -l)
LOC_SINCE=$(git log -p "$LAST_REF"..HEAD -- ':(exclude)<feature-folder>/' | grep -E '^[+-]' | grep -vE '^[+-]{3}' | wc -l)
```

If `DELIVERABLES_SINCE >= every_n_deliverables` OR `LOC_SINCE >= loc_threshold`: invoke `strategic-implementation:simplify` with the feature folder. The skill writes `<feature-folder>/simplify-report-NN.md` and returns the path.

**Surface the report.** Append to chat:

> Simplify report: `<path>` — <total> findings (high: <h>, med: <m>, low: <l>). Disposition each finding conversationally (apply / defer / dismiss) before the next deliverable, or proceed and let undispositioned findings surface in the deviation log.

**Disposition rules:**
- `supervised`: pause for PM to fill every finding's disposition before next deliverable.
- `auto`: proceed; log a `simplify-disposition-pending` deviation only if the next atomic commit lands with unfilled dispositions in the latest report.
- `yolo`: proceed; log nothing.

The `simplify` skill never auto-edits source. PM-applied changes (when disposition is `apply`) become a follow-up deliverable or land as part of a future deliverable's same-file edits — never as a side-effect of `simplify` itself.

---

## Failure Protocol

On validation failure:

**Classify:**
- **Determinate** (clear root cause): fix → re-validate. If that fails, treat as assumption-based.
- **Assumption-based** (must infer): state the assumption explicitly before any fix.

**Attempt 1:**
1. State assumption / root cause in one sentence.
2. Fix. Re-validate.
3. Success → log `retry` deviation, continue.
4. Failure → revert changes. Confirm baseline restored.

**Re-examine:**
- List all assumptions. Rate each `high` / `medium` / `low`.
- If all `high`: **EXIT** (see Exit Report).
- Else: revise the lowest-confidence assumption.

**Attempt 2** (only if revision yields a distinct fix):
1. **Precondition:** if `error-loop-escalation` has already triggered for this deliverable (3+ consecutive failures), do NOT attempt Attempt 2 — proceed directly to EXIT and Exit Report.
2. State revised assumption.
3. Fix. Re-validate.
4. Success → log deviation, continue.
5. Failure → revert. **EXIT.**

### Exit Report

```
## Execution Blocked

**Deliverable:** D<n> — <name>
**Failure:** <exact error / test output>

**Confirmed facts:**
- ...

**Assumptions held:**
- <assumption> — confidence: high/med/low
- ...

**Attempts:**
1. <what> → <outcome>
2. <what> → <outcome> (if applicable)

**Most suspect assumption:** <one sentence>

**Blocked on:** <what PM input or external info is needed>

All failed-attempt changes reverted. Working tree at baseline.
```

Do not mark complete. Do not proceed to next deliverable. Await PM direction.

---

## Deviation logging

A deviation exists on any of: blocker, retry, user-correction, reversal, ambiguity-decision, auto-escalation, yolo-skip, branch-risk, consumer-audit-mismatch, thrash-pause, error-loop-escalation, repro-blocked, spec-ambiguity-redirect, spec-ambiguity-override, simplify-disposition-pending.

Append to `validation-log.md`:

```markdown
## DEV-NNN
**Type:** blocker | retry | user-correction | reversal | ambiguity-decision | auto-escalation | yolo-skip | branch-risk | consumer-audit-mismatch | thrash-pause | error-loop-escalation | repro-blocked | spec-ambiguity-redirect | spec-ambiguity-override | simplify-disposition-pending
**Deliverable:** D<n>
**Plan said:** <verbatim>
**Actually:** <what happened>
**Resolution:** <how resolved>
**Downstream impact?** yes | no — <if yes: one sentence on what changes for later deliverables>
**Agent category:** alignment | boundaries | runtime-risk | tests | frontend | technical | simplify
```

If `downstream impact: yes` and a later deliverable is affected: prepend `⚠️ REVISION NEEDED — <one sentence>` to that deliverable's block in `execution-plan.md`. Surface flagged deliverables to the PM before starting them.

---

## Step 3 — All-deliverables checkpoint

When all deliverables are marked complete:

1. Announce: "All deliverables complete. Running regression check."
2. Invoke `strategic-implementation:post-execution` in `regression-check` mode with the feature folder path.
3. `post-execution` writes `post-execution-report.md` and reports back.
4. If the report status is `PASS`: announce feature complete.
5. If `FLAG` or `BLOCK`: surface to PM; do not declare complete until resolved.
6. **Deactivate hook state.** Set `.active = false` in `.claude/strategic-implementation/state.json` so subsequent sessions on the same repo do not trigger the counter or Stop-orchestrator hooks. Use:

   ```bash
   jq '.active = false' .claude/strategic-implementation/state.json \
     > .claude/strategic-implementation/state.json.tmp \
     && mv .claude/strategic-implementation/state.json.tmp .claude/strategic-implementation/state.json
   ```

### Learnings trigger

If `validation-log.md` has ≥2 meaningful deviations (judgment — typo-fixes don't count), offer the PM:

> "N meaningful deviations logged. Run learnings synthesis? (yes/skip)"

On yes: invoke `post-execution` in `learnings-synthesis` mode.

---

## Constraints

- No execution on `main`/`master` without explicit consent.
- No deliverable skipped without explicit PM decision.
- One commit per deliverable. No batching, no amending prior deliverable commits.
- No LOC budget — fitness is the gate, not size.
- Deviation log is append-only. Never rewrite.
- Hard decisions in the brief and plan are immutable during execution.
- Every deliverable's atomic commit must touch `<feature-folder>/checkpoint.md` (and `validation-log.md`). This guarantees git-log derived counters elsewhere in the chain stay accurate.

---

## Tone discipline

Terse. Substance exact. Drop articles, filler ("just", "really", "basically"), pleasantries, hedging. Fragments OK if unambiguous. One sentence per update is enough.

**Carve-outs (do NOT compress):** code blocks, tool output, BLOCK/FLAG callouts, irreversible-action warnings, PM-facing approval prompts.

---

## Record routing — externalized artifact store

Per-feature **records** (brief / plan / validation-log / checkpoint / reports / mockup / brief-meta) route through the store adapter, not the feature folder directly: wherever a step says write/read `<feature-folder>/<file>`, use the store address `<repo-id>/<date-slug>/<file>` with in-repo fallback. Full read/write/fallback protocol: [`scripts/store/README.md`](../../scripts/store/README.md#record-routing-protocol-agent-facing). **Durable tier — `project-learnings.md`, `documentation-registry.md` — stays in-repo, never routed to the store.**
