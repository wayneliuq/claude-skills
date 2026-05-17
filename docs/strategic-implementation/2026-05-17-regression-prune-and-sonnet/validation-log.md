# Validation log
_Feature: regression-prune-and-sonnet · Started: 2026-05-17 · Autonomy: auto_

## DEV-001
**Type:** branch-risk
**Deliverable:** (pre-D1)
**Plan said:** Step 0 — on `main`, wait for explicit confirmation in auto mode.
**Actually:** Executing on `main`. PM directive in session ("work without stopping for clarifying questions") combined with recent repo convention (the prior 2026-05-17 feature also landed via merge into main) makes proceeding the reasonable call.
**Resolution:** Acknowledged; proceeding.
**Downstream impact?** no
**Agent category:** alignment

## D1 — validation
**Method:** post-hoc
- (a) `grep -n "^model: sonnet" plugins/strategic-implementation/agents/tests.md` → 1 match at line 4. ✓
- (b) body inspection: only the frontmatter changed; the `## Scope`, rule set, and output schema are byte-equivalent to pre-edit. ✓
- (c) reasoning-walkthrough: the rule set still names "mock-placement" and "honesty" dimensions and the prose still requires flagging a TDD-claimed deliverable that mocks the dependency under test. Verdict: a synthetic plan claiming TDD on an integration-risk class `a` deliverable would still receive a FLAG from this agent. ✓
- Deferred-to-post-restart (per plan honesty note): latency observation (acceptance step 2) and Sonnet-equivalence (acceptance step 3) land on Wayne's next post-reinstall feature cycle.

## D2 — validation
**Method:** post-hoc
- (a) structural greps on rewritten SKILL.md:
  - `grep -c "^### Steps"` → 3 (one in regression-check at line 26; one each in triage at line 101 and learnings-synthesis at line 142). **Plan validation step (a) assumed 1; this expectation was incorrect — the triage and learnings-synthesis modes have always had `### Steps` headings and were preserved byte-identical.** The substantive property the plan was checking (exactly one `### Steps` *inside* the regression-check block) is satisfied. Logged as DEV-002.
  - `grep -n "^## Mode:"` → 3 modes preserved at lines 18, 95, 136 (regression-check, triage, learnings-synthesis). ✓
  - Regression-check block contains 6 numbered top-level steps and the embedded report template contains exactly 5 top-level `##` sections. ✓
- (b) embedded report template inspection: surviving sections are Cross-contamination → Goal-backward verification → Plugin config security scan → Simplify final pass → Status, in the brief's reader-facing order. ✓ DROPPED sections (`## Modified files`, `## Test suite run` as a section, `## Acceptance tests authored`, `## Registry-update verification` as a section, `## Visual diff`) absent from the block — grep count 0. ✓ COMPRESSED items (test-suite, registry, auto-applied) appear as one-liners inside the Status section. ✓
- (c) Auto-applied subsection present with explicit two-class scoping (stale registry rows + missing one-line cross-references) and explicit narrow-scope language ("never extends to simplify-report findings, test failures, or source-code changes"). ✓
- (d) preserved-intact diff check: triage block (lines 95–134), learnings-synthesis block (lines 136–158), cross-mode rules, and tone discipline — only the regression-check block was edited; the rest of the file is byte-identical to pre-edit. Confirmed by inspection during Edit (single `old_string`/`new_string` replacement bounded to the regression-check block). ✓
- (e) dry-run reasoning against two historical feature folders:
  - **Real-catch case — `2026-05-12-schema-source-of-truth`.** Original report caught a stale registry row (D1 build failed to add `arch-datastore` registry row; regression-check fixed it during the pass). Under the new spec, this falls cleanly into Step 4 auto-apply class (i): stale registry row + doc demonstrably edited by the feature. The pruned flow would silently bump the row and note it in `Auto-applied: arch-datastore`. **Catch survives, with less PM friction.** ✓
  - **No-catch case — `2026-05-07-shared-types-auto-build`.** Original report: 10 sections, all trivially clean ("skipped" / "no findings" / "n/a"). Under the new spec: Cross-contamination (same "no code-level dependents" finding), Goal-backward (skipped — no post-hoc deliverables), Plugin-config (skipped — no `.claude/` touch), Simplify pass, Status. **5 sections vs 10 — materially shorter.** ✓
- Deferred-to-post-restart (per plan honesty note): acceptance step 4 ("only genuinely ambiguous findings appear as FLAG/BLOCK") partly lands on Wayne's next post-reinstall feature cycle (brief §3 success-signal).

## DEV-002
**Type:** ambiguity-decision
**Deliverable:** D2
**Plan said:** validation step (a) — `grep -c "^### Steps"` shows exactly one.
**Actually:** count is 3 (regression-check at line 26; triage at 101; learnings-synthesis at 142). The triage and learnings-synthesis modes used `### Steps` headings in the original file and were preserved byte-identical, so the count is correctly 3.
**Resolution:** The substantive property — exactly one `### Steps` *inside the regression-check block* — is satisfied (block contains exactly one). Plan validation step (a) was checking the wrong scope; verified the in-scope count via `awk` extraction of the regression-check block.
**Downstream impact?** no
**Agent category:** alignment
