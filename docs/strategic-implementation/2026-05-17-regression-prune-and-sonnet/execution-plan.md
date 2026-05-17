# Execution Plan: Regression-check prune + Sonnet for the tests reviewer

_Implements: [product-brief_regression-prune-and-sonnet.md](docs/strategic-implementation/2026-05-17-regression-prune-and-sonnet/product-brief_regression-prune-and-sonnet.md) · Date: 2026-05-17_

## Context

Plugin-internal markdown change. The product brief locks in two HARD-DECISIONs: only the `tests` reviewer downgrades to Sonnet; regression-check is pruned (not removed) to five surviving sections with auto-apply scoped to trivial fixes the skill already performs inline. No source code, no tests, no dependencies. Both deliverables edit a single file each.

## Library lifecycle audit

n/a — clarify declared `none`. No third-party runtimes, no browser/network behavior, no cross-component reactive state coordination. Edits are inert plugin definition files consumed by the Claude harness on next session load.

## Deliverables (DAG)

### D1 — `tests` reviewer model downgrade

- **Integration-risk class:** `d` (none of a/b/c; pure metadata change in plugin definition)
- **User-acceptance steps (from brief):**
  1. Start a feature cycle and approve a brief that produces an execution plan with several deliverables.
  2. When the review tier launches, watch the specialist verdicts come back: the validation-method reviewer returns visibly ahead of its sibling specialists.
  3. Read its output. The verdict still flags the same kinds of mismatches it used to — e.g., a deliverable that claims TDD validation but ships no tests, or a post-hoc claim that doesn't honor a brief's user-acceptance step — without any new false positives.
- **Validation method (chosen here):** `post-hoc`. Live-agent invocation in-session is unreliable per project learning L-005 (plugin cache drift — agents load from `~/.claude/plugins/cache/...`, not the working tree). The verifiable post-hoc check is grep-based on the working-tree file + a synthetic-plan reasoning walkthrough.
  - Step (a): `grep -n "^model: sonnet" plugins/strategic-implementation/agents/tests.md` → expect exactly one match in the frontmatter block (lines 1–4).
  - Step (b): read the file body and confirm prose semantics unchanged (no scope or output-schema edits). The downgrade is metadata-only.
  - Step (c): reasoning-walkthrough — given a synthetic plan with a TDD-claimed deliverable that mocks the dependency under test, confirm the `tests` agent's existing rule set still produces a FLAG. (Reasoning happens against the prose; the verdict's runtime correctness lands when the plugin reinstalls.)
  - **Deferred to post-restart (necessary-but-not-sufficient honesty note).** Acceptance step 2 ("returns visibly ahead of sibling specialists") is a runtime latency claim observable only on the next post-reinstall feature cycle — pre-restart, L-005 makes it unobservable. Acceptance step 3 ("no new false positives") is a behavioral claim about Sonnet's verdict quality; the reasoning-walkthrough confirms the *spec* still flags the synthetic case, but cannot prove Sonnet executes it equivalently to the prior model. Both observations are gated on the brief §3 success-signal verification (Wayne's next live cycle after plugin reinstall). The post-hoc evidence here covers only the metadata-correctness precondition.
- **Files:** `plugins/strategic-implementation/agents/tests.md` (verified present, 5.5K)
- **Steps:**
  1. Open `plugins/strategic-implementation/agents/tests.md`.
  2. Add a single line to the frontmatter immediately after `description:`: `model: sonnet`.
  3. Do NOT touch the body — scope, output schema, rule set all preserved.
- **Deps:** none.
- **Pre-flight env check:** none (text edit only).
- **may-invalidate:** none. (Registry does not track per-agent definition files; only skill SKILL.md files and the script/report telemetry are indexed.)
- **Visual contract:** n/a.
- **Consumer audit:** n/a — no shape change. The frontmatter `model` field is read by the Claude harness, not by any in-repo consumer.

### D2 — `regression-check` report prune + auto-apply

- **Integration-risk class:** `d` (markdown spec change consumed by an LLM at skill-invocation time).
- **User-acceptance steps (from brief):**
  1. Let a feature cycle run to completion; the orchestrator invokes regression-check automatically on the final deliverable.
  2. Open the report file in the feature folder. The body has at most five top-level sections — covering, in plain reader terms: which shared files this feature touched and what else might be affected; whether the artifacts a deliverable claimed to produce actually exist on disk (only when a deliverable was validated by claim-and-verify rather than a live test); a security review of any maintainer-tooling configuration touched (only when such files changed); a final simplicity-review pass; and an overall status line. The rest is either gone entirely or compressed to a single line.
  3. Look at the new "auto-applied" subsection. Trivial gaps (a stale registry row, a missing one-line cross-reference of the type the skill already handles inline) appear there with a brief note of what was fixed; the maintainer is not prompted to disposition them.
  4. Look at the status line. Only genuinely ambiguous findings — ones that require maintainer judgment — appear as FLAG or BLOCK items requiring disposition.
- **Validation method (chosen here):** `post-hoc`. Same L-005 reasoning — invoking the skill in-session loads the cached copy, not the working-tree copy. Verifiable post-hoc checks:
  - Step (a): structural grep on the rewritten SKILL.md:
    - `grep -c "^### Steps" plugins/strategic-implementation/skills/post-execution/SKILL.md` shows exactly one (regression-check Steps section; triage + learnings-synthesis retain their internal numbering but use their own headings).
    - `grep -n "^## Mode:" plugins/strategic-implementation/skills/post-execution/SKILL.md` shows exactly three modes preserved (`regression-check`, `triage`, `learnings-synthesis`).
    - Regression-check Steps section enumerates ≤ 6 numbered steps and produces a report template with ≤ 5 top-level `##` sections inside the regression-check block.
  - Step (b): inspect the regression-check report template embedded in SKILL.md — confirm the surviving sections are exactly: dependent-file impact (cross-contamination), goal-backward (gated), plugin-config security scan (gated), simplify final pass, status. Confirm DROPPED sections are absent: modified-files inventory, acceptance-tests-authored, visual-diff. Confirm COMPRESSED items appear as one-liners in the status block: test-suite exit code, registry sanity.
  - Step (c): confirm the new "Auto-applied" subsection of the status section exists, with explicit scoping language matching the brief's HARD DECISION — applies only to stale registry rows and missing one-line cross-references; does NOT apply to simplify findings, test failures, or source code.
  - Step (d): preserved-intact diff check — the `## Mode: triage` and `## Mode: learnings-synthesis` blocks are byte-identical (or only whitespace/cross-reference adjusted) compared to the pre-edit file. Confirmed by reading them post-edit.
  - Step (e): dry-run reasoning — pick **two** historical feature folders under `/Users/qiangliu/Documents/Development/axiph/docs/strategic-implementation/`: one with a real regression-check catch (e.g., `2026-05-12-schema-source-of-truth` — caught a stale registry row), and one with no genuine catch (e.g., `2026-05-07-shared-types-auto-build` — clean PASS). Mentally walk the rewritten Steps against each `validation-log.md` and post-execution-report.md. Record both walkthroughs in this feature's `validation-log.md` with one line each: (i) "would the pruned flow still surface this catch?" (must be yes for the catch case), (ii) "would the pruned report be shorter than the historical one?" (must be yes for the no-catch case).
  - **Deferred to post-restart (honesty note).** Acceptance step 4 ("only genuinely ambiguous findings appear as FLAG/BLOCK") rests partly on the dry-run reasoning here and partly on live observation in the next post-reinstall feature cycle. The post-hoc evidence demonstrates the spec produces the right report shape and routes auto-apply correctly; the lived experience of "I was not nagged on trivia" surfaces on the next cycle (brief §3 success-signal).
- **Files:** `plugins/strategic-implementation/skills/post-execution/SKILL.md` (verified present, 13.1K).
- **Steps:**
  1. Read the current file. Identify three blocks: `## Mode: regression-check` (lines 18–117 approx), `## Mode: triage` (lines 119–158 approx), `## Mode: learnings-synthesis` (lines 161–180 approx), and `## Cross-mode rules` + `## Tone discipline` (lines 183–195). Triage, learnings-synthesis, cross-mode rules, and tone discipline are preserved intact.
  2. Rewrite ONLY the `## Mode: regression-check` block. The new block has:
     - The same plan-mode entry-check line at the top.
     - The same trigger sentence ("Triggered automatically by `executing-plans` when the final deliverable is marked complete.").
     - A new ≤6-step Steps section in this order:
       1. **Discover modified file set + cross-contamination scan.** Union of execution-plan files and `git diff --name-only`; for each, grep the rest of the repo for imports/references and flag dependents whose tests should be rerun. (Folds the old Step 1 modified-files discovery into the cross-contamination step — the file list is no longer a standalone report section, only an input to dependent analysis.)
       2. **Plugin-config security scan (gated).** Skip with one line "no plugin-config files touched" if no `.claude/` path was modified. Otherwise run the same five-rule category scan as today (Secrets / Permissions audit / Hook injection / MCP risk / Agent config review) with the same severity gating. _(Preserve the rule body verbatim from the current file's Step 2a — same regexes, same exclusion list, same gating.)_
       3. **Goal-backward verification (gated).** Skip with one line if no deliverable has `Validation: post-hoc` and no `FLAG (mocked-seam)` entry in `validation-log.md`. Otherwise run the same first-3-matches walkthrough as today (read expected outcome from execution-plan; one grep per artifact; yes/no per artifact; any `no` → BLOCK).
       4. **Registry-update verification + small-cross-reference auto-apply.** Load `docs/strategic-implementation/documentation-registry.md` if present. For each `may-invalidate` entry, check whether `Last Updated` advanced past feature-start. **Two auto-apply classes are in scope here, matching the brief's HARD DECISION:**
        - **(i) Stale registry rows.** For each stale row where the doc itself was edited in the feature commits OR the row's `may-invalidate` target is plumbed by a deliverable that demonstrably ran → bump `Last Updated` to today, append one line to the report under "Auto-applied:" naming the row.
        - **(ii) Missing one-line cross-references.** If a deliverable's `may-invalidate` declared a doc that should now cross-reference a new artifact (e.g., a new module path or section header), and the registry row was bumped but the doc itself is missing that one-line backlink → insert the one-line backlink at the relevant section heading and note it under "Auto-applied:".
        - For ambiguous cases (doc not edited; `may-invalidate` target unclear; cross-reference location not obvious) → escalate as FLAG, do not auto-apply.
       5. **Final simplify pass (mandatory).** Invoke `strategic-implementation:simplify` against `git diff <merge-base>...HEAD`. Capture report path and high/med/low counts. Disposition handling unchanged from current behavior.
       6. **Write report + telemetry.** Write `<feature-folder>/post-execution-report.md` per the pruned template below. Then run `bash plugins/strategic-implementation/scripts/token-report.sh "<feature-folder>"` and verify `token-report.md` landed (script is source of truth; never read its contents).
     - A pruned report template (replace lines 67–106 of the current file) containing exactly these top-level sections, **in the brief's reader-facing order** — cross-contamination → goal-backward → plugin-config → simplify → status:
       ```
       # Post-execution report
       _Date: <date> · Feature: <slug>_

       ## Cross-contamination
       <dependents examined; regressions flagged. Brief modified-files context inline (filename + deliverable annotation) — no separate inventory section.>

       ## Goal-backward verification
       <one block per matched deliverable, or "skipped — no post-hoc or mocked-seam matches">

       ## Plugin config security scan
       <bulleted findings, or "no plugin-config files touched" / "no findings">

       ## Simplify final pass
       - Report: `<simplify-report-path>`
       - Findings: <total> (high: <h>, med: <m>, low: <l>)
       - Disposition: <all-filled | <n> unfilled — FLAG>

       ## Status
       <PASS / FLAG / BLOCK — gating same as today.>
       - Test suite: <one-liner observed from `validation-log.md` — "green per validation-log" | "<n> regressions logged — FLAG" | "n/a — no executable test surface". Reads from the feature's existing validation-log, not from an executing-plans handoff.>
       - Registry: <"all current" | "auto-applied: <n> row(s)" | "<n> stale — FLAG">
       - Auto-applied (this run): <bulleted list of fixes the regression-check made without prompting, or "none">
       ```
     - Removed entirely: `## Modified files`, `## Test suite run` (as a section — moved to a Status one-liner), `## Acceptance tests authored`, `## Registry-update verification` (as a section — moved to Status one-liner + Auto-applied), `## Visual diff` (and the entire visual-contract prompt step).
  3. The current file's closing announcement (Step 9: "If any regression is unresolved or any goal-backward verification returns `no`: surface to PM. Otherwise announce completion.") is preserved verbatim as a closing line after the new Steps block — same BLOCK-surfacing language, no rewording. This is the one piece of regression-check behavior the maintainer relies on for hard-stops and must not drift.
  4. Confirm `## Mode: triage`, `## Mode: learnings-synthesis`, `## Cross-mode rules`, `## Tone discipline` blocks are byte-equivalent to before (no incidental edits).
- **Deps:** none (independent of D1).
- **Pre-flight env check:** none.
- **may-invalidate:** `[plugins/strategic-implementation/skills/post-execution/SKILL.md]` — but this file is not in the documentation-registry today, so no registry row to update. Confirmed by reading the registry above.
- **Visual contract:** n/a.
- **Consumer audit:** n/a — no shape change. The SKILL.md is consumed by an LLM reading the spec; no in-repo code imports it.

## Parallel groups & order

D1 and D2 are independent — different files, no shared content. They can be authored in parallel and committed as two atomic commits in either order. Default sequential order: D1 first (single-line change, fast), then D2 (substantive rewrite).

## Reused existing patterns

- **Auto-apply pattern for registry rows.** The current `## Mode: regression-check` Step 6 already prompts the maintainer ("Update the doc now? (y/n/skip)") on stale entries; D2 narrows this to silent auto-apply for the unambiguous subclass (doc demonstrably edited during the feature) while preserving the prompt path for genuinely ambiguous cases. Same primitive, narrower trigger.
- **Gated section pattern.** The plugin-config security scan in the current file (Step 2a) already short-circuits with a one-line "no plugin-config files touched" when no `.claude/` path was modified. D2 extends this gated-skip primitive to goal-backward verification.
- **Frontmatter `model` field.** Frozen-leakage reviewer inside `product-brief-drafter/SKILL.md:110` already uses `model: "sonnet"` for inline `Agent` invocation. D1 applies the same field at the standalone-agent-file altitude.

## Risks & contingencies

- **Plugin cache drift (project learning L-005).** Working-tree edits to `plugins/strategic-implementation/agents/tests.md` and `plugins/strategic-implementation/skills/post-execution/SKILL.md` are NOT visible to in-session agent invocations. Validation methods chosen accordingly (`post-hoc` grep + reasoning). The success-signal verification in the brief explicitly requires Wayne to restart the session after the upstream plugin update lands — already noted in brief §6 risks.
- **Pruned section loses a low-frequency catch we didn't see in 24 reports.** Mitigation per brief: each dropped section is justified against the audit; restoration is a one-section markdown edit if a missed catch surfaces.
- **Auto-apply masks a fix that should have been escalated.** Mitigation per brief: every auto-applied fix appears in the `Auto-applied:` bullet list of the Status section; nothing happens silently. The maintainer scans it on each cycle.
- **Sonnet false-negative rate on validation-method review unmeasured.** Mitigation: if quality drops on the next cycle, revert by removing the `model: sonnet` frontmatter line. Single-line reverse.

## Out of scope for this plan

- Any other reviewer agent's model assignment.
- The triage and learnings-synthesis modes of post-execution.
- The `executing-plans` skill and the `strategic-implementation` orchestrator.
- The `review` skill.
- New telemetry, new metrics, new dependencies.
- Adjustments to the project-learnings file or the documentation-registry schema.

## Final steps on approval

1. Save execution plan → `/Users/qiangliu/Documents/Development/claude-skills/docs/strategic-implementation/2026-05-17-regression-prune-and-sonnet/execution-plan.md`
2. Exit plan mode
3. Invoke `strategic-implementation:executing-plans`
   - Execution plan path: `docs/strategic-implementation/2026-05-17-regression-prune-and-sonnet/execution-plan.md`
   - Feature folder path: `docs/strategic-implementation/2026-05-17-regression-prune-and-sonnet/`
   - Autonomy level: auto
