---
name: post-execution
description: Post-execution skill with three modes — regression-check (auto after all deliverables complete), triage (PM-reported behavioral issue), learnings-synthesis (validation-log accumulation).
---

# post-execution

Three modes, selected by the caller based on context.

You receive:
- `mode`: `regression-check` | `triage` | `learnings-synthesis`
- Feature folder path
- For `triage`: the PM's issue report
- For `learnings-synthesis`: (no extra input — reads validation-log)

**Plan-mode entry-check (all modes):** if plan mode is active, call `ExitPlanMode` before writing files. (`execution-plan` is the only skill exempt from this rule.)

---

## Mode: regression-check

Triggered automatically by `executing-plans` when the final deliverable is marked complete.

The mode is intentionally lean. Across 24 historical regression-check reports, only the dependent-file impact, post-hoc artifact spot-check, plugin-config scan, and final simplify pass produced real catches; the other sections were bookkeeping. This rewrite drops the bookkeeping, gates the conditional checks, and auto-applies trivial fixes the skill already handles (stale registry rows, missing one-line cross-references) rather than nagging the PM for disposition.

### Steps

1. **Cross-contamination scan.** Build the modified-file set as the union of (a) files listed across all deliverables in `execution-plan.md` and (b) files touched in git history since the feature branch diverged (`git diff --name-only <base>..HEAD`). For each modified file, grep the rest of the repo for imports/references. For each dependent, decide: is its behavior potentially affected? Flag dependents whose tests should be rerun. The modified-file list is an input to this analysis only — it is no longer a standalone report section; surface the filename inline under each dependent finding when relevant.

2. **Goal-backward verification (gated).** Skip with the one-liner "skipped — no post-hoc or mocked-seam matches" under `## Goal-backward verification` if no deliverable in `execution-plan.md` has `Validation: post-hoc` and no `FLAG (mocked-seam)` entry exists in `validation-log.md`.

   Otherwise, build the suspect-set (post-hoc OR mocked-seam) and take the first **3 matches**. For each matched deliverable, read its expected outcome from `execution-plan.md` (not from any commit message, summary, or validation-log narrative). For each named artifact (function / route / consumer / config key / file path), run a single grep and record yes/no — does it exist in the codebase as the plan claims? Append findings to the report under `## Goal-backward verification` as one block per deliverable: `D<n>: <artifact> — yes|no`. Any `no` → status BLOCK.

3. **Plugin config security scan (gated).** Gate on whether the modified-file set includes any path under `.claude/` (settings, hooks, MCP, agent configs). If no `.claude/` path was modified, write the one-liner "no plugin-config files touched" under `## Plugin config security scan` and proceed.

   If `.claude/` files were modified, run inlined static checks across **five rule categories**. Apply a placeholder/env-ref exclusion list (`<.*>`, `\$\{?[A-Z_]+\}?`, `placeholder`, `example`, `your-.*-here`, `xxx+`) before any Critical-tier escalation; matches against the exclusion list demote to Medium.

   - **Secrets** — scan `settings.json`, `mcp.json`, hook scripts, agent configs for: generic `[A-Z0-9_]*API_KEY\s*[:=]\s*["'][A-Za-z0-9_-]{16,}` (Critical only if not excluded; else Medium); `sk-[A-Za-z0-9]{20,}` (OpenAI, Critical); `Bearer\s+[A-Za-z0-9._-]{20,}` (Critical); `xox[baprs]-[A-Za-z0-9-]{10,}` (Slack, Critical); `AKIA[0-9A-Z]{16}` (AWS, Critical); `gh[pousr]_[A-Za-z0-9]{30,}` (GitHub, Critical); `-----BEGIN [A-Z ]*PRIVATE KEY-----` (PEM, Critical).
   - **Permissions audit** — `Bash\(\*\)` in `allow` array (High); missing `deny` block when `allow` is broad (High); presence of `--no-verify` or `--dangerously-skip-permissions` flags (High).
   - **Hook injection** — `eval ` in hook commands (Critical); backtick command substitution (Critical); `\$\([^)]*\$[A-Z_]` nested-`$()`-with-var (Critical); `curl[^|]*\|\s*sh` pipe-to-shell (Critical); silent error suppression `2>/dev/null` or `\|\| true` (Medium/log only — common in legitimate probe checks; quote-context analysis is a known grep limitation, reserved for behavioral validation).
   - **MCP risk profile** — `npx -y` in MCP server commands (Medium/log; documented install pattern); `npx -y` combined with unpinned package version or non-registry source (High); hardcoded env values matching key-shapes (High); shell-running MCP servers (High).
   - **Agent config review** — agent definitions with no model spec (Medium/log); unrestricted tool access shape (Medium/log).

   **Severity gating:** Critical → Status `BLOCK` (sets the regression-check status line to BLOCK and halts post-execution sign-off until resolved); High → Status `FLAG`; Medium/log-only → log to report only, no status change. Append findings under `## Plugin config security scan` with one bullet per finding: severity, rule, file, line, snippet (≤80 chars).

4. **Registry-update verification + small-cross-reference auto-apply.** Load `docs/strategic-implementation/documentation-registry.md` if present. For each `may-invalidate` entry declared by any deliverable in `execution-plan.md`, check whether the corresponding registry row's `Last Updated` advanced past feature start. **Two auto-apply classes are in scope, both bounded to fixes the skill historically performed inline:**

   - **(i) Stale registry rows.** For each stale row where the doc itself was edited in the feature commits OR the row's `may-invalidate` target is plumbed by a deliverable that demonstrably ran (its files exist, its commit landed) → silently bump `Last Updated` to today; append one line to the Status section's `Auto-applied (this run):` bullet list naming the row.
   - **(ii) Missing one-line cross-references.** If a deliverable's `may-invalidate` declared a doc that should now cross-reference a new artifact (e.g., a new module path, file, or section heading the deliverable introduced), and the registry row was bumped but the doc itself is missing that one-line backlink → insert a one-line backlink at the relevant section heading; append one line to `Auto-applied (this run):` naming the doc.
   - **Anything else** — doc not edited; `may-invalidate` target unclear; cross-reference location not obvious; multi-line edit required → escalate as FLAG under the Status section's `Registry:` summary; do NOT auto-apply.

   The auto-apply scope is intentionally narrow: it never extends to simplify-report findings, test failures, or source-code changes — those require PM disposition.

5. **Final simplify pass (mandatory).** Invoke `strategic-implementation:simplify` against the full feature diff (`git diff <merge-base>...HEAD`). The skill writes `<feature-folder>/simplify-report-NN.md` (next monotonic number). Capture the report path and the high/med/low counts. PM-disposition is captured conversationally (apply / defer / dismiss per finding; the report file is output-only, not hand-edited). In `auto`/`yolo`, undispositioned findings become a FLAG in this report's status, not a BLOCK.

6. **Write report + token-report telemetry.** Write `<feature-folder>/post-execution-report.md` using the template below — exactly five top-level sections, in this reader-facing order: Cross-contamination → Goal-backward → Plugin-config → Simplify → Status. The previous report's `## Modified files`, `## Test suite run` (as a section), `## Acceptance tests authored`, `## Registry-update verification` (as a section), and `## Visual diff` are removed; the test-suite and registry signals appear as one-liners inside Status.

   ```markdown
   ---
   status: complete           # complete (PASS) | flagged (FLAG) | aborted | superseded — derived from the Status verdict below
   domains: [<domain>, ...]   # areas / integration-risk dependencies this feature touched
   outcome: <one phrase>      # what shipped, in a phrase
   supersedes: none           # <feature-slug> this work replaces, or `none`
   ---
   # Post-execution report
   _Date: <date> · Feature: <slug>_

   ## Cross-contamination
   <dependents examined; regressions flagged. Modified-file context is inline under each finding (filename + deliverable annotation) — no separate inventory section.>

   ## Goal-backward verification
   <one block per matched deliverable: `D<n>: <artifact> — yes|no`, or "skipped — no post-hoc or mocked-seam matches">

   ## Plugin config security scan
   <bulleted findings: severity, rule, file, line, snippet — or "no plugin-config files touched" / "no findings">

   ## Simplify final pass
   - Report: `<simplify-report-path>`
   - Findings: <total> (high: <h>, med: <m>, low: <l>)
   - Disposition: <all-filled | <n> unfilled — FLAG>

   ## Status
   <PASS / FLAG / BLOCK — BLOCK if any goal-backward `no` or any Critical plugin-config finding. Visual mismatches and unfilled simplify dispositions are FLAG. Plugin config: <PASS | FLAG | BLOCK> alongside the overall status.>
   - Test suite: <one-liner observed from `validation-log.md` — "green per validation-log" | "<n> regressions logged — FLAG" | "n/a — no executable test surface". Reads from the feature's existing validation-log, not from a separate test-suite re-run.>
   - Registry: <"all current" | "auto-applied: <n> row(s)" | "<n> stale — FLAG">
   - Auto-applied (this run): <bulleted list of fixes regression-check made without prompting, or "none">
   ```

   After writing the report, invoke the telemetry helper:

   ```bash
   bash plugins/strategic-implementation/scripts/token-report.sh "<feature-folder>"
   ```

   Verify `<feature-folder>/token-report.md` landed; do NOT read or interpret its contents — the script is the source of truth, the skill never spends model tokens on the telemetry. Any `unavailable` sections are expected behavior (transcript format drift, missing rtk, etc.) and never block. Exit code 0 from the script means success; non-zero is a `blocker` deviation.

If any regression is unresolved or any goal-backward verification returns `no`: surface to PM. Otherwise announce completion.

---

## Mode: triage

Triggered when PM reports a behavioral issue after execution completed (bug, unexpected behavior, missing edge case).

### Steps

1. Read the PM's report. Identify: what surface, what the expected behavior was, what was observed.

   **Step 1.5 — Specification-ambiguity check (before repro).** Scan the last 5 PM messages in the current session. If any pair shows ≥60% phrase-overlap (agent-eyeballed — substantive nouns and verbs repeated, not just function words), the issue is likely specification ambiguity, not a code defect. On detection: do **not** proceed to repro. Surface to PM:

   > "Detected repeated/paraphrased instruction in last 5 turns — `<paraphrase A>` vs `<paraphrase B>`. This pattern usually indicates the brief or plan is ambiguous. Recommend invoking `product-brief-drafter:revise` rather than attempting another fix. Proceed to repro anyway? (y/N)"

   Default N. On N: route to brief revision via the orchestrator. Log a `spec-ambiguity-redirect` deviation and stop. On y: proceed to Step 2; log `spec-ambiguity-override`.

2. **Build a deterministic repro before hypothesizing.** Don't propose fixes until a fast, agent-runnable signal distinguishes "broken" from "fixed" (failing test / CLI snapshot / headless script / bisect — whichever is cheapest). If none can be built, log a `repro-blocked` deviation and surface to PM rather than dive into code. Rank the plausible causes and rule out the top ones first. Tag any debug logs with a unique prefix (e.g. `[DBG-<short-uuid>]`) so Step 5 records it and cleanup is a single grep.

3. **TDD the fix.** Write an acceptance test that captures the bug (fails currently). Then write the minimum code to make it pass.
4. Run the full test suite to confirm no new regressions.
5. Append to `<feature-folder>/validation-log.md`:

```markdown
## Triage · <date>
**Reported:** <PM's words>
**Repro:** <how reproduced>
**Debug-log prefix:** <prefix declared in Step 2b, or "none">
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

---

## Tone discipline

Terse. Substance exact. Drop articles, filler ("just", "really", "basically"), pleasantries, hedging. Fragments OK if unambiguous. One sentence per update is enough.

**Carve-outs (do NOT compress):** code blocks, tool output, BLOCK/FLAG callouts, irreversible-action warnings, PM-facing approval prompts.

---

## Record routing — externalized artifact store

Per-feature **records** (brief / plan / validation-log / checkpoint / reports / mockup / brief-meta) route through the store adapter, not the feature folder directly: wherever a step says write/read `<feature-folder>/<file>`, use the store address `<repo-id>/<date-slug>/<file>` with in-repo fallback. Full read/write/fallback protocol: [`scripts/store/README.md`](../../scripts/store/README.md#record-routing-protocol-agent-facing). **Durable tier — `project-learnings.md`, `documentation-registry.md` — stays in-repo, never routed to the store.**
