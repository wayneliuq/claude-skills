---
name: post-execution
description: Consolidated post-execution skill replacing v1's bug-fix + post-mortem + end-of-implementation. Three modes — regression-check (auto after all deliverables complete), triage (PM-reported behavioral issue), learnings-synthesis (validation-log accumulation).
---

# post-execution

Three modes, selected by the caller based on context.

You receive:
- `mode`: `regression-check` | `triage` | `learnings-synthesis`
- Feature folder path
- For `triage`: the PM's issue report
- For `learnings-synthesis`: (no extra input — reads validation-log)

---

## Mode: regression-check

**Plan-mode entry-check:** if plan mode is active, call `ExitPlanMode` before writing files. (`execution-plan` is the only skill exempt from this rule.)

Triggered automatically by `executing-plans` when the final deliverable is marked complete.

### Steps

1. **Discover modified file set.** Union of:
   - Files listed across all deliverables in `execution-plan.md`
   - Files touched in git history since the feature branch diverged (`git diff --name-only <base>..HEAD`)
2. **Cross-contamination check.** For each modified file, grep the rest of the repo for imports/references. For each dependent, decide: is its behavior potentially affected? Flag dependents whose tests should be rerun.

   **Step 2a — Plugin config security scan.** Gate on whether the modified-file set above includes any path under `.claude/` (settings, hooks, MCP, agent configs). If no `.claude/` path was modified, skip with the line "no plugin-config files touched."

   If `.claude/` files were modified, run inlined static checks across **five rule categories**. Apply a placeholder/env-ref exclusion list (`<.*>`, `\$\{?[A-Z_]+\}?`, `placeholder`, `example`, `your-.*-here`, `xxx+`) before any Critical-tier escalation; matches against the exclusion list demote to Medium.

   - **Secrets** — scan `settings.json`, `mcp.json`, hook scripts, agent configs for: generic `[A-Z0-9_]*API_KEY\s*[:=]\s*["'][A-Za-z0-9_-]{16,}` (Critical only if not excluded; else Medium); `sk-[A-Za-z0-9]{20,}` (OpenAI, Critical); `Bearer\s+[A-Za-z0-9._-]{20,}` (Critical); `xox[baprs]-[A-Za-z0-9-]{10,}` (Slack, Critical); `AKIA[0-9A-Z]{16}` (AWS, Critical); `gh[pousr]_[A-Za-z0-9]{30,}` (GitHub, Critical); `-----BEGIN [A-Z ]*PRIVATE KEY-----` (PEM, Critical).
   - **Permissions audit** — `Bash\(\*\)` in `allow` array (High); missing `deny` block when `allow` is broad (High); presence of `--no-verify` or `--dangerously-skip-permissions` flags (High).
   - **Hook injection** — `eval ` in hook commands (Critical); backtick command substitution (Critical); `\$\([^)]*\$[A-Z_]` nested-`$()`-with-var (Critical); `curl[^|]*\|\s*sh` pipe-to-shell (Critical); silent error suppression `2>/dev/null` or `\|\| true` (Medium/log only — common in legitimate probe checks; quote-context analysis is a known grep limitation, reserved for behavioral validation).
   - **MCP risk profile** — `npx -y` in MCP server commands (Medium/log; documented install pattern); `npx -y` combined with unpinned package version or non-registry source (High); hardcoded env values matching key-shapes (High); shell-running MCP servers (High).
   - **Agent config review** — agent definitions with no model spec (Medium/log); unrestricted tool access shape (Medium/log).

   **Severity gating:** Critical → Status `BLOCK` (sets the regression-check status line to BLOCK and halts post-execution sign-off until resolved); High → Status `FLAG`; Medium/log-only → log to report only, no status change.

   Append findings to `post-execution-report.md` under heading `## Plugin config security scan` with one bullet per finding: severity, rule, file, line, snippet (≤80 chars). If no `.claude/` files modified or no findings, write a one-line "no findings."

3. **Run the existing test suite.** Use the project's test command (detect from `package.json` / `pyproject.toml` / `Makefile`). Record failures. A test that was passing before this feature and fails now is a regression.
4. **Author acceptance tests for feature flows.** For every brief deliverable that was not validated via TDD during execution, author an E2E or integration test now that exercises its user-observable outcome. Run it.
5. **Goal-backward claim verification.** Build the suspect-set: deliverables whose `Validation` is `post-hoc` OR which carry a `FLAG (mocked-seam)` entry in `validation-log.md`. Take the first **3 matches**. If none, skip this step.

   For each matched deliverable, read its expected outcome from `execution-plan.md` (not from any commit message, summary, or validation-log narrative). For each named artifact (function / route / consumer / config key / file path), run a single grep and record yes/no — does it exist in the codebase as the plan claims? Use the acceptance test authored in Step 4 (if any) as one of the yes/no signals.

   Append findings to the report under `## Goal-backward verification` as one block per deliverable: `D<n>: <artifact> — yes|no`. Any `no` → status BLOCK.

6. **Registry-update verification.** Load `docs/strategic-implementation/documentation-registry.md` if present. For each deliverable's `may-invalidate` entries (from `execution-plan.md`), check the registry row's `Last Updated` is ≥ feature start date. For each **stale entry** (`Last Updated` did not advance), surface:

   > "Deliverable D<n> declared `may-invalidate <path>` but registry row was not updated. Update the doc now? (y/n/skip)"

   On `y` in `supervised`: pause. On `auto` / `yolo`: surface but do not block. Cross-mode rule: stale registry entries block cycle close in `supervised`; in `auto` and `yolo`, they appear in the report as a FLAG but do not BLOCK.

7. **Visual-contract diff prompt.** For each deliverable in `execution-plan.md` whose `Visual contract:` is non-empty (a mockup file path), prompt:

   > "Open `<mockup-path>` and compare against the shipped UI for D<n>. Match? (y/n/notes)"

   Capture the answer in the report under `## Visual diff`. A `n` (mismatch) is a FLAG, not a BLOCK — the PM may accept divergence, but it is recorded.

8. **Write** `<feature-folder>/post-execution-report.md`:

```markdown
# Post-execution report
_Date: <date> · Feature: <slug>_

## Modified files
<bulleted, with "touched by deliverable D<n>" annotations>

## Cross-contamination
<dependents examined; regressions flagged>

## Plugin config security scan
<bulleted findings: severity, rule, file, line, snippet — or "no plugin-config files touched" / "no findings">

## Test suite run
- Command: <...>
- Result: <n passed, m failed>
- Regressions: <list or "none">

## Acceptance tests authored
<list — which criteria, which test files>

## Goal-backward verification
<one block per matched deliverable, or "skipped — no post-hoc or mocked-seam matches">

## Registry-update verification
<bulleted: "D<n>: <doc-path> — Last Updated advanced | stale (PM action: <updated|skipped>)" or "skipped — no may-invalidate entries">

## Visual diff
<bulleted: "D<n>: <mockup-path> — match | mismatch (notes: ...)" or "skipped — no Visual contract entries">

## Status
<PASS / FLAG / BLOCK — BLOCK if regressions unresolved or any goal-backward `no` or any Critical plugin-config finding. Stale registry entries are FLAG in auto/yolo, BLOCK in supervised. Visual mismatches are FLAG. Plugin config: <PASS | FLAG | BLOCK> alongside the overall status.>
```

9. If any regression is unresolved or any goal-backward verification returns `no`: surface to PM. Otherwise announce completion.

---

## Mode: triage

**Plan-mode entry-check:** if plan mode is active, call `ExitPlanMode` before writing files. (`execution-plan` is the only skill exempt from this rule.)

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

**Plan-mode entry-check:** if plan mode is active, call `ExitPlanMode` before writing files. (`execution-plan` is the only skill exempt from this rule.)

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
