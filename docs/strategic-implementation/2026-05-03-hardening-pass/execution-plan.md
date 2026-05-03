# Execution Plan: Hardening Pass — Five Rules
_Implements: product-brief_hardening-pass.md · Date: 2026-05-03 · Revised after review v2_

## Context

The strategic-implementation plugin currently has no security gate, no diagnostic discipline for triage, no runtime guardrails against rework loops, and a tests reviewer that does not flag mock-at-internal-collaborator anti-patterns. Three external skill repos (mattpocock/skills, affaan-m/everything-claude-code, millionco/claude-doctor) supplied research-validated patterns that close these gaps at <1% session-token overhead. This plan imports the five highest impact-per-token patterns into our skill bodies, with all attribution consolidated in the plugin README. Brief working-backwards and success-signal remain TBD per PM direction.

This is the **revision-2** plan: the original v1 had six deliverables and inline per-site attribution comments; review (alignment + simplify + tests + boundaries) converged on collapsing to four deliverables, dropping inline comments in favor of a single README acknowledgments section, using lettered substeps to avoid renumbering, declaring honest validation methods (mostly `post-hoc` for prose changes, `cli` for the one mock-placement fixture), and incorporating boundaries' security-pattern improvements.

## Library lifecycle audit

_None — clarify declared no integration-risk dependencies. AgentShield's npm runtime is a non-goal (HARD DECISION); rule patterns are inlined as prose._

## Deliverables (DAG)

### D1 — Inlined plugin-config security scan in `post-execution:regression-check`  ✅ complete
- **Source:** `affaan-m/everything-claude-code` AgentShield (commit `841beea`).
- **Integration-risk class:** `d`.
- **Validation:** `post-hoc` — PM diff-reads the new Step 2a in `post-execution/SKILL.md`; checks the five rule categories, severity gating, and the inserted `## Plugin config security scan` report block. Behavioral end-to-end (regression-check BLOCK on a real poisoned hook) is deferred to first real use.
- **Files:** `plugins/strategic-implementation/skills/post-execution/SKILL.md` (regression-check section).
- **Steps:**
  1. Insert a new lettered substep **Step 2a** in regression-check, between current Step 2 (cross-contamination check) and Step 3 (test-suite run), titled "Plugin config security scan." No renumbering of subsequent steps.
  2. Body of Step 2a: gate on whether the modified-file set includes any path under `.claude/` (settings, hooks, MCP, agent configs). If no `.claude/` path was modified, skip with the line "no plugin-config files touched."
  3. If `.claude/` files were modified, run inlined static checks across **five rule categories**. Apply a placeholder/env-ref exclusion list (`<.*>`, `\$\{?[A-Z_]+\}?`, `placeholder`, `example`, `your-.*-here`, `xxx+`) before any Critical-tier escalation; matches against the exclusion list demote to Medium.
     - **Secrets** — patterns: generic `[A-Z0-9_]*API_KEY\s*[:=]\s*["'][A-Za-z0-9_-]{16,}` (Critical only if not excluded; else Medium); `sk-[A-Za-z0-9]{20,}` (OpenAI, Critical); `Bearer\s+[A-Za-z0-9._-]{20,}` (Critical); `xox[baprs]-[A-Za-z0-9-]{10,}` (Slack, Critical); `AKIA[0-9A-Z]{16}` (AWS, Critical); `gh[pousr]_[A-Za-z0-9]{30,}` (GitHub, Critical); `-----BEGIN [A-Z ]*PRIVATE KEY-----` (PEM, Critical). Scan in `settings.json`, `mcp.json`, hook scripts, agent configs.
     - **Permissions audit** — `Bash\(\*\)` in `allow` array (High); missing `deny` block when `allow` is broad (High); presence of `--no-verify` or `--dangerously-skip-permissions` flags (High).
     - **Hook injection** — `eval ` in hook commands (Critical); backtick command substitution (Critical); `\$\([^)]*\$[A-Z_]` nested-`$()`-with-var (Critical); `curl[^|]*\|\s*sh` pipe-to-shell (Critical); silent error suppression `2>/dev/null` or `\|\| true` (Medium/log only — common in legitimate probe checks; quote-context analysis is a known grep limitation, reserved for behavioral validation).
     - **MCP risk profile** — `npx -y` in MCP server commands (Medium/log; documented install pattern); `npx -y` combined with unpinned package version or non-registry source (High); hardcoded env values matching key-shapes (High); shell-running MCP servers (High).
     - **Agent config review** — agent definitions with no model spec (Medium/log); unrestricted tool access shape (Medium/log).
  4. **Severity gating:** Critical → Status `BLOCK` (sets the regression-check status line to BLOCK and halts post-execution sign-off until resolved); High → Status `FLAG`; Medium/log-only → log to report only, no status change.
  5. Append findings to `post-execution-report.md` under new heading `## Plugin config security scan` with one bullet per finding: severity, rule, file, line, snippet (≤80 chars). If no `.claude/` files modified or no findings, write a one-line "no findings."
  6. Update the `## Status` line in the report template to mention `Plugin config: <PASS | FLAG | BLOCK>` alongside existing status drivers.
  7. **No inline attribution comments in the SKILL prose** — provenance lives in the README (D4).
- **Deps:** none.
- **Pre-flight env check:** `grep` available; access to `plugins/strategic-implementation/skills/post-execution/SKILL.md`.
- **may-invalidate:** none.
- **Visual contract:** n/a.
- **Consumer audit:** `post-execution-report.md` schema gains a new `## Plugin config security scan` section and a new field in the `## Status` line. The report is human-read by the PM (no machine consumer). `unaffected-because-no-machine-consumer-of-report-schema`.

### D2 — Executing-plans Step 2b hardening + tests reviewer mock-placement  ✅ complete (cli validation deferred to post-D4 plugin reinstall — see DEV-002)
- **Source:** `mattpocock/skills` @ `b843cb5` (TDD vertical-slice + mocking.md); `millionco/claude-doctor` @ `f5efb2a` (edit-thrashing + error-loop signals).
- **Integration-risk class:** `d`.
- **Validation:** `cli` — synthetic-plan fixture exercises the new `mock-placement` rule. Create `docs/strategic-implementation/2026-05-03-hardening-pass/fixtures/synthetic-plan-with-internal-mock.md` containing a one-deliverable plan that declares `tdd` validation and explicitly mocks an internal collaborator (e.g., a helper function in the same module). Run the `tests` reviewer agent against this fixture (via the same Skill/Agent invocation pattern reviewers normally use). Assert the agent's JSON output contains a flag with `dimension: "mock-placement"` and severity `high`. Prose additions (rework guardrails, TDD vertical-slice rule) are observed in the same commit's diff as the mock-placement rule lands; the cli fixture is the proof-point that any new rule wording is structurally correct.
- **Files:**
  - `plugins/strategic-implementation/skills/executing-plans/SKILL.md` (Step 2b Build, plus Failure Protocol, plus Deviation logging type list).
  - `plugins/strategic-implementation/agents/tests.md` (Scope section, new rule item; Output schema enum extension).
  - `docs/strategic-implementation/2026-05-03-hardening-pass/fixtures/synthetic-plan-with-internal-mock.md` (new fixture file).
- **Steps:**
  1. **Executing-plans Step 2b — TDD vertical-slice rule (mattpocock).** Expand the existing `**TDD where declared.**` bullet into:
     - "**TDD where declared (vertical-slice tracer-bullet rule):** when validation is `tdd`, write ONE failing test for the next thinnest slice of user-observable behavior, make it pass, commit-or-stage, then move to the next slice. Do **not** write all tests first then all implementation — that produces tests of imagined behavior and the shape of things, not user-facing behavior. The horizontal-slice anti-pattern (test-batch then code-batch) is rejected."
  2. **Executing-plans Step 2b — Rework guardrails block (claude-doctor).** After the existing "Code discipline" bullet block, insert a new bullet block titled "**Rework guardrails (per-deliverable counters):**"
     - "**Edit-thrashing:** track Edit/Write tool calls per file within the current deliverable. On the 4th edit to the same file (>3 edits), pause: re-read the brief and the deliverable's plan block before any further Edit/Write to that file. Log a `thrash-pause` deviation. In `auto`, decide and proceed; in `supervised`, surface and pause."
     - "**Error-loop:** track consecutive tool failures. On the 3rd consecutive failure of any tool call within the current deliverable without a strategy change, do not retry. Escalate to `post-execution:triage` with the error trace as the reported issue. Log an `error-loop-escalation` deviation."
  3. **Executing-plans Failure Protocol.** In the Attempt-2 block, add the precondition: "If error-loop has already triggered (3+ consecutive failures), do NOT attempt Attempt 2 — proceed directly to EXIT and Exit Report."
  4. **Executing-plans Deviation logging.** Extend the deviation type list to include `thrash-pause` and `error-loop-escalation` alongside the existing types.
  5. **agents/tests.md Scope — new rule item (mattpocock mocking.md).** Insert a new numbered Scope item after the current item 2 (Validation honesty at integration-risk seams), titled "**Mock placement (HIGH).**" Body:
     - "Mocks are allowed only at system boundaries (third-party SDKs, network, file system, OS). Mocks of internal collaborators (helpers, factories, services within the same module/package) are a HIGH-severity FLAG. Required wording shape: 'D<n> mocks internal collaborator `<name>` — internal collaborators must be exercised, not stubbed. Move the mock to the system boundary or remove it.' A test suite that mocks its own callees proves nothing about integration."
  6. **agents/tests.md — renumber subsequent Scope items** (current 3 → 4, ..., 8 → 9). This is the one renumber the plan accepts; it is contained to a single agent file and the items are not cross-referenced from outside the file.
  7. **agents/tests.md Output schema.** Extend the `dimension` enum from `method|honesty|coverage|fragility|regression` to `method|honesty|coverage|fragility|regression|mock-placement`.
  8. **Author the synthetic fixture.** Create `docs/strategic-implementation/2026-05-03-hardening-pass/fixtures/synthetic-plan-with-internal-mock.md` — a minimal one-deliverable plan declaring `tdd` validation and explicitly mocking an internal helper. Include a comment header noting it is a test fixture for D2 validation, not a real plan.
  9. **No inline attribution comments** in any of the three edited files. Provenance lives in the README (D4).
- **Deps:** none.
- **Pre-flight env check:** access to `executing-plans/SKILL.md`, `agents/tests.md`; ability to invoke the `tests` agent against a fixture.
- **may-invalidate:** none.
- **Visual contract:** n/a.
- **Consumer audit:**
  - `dimension` enum in `agents/tests.md` Output schema → consumers verified at plan-approval time: `grep -rn 'dimension' plugins/strategic-implementation/skills/review/ plugins/strategic-implementation/agents/alignment.md` confirms no switch/case on enum values; `dimension` appears only as a prose word in review SKILL description and as a JSON output field in alignment (emitted, not consumed). **Status: `unaffected-because-not-parsed-as-enum-only-emitted`.**
  - Deviation type strings (`thrash-pause`, `error-loop-escalation`) — `unaffected-because-deviation-types-are-narrative-prose-not-parsed-as-enum`. Note: deviation-type vocabulary is now load-bearing for `learnings-synthesis` prose pattern-matching only; if a future skill ever switches on this enum, both D2 and D3 (which adds spec-ambiguity-* types) silently regress together.

### D3 — Triage rewrite: spec-ambiguity check + Phase-1 deterministic-repro discipline  ✅ complete
- **Source:** `mattpocock/skills` @ `b843cb5` (`diagnose` Phase-1); `millionco/claude-doctor` @ `f5efb2a` (repeated-instructions).
- **Integration-risk class:** `d`.
- **Validation:** `post-hoc` — PM diff-reads the rewritten triage section in `post-execution/SKILL.md`; checks that Step 1.5 (spec-ambiguity) precedes the rewritten Step 2 (deterministic repro), 3-5 ranked falsifiable hypotheses are required, and debug-log prefix tagging is declared.
- **Files:**
  - `plugins/strategic-implementation/skills/post-execution/SKILL.md` (triage section).
  - `plugins/strategic-implementation/skills/executing-plans/SKILL.md` (deviation type list — adds `spec-ambiguity-redirect`, `spec-ambiguity-override`).
- **Steps:**
  1. **Insert Step 1.5 — Specification-ambiguity check (claude-doctor).** Between current triage Step 1 (read PM report) and the rewritten Step 2 (deterministic repro). Body: scan the last 5 PM messages in the current session. If any pair shows ≥60% phrase-overlap (agent-eyeballed — substantive nouns and verbs repeated, not just function words), the issue is likely specification ambiguity, not a code defect. On detection: do **not** proceed to repro. Instead, surface to PM: "Detected repeated/paraphrased instruction in last 5 turns — `<paraphrase A>` vs `<paraphrase B>`. This pattern usually indicates the brief or plan is ambiguous. Recommend invoking `product-brief-drafter:revise` rather than attempting another fix. Proceed to repro anyway? (y/N)" Default N. On N: route to brief revision via the orchestrator. Log a `spec-ambiguity-redirect` deviation. On y: proceed to Step 2; log `spec-ambiguity-override`.
  2. **Replace triage Step 2 (mattpocock diagnose).** Replace the current one-line "Reproduce. Use the validation method from the relevant deliverable to confirm." with a new Step 2 titled "Build deterministic repro **before** hypothesizing." Body: prohibit proposing fixes until a fast, deterministic, agent-runnable signal exists that distinguishes "broken" from "fixed." If one cannot be built, log a `repro-blocked` deviation and surface to PM rather than dive into code. List the repro-construction ladder in order of preference: failing test → curl/CLI snapshot diff → headless browser script → trace replay → throwaway harness → bisect harness → differential vs. last-known-good. Stop at the first rung that yields a deterministic pass/fail.
  3. **Insert Step 2a — Generate ranked hypotheses.** Require 3-5 falsifiable hypotheses, ranked by expected explanatory power, each with one-line falsification cost. Forbid fix attempts on hypotheses below rank 3 until top-3 are ruled out.
  4. **Insert Step 2b — Tag debug logs for cleanup.** Any debug print/log added during diagnosis carries a unique prefix declared up front (e.g. `[DBG-D<n>-<short-uuid>]`). The Triage block in Step 5 (validation-log entry) records the prefix so cleanup is a single grep/remove.
  5. **Update the validation-log Triage entry template** to add a `**Debug-log prefix:**` line.
  6. **Add `repro-blocked`, `spec-ambiguity-redirect`, `spec-ambiguity-override` to the deviation type list** in `executing-plans/SKILL.md` (alongside D2's `thrash-pause` and `error-loop-escalation`). Single edit pass on the deviation list.
  7. **No inline attribution comments.** README is the single source of provenance.
- **Deps:** D1 (same file `post-execution/SKILL.md`, different sections — sequenced to keep edits linear and reduce merge risk); D2 (same deviation type list extension in `executing-plans/SKILL.md` — sequenced to extend the same list once-per-deliverable rather than collide).
- **Pre-flight env check:** D1 + D2 committed.
- **may-invalidate:** none.
- **Visual contract:** n/a.
- **Consumer audit:** triage validation-log Triage entry gains a new `**Debug-log prefix:**` field — additive, parsed only by `learnings-synthesis` summarizer (no enum). `unaffected-because-additive-prose-field`. Deviation type additions (`repro-blocked`, `spec-ambiguity-redirect`, `spec-ambiguity-override`) — same posture as D2's deviation additions: `unaffected-because-deviation-types-are-narrative-prose-not-parsed-as-enum`.

### D4 — README attribution + version bump  ✅ complete
- **Integration-risk class:** `d`.
- **Validation:** `post-hoc` — PM diff-reads README new Acknowledgments section and `package.json` version field.
- **Files:**
  - `plugins/strategic-implementation/README.md` (extend existing Acknowledgments block at line ~202; add sibling section for v3.1; update top-of-README `**Version:**` line).
  - `plugins/strategic-implementation/package.json` (version `3.0.0` → `3.1.0`).
- **Steps:**
  1. Below the existing `## Acknowledgments — inspirations for v2.2` section in README, add a new sibling section `## Acknowledgments — inspirations for v3.1 (Hardening Pass)`.
  2. Three bullets, one per source repo, each naming the technique imported, the file mirrored, the commit hash, and the deliverable it landed in:
     - `[mattpocock/skills](https://github.com/mattpocock/skills) @ b843cb5` — `diagnose` Phase-1 feedback-loop discipline (D3 in `post-execution:triage`); `tdd` vertical-slice tracer-bullet rule and `mocking.md` mock-at-system-boundaries rule (D2 in `executing-plans` Step 2b and `agents/tests.md` Scope item 3).
     - `[affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) @ 841beea` — AgentShield static-config-scan rule patterns (D1 in `post-execution:regression-check` Step 2a). Patterns are inlined (no `npx` runtime); upstream maintains 102 rules with auto-fix mode.
     - `[millionco/claude-doctor](https://github.com/millionco/claude-doctor) @ f5efb2a` — edit-thrashing and error-loop signals (D2 in `executing-plans` Step 2b); repeated-instructions detection (D3 in `post-execution:triage` Step 1.5).
  3. **De-facto-policy note.** One-paragraph closing note: "The inlined AgentShield rule patterns in D1 are the plugin's de-facto plugin-config security policy as of v3.1 — the brief declared no security policy doc upstream of this work, and the rule wording shipped here is authoritative-by-default. Future PMs editing security-sensitive plugin config should treat these patterns as the contract until a project-level security policy supersedes them."
  4. Closing paragraph mirroring the v2.2 acknowledgments tone: lean choice to inline patterns rather than depend on external tooling; thanks to the projects.
  5. Update the `**Version:** 3.0.0` line near the top of README to `**Version:** 3.1.0`.
  6. Update `package.json` field `"version"` from `"3.0.0"` to `"3.1.0"`.
  7. The existing `Skills (9) and agents (7)` heading in README is unchanged — no new skills or agents added in this feature, only edits to existing ones.
- **Deps:** D1, D2, D3 — all three must be complete so the Acknowledgments rows accurately reflect what shipped.
- **Pre-flight env check:** D1, D2, D3 all committed.
- **may-invalidate:** `docs/strategic-implementation/documentation-registry.md` is not invalidated (the registry's `Owning Area` for the brief row is `strategic-implementation`; this feature does not touch tracked docs other than its own brief).
- **Visual contract:** n/a.
- **Consumer audit:** `package.json` `"version"` field is shape-stable (string semver). README is human-read.

## Parallel groups & order

```
D1 (post-exec regression-check Step 2a)  ─┐
D2 (executing-plans 2b + tests.md 3 + fixture) ─┤  parallel group A
                                           │
D3 (post-exec triage rewrite + dev list)  ◀── after D1 (same SKILL.md, different section) AND after D2 (shared deviation list edit in executing-plans)
                                           │
D4 (README + version)                     ◀── after D1, D2, D3
```

D1 and D2 in parallel. D3 sequenced after both (touches the same `post-execution/SKILL.md` as D1 and the same deviation list in `executing-plans/SKILL.md` as D2). D4 last.

## Reused existing patterns

- **Lettered substep pattern** (Step 2a, Step 2.5, Step 1.5) already used in `post-execution/SKILL.md` and `executing-plans/SKILL.md` — D1 and D3 use it instead of renumbering. The single allowed renumber is contained to `agents/tests.md` Scope items in D2, where items are not cross-referenced from outside the file.
- **Existing Deviation type list in `executing-plans/SKILL.md`** — D2 and D3 extend rather than parallel-define; combined enum gains `thrash-pause`, `error-loop-escalation`, `repro-blocked`, `spec-ambiguity-redirect`, `spec-ambiguity-override`.
- **Existing `## Acknowledgments — inspirations for v2.2` section** in README — D4 adds a sibling v3.1 section, preserving v2.2 attribution intact.
- **Severity vocabulary (HIGH / FLAG / BLOCK)** — D1 and D2 reuse verbatim.
- **Output JSON schema in `agents/tests.md`** — D2 extends the `dimension` enum rather than inventing a parallel field.
- **Test fixture pattern** — placing the synthetic plan fixture under `docs/strategic-implementation/2026-05-03-hardening-pass/fixtures/` mirrors how feature-folder artifacts (briefs, plans, validation logs) live alongside execution.

## Risks & contingencies

- **Same-file edit collisions.** D1 and D3 both touch `post-execution/SKILL.md`. D2 and D3 both touch the deviation type list in `executing-plans/SKILL.md`. The DAG sequences edits linearly. Contingency: post-execution regression-check's cross-contamination scan (now augmented by D1's plugin-config scan) catches accidental drift.
- **Validation honesty residual risk.** D1, D3, D4 are honestly `post-hoc`; D2 has a real cli fixture. The fixture-based cli for D2 proves the `mock-placement` rule structurally; the `tests` agent invocation is non-deterministic in wording but deterministic in JSON-shape (the `dimension: "mock-placement"` flag must appear). If the `tests` agent fails to flag on the fixture, D2 fails and is re-worked.
- **Skill-prose surface area.** Brief flagged this; alignment confirmed. `post-execution:triage` doubles in size (D3 adds Step 1.5, rewrites Step 2, adds Steps 2a + 2b). At end of D3 execution, if the rewritten triage section exceeds 250 lines, surface to PM whether to compress further or ship as-is. Same for `executing-plans` Step 2b after D2 and D3 land their deviation-list extensions.
- **Renumbering risk in `agents/tests.md`.** D2 step 6 renumbers Scope items 3-9. Risk: the rest of the plugin references those numbers. Mitigation: at execution time, `grep -rn 'Scope.*item\|tests\.md.*item\|tests Scope' plugins/strategic-implementation/` before committing. If references found, update them in the same atomic commit.
- **TBD outcome (working-backwards / success-signal in brief).** PM accepted brief without filling these in and explicitly elected to ship as TBD. Plan does not pin an interim anchor. Post-execution regression-check and learnings-synthesis will operate without an outcome anchor; this is intentional and PM-acknowledged.
- **Inlined-rules drift.** D1's regex patterns mirror upstream AgentShield as of commit `841beea`. Upstream evolves; ours will not. README v3.1 acknowledgments state this explicitly; future maintainers refresh at their discretion.
- **Plugin-cache drift.** Source-of-truth edits land in working repo (`plugins/strategic-implementation/`); the user's running cache at `~/.claude/plugins/cache/wayneliuq/strategic-implementation/3.0.0/` is stale until plugin reinstall. This is expected; the user knows.
- **Deviation-type vocabulary load-bearing risk** (alignment low-severity flag, accepted). The deviation-type vocabulary is now load-bearing for `learnings-synthesis` prose pattern-matching only. If any future skill ever switches on this enum, D2 + D3 silently regress together. Documented in this risks block; no further mitigation this round.

## Out of scope for this plan

- Full `npx ecc-agentshield` external dependency (HARD DECISION — inline only).
- AgentShield's optional `--opus` red-team multi-agent deep scan.
- claude-doctor cross-session signals (restart-cluster, sentiment, abandonment, negative-drift).
- mattpocock's `CONTEXT.md` + ADR persistent-domain-language convention.
- Confidence scoring + auto-promotion in `learnings-synthesis` from continuous-learning-v2.
- Any `PreToolUse`/`PostToolUse` hooks or daemon (no background instrumentation).
- Migration tooling for users on v3.0.0 (changes are additive; no migration needed).
- Behavioral end-to-end test harness for D1 and D3 (covered by first-real-use; not a fixture). D2 has a single targeted fixture for the mock-placement rule only.
- Inline per-site attribution comments in skill prose (rejected by simplify; consolidated in README D4).
- Quote-context-aware static analysis (a known grep limitation; reserved for behavioral validation in future work).
- Project-level security policy doc upstream of D1's inlined rules (D4 acknowledges D1's rules as de-facto policy; project policy is separate work).

---

Final steps on approval:
1. Save execution plan → `docs/strategic-implementation/2026-05-03-hardening-pass/execution-plan.md`
2. Exit plan mode
3. Invoke `strategic-implementation:executing-plans`
   - Execution plan path: `docs/strategic-implementation/2026-05-03-hardening-pass/execution-plan.md`
   - Feature folder path: `docs/strategic-implementation/2026-05-03-hardening-pass/`
   - Autonomy level: auto
