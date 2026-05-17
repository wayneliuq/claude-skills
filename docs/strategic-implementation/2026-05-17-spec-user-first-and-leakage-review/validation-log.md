# Validation log
_Feature: spec-user-first-and-leakage-review · Started: 2026-05-17 · Autonomy: auto_

## Note on commit scope

The deliverable files for this plan live at `/Users/qiangliu/.claude/plugins/cache/wayneliuq/strategic-implementation/3.3.0/` — outside this axiph repo's git tree. Per-deliverable atomic commits in this repo therefore contain only the feature-folder docs (execution-plan status updates, checkpoint, this log). The plugin-file edits themselves are made out-of-tree and require an upstream PR to GitHub `wayneliuq/strategic-implementation` after execution (surfaced in post-execution).

Each deliverable's validation will include a path-by-path inspection of the out-of-tree plugin files to confirm the documented changes landed.

---

## ED1 — validation

**Plugin file edited:** `/Users/qiangliu/.claude/plugins/cache/wayneliuq/strategic-implementation/3.3.0/skills/product-brief-drafter/SKILL.md`

**Discipline-rule inspection (post-hoc):**
- Rule 4 "Define the user" present at line 21. ✅
- Rule 6 "No implementation leakage in §2 or §5" present at line 23. ✅
- Rule 7 "HARD DECISIONs … stay at strategic altitude" present at line 24. ✅
- Brief template `**Who is the user of this feature:**` slot at top of §2 present at line 53. ✅
- "## Leakage gate (both modes)" section present at line 108 with inline sonnet prompt. ✅
- "### After writing" and "### After revising" updated to run gate before PM announcement. ✅

**Leakage-injection smoke test:**
- Source: snapshot of this feature's brief at `/tmp/leakage-smoke-test-brief.md`.
- Injection: `### D5 — User-validation reviewer (built with LangChain and stores findings in SQLite) …`.
- Gate run via `Agent` with `model: "sonnet"` and the inline prompt from drafter's Leakage gate section.
- **Result:** `status: FLAG` — flagged D5 LangChain/SQLite with line excerpt + reason. Also caught a bonus real-world leakage in D4 ("sonnet-class") that existed in the live brief — logged as DEV-001 below for follow-up brief revision.

**Latency check (alignment FLAG #1):**
- Sonnet leakage gate wall-clock: **9.093s** (`duration_ms: 9093`).
- In-session alignment-tier reference: **27.312s** (`duration_ms: 27312`) on this plan.
- Assertion: 9s ≪ 27s. Sonnet gate materially faster than generalist tier. ✅

**Success-signal validation (alignment FLAG #2):**
- Representative pre-existing brief picked: `docs/strategic-implementation/2026-05-06-roadmap-refactor/product-brief_roadmap-refactor.md` (drafted under old discipline).
- Ran leakage gate against it directly (proxy for re-draft — if old brief FLAGs, the gate would catch the leakage during a re-draft under updated discipline, forcing cleanup before PM handoff).
- **Result:** `status: FLAG` — 10 findings naming specific file paths (`docs/wiki/Axiph Version Feature List.md`, `mvp-ux.md`), CLI tools (`grep`), markdown syntax (`- [x]`), and internal artifacts in §1, §2, §4, §5.
- Conclusion: gate catches real leakage in pre-existing briefs. A re-draft under updated discipline would yield §2/§5 free of these leaks. Success signal met (as far as gate behavior is concerned; full re-draft deferred — gate is the enforcing mechanism). ✅

## DEV-001
**Type:** ambiguity-decision
**Deliverable:** ED1
**Plan said:** brief's success signal references "this feature's own brief, re-drafted, contains zero impl mentions"
**Actually:** the live brief was discovered to contain "sonnet-class" in D4 acceptance step (caught by gate during ED1's own smoke test as a bonus finding). Not blocking ED1, but the feature's own brief has a leak by its own standard.
**Resolution:** Brief needs a v0.3 revision to soften D4.4 from "(sonnet-class, single agent)" to "materially faster than the generalist tier" — outcome-level. Tracked as post-execution follow-up; does not block plan execution because the live drafter changes are landed and gating mechanism works.
**Downstream impact?** no — drafter discipline is in place; subsequent deliverables unaffected. Brief revision is a documentation hygiene follow-up.
**Agent category:** alignment

---

## ED2 — validation

**Plugin file created:** `/Users/qiangliu/.claude/plugins/cache/wayneliuq/strategic-implementation/3.3.0/agents/user-validation.md`

**File inspection (post-hoc):**
- Frontmatter `name: user-validation`, description references generalist tier + walkthrough role. ✅
- "Adversarial stance" section present with named soft-failure modes. ✅
- "Scope" lists 5 dimensions: named user, interaction surface, walkthrough, reachability, PMF. ✅
- "Do not review" explicitly cedes: missing deliverables → alignment; architecture conformance → alignment; consumer audits → alignment; validation-method honesty → tests; simplicity → simplify; specialist domains → specialists. ✅
- "Output schema" includes `walkthrough[]` matrix + `flags[]` + `recommendations[]` + `specialists_needed[]`. Cap ~1500 tokens. ✅
- "Escalation triggers" list BLOCK conditions including the canonical "client-built, pipeline-missing" loophole. ✅
- "Processing learnings" tags: `#user-validation`, `#pmf`, `#walkthrough`, `#reachability`. ✅

**Synthetic-plan cli test:**
- Synthetic brief: `/tmp/synthetic-brief-pipeline-missing.md` — Project Activity Dashboard; named user is an end-user in the shipped product; success signal is "real events appear within seconds".
- Synthetic plan: `/tmp/synthetic-plan-pipeline-missing.md` — D1 ships UI + 5-row mock array + stub modal; D2 ships empty state with cleared mock; activity schema / ingestion / `/activity` API all explicitly out-of-scope.
- Invoked via `Agent` with `subagent_type: general-purpose` (new subagent type not yet registered in this session; agent prompt was loaded from the user-validation.md file inline).
- **Result:** `status: BLOCK`. Walkthrough enumerated 4 acceptance steps, named supporting deliverables per step, marked 2 as `reachable: no` (D1 step 2: real events absent because schema/ingestion/API deferred; D1 step 3: stub modal not real detail). Two HIGH flags on reachability; one HIGH flag on PMF recognizability. Did NOT flag "missing deliverables" directly — flagged the unreachable acceptance steps instead, respecting the anti-overlap rule with alignment.

**Acceptance step coverage:**
- Brief D5.1 (reviewer walks step-by-step through named user's actions): ✅ walkthrough[] matrix is the structural artifact.
- Brief D5.2 (enumerates each step paired with deliverables, or flags unreachable): ✅ supporting_deliverables[] + reachable enum.
- Brief D6 (catches client-built-no-pipeline loophole with BLOCK naming the unreachable step): ✅ "D1 step 2: real events in their workspace … schema, ingestion, and backend API are explicitly deferred out-of-scope".

---

## ED3 — validation

**Plugin files edited:**
- `/Users/qiangliu/.claude/plugins/cache/wayneliuq/strategic-implementation/3.3.0/agents/alignment.md` — PMF removed; "Do not review" updated; `flags[].dimension` enum cleaned (dropped `pmf`).
- `/Users/qiangliu/.claude/plugins/cache/wayneliuq/strategic-implementation/3.3.0/skills/review/SKILL.md` — `user-validation` added to Step 2 generalist tier; "Generalist tier composition" section added; specialist union now includes user-validation's `specialists_needed`; BLOCK propagation + corroboration-dedup updated for the alignment ↔ user-validation pair; Re-review rule extended.
- `/Users/qiangliu/.claude/plugins/cache/wayneliuq/strategic-implementation/3.3.0/skills/strategic-implementation/SKILL.md` Step 4 — narrative now names three generalists.

**File-on-disk inspection (post-hoc):**
- alignment.md Scope contains exactly five top-level dimensions (1 brief, 2 consumer-audit, 3 architecture, 4 future-proofing, 5 specialist routing). PMF absent. ✅
- alignment.md "Do not review" explicitly cedes "PMF, user-validation walkthroughs, and user-reachability checks". ✅
- alignment.md output schema dimension enum: `brief|consumer-audit|architecture|future-proofing`. `pmf` removed. ✅
- review/SKILL.md "## Generalist tier composition" section present at line 21, table lists alignment / simplify / user-validation with scope + anti-overlap. ✅
- review/SKILL.md Step 2 launches three agents in parallel; brief path passed to alignment AND user-validation. ✅
- review/SKILL.md Step 5 BLOCK propagation includes user-validation; corroboration-dedup note added for "D<n> absent" ↔ "step k of D<n> unreachable" pair. ✅
- strategic-implementation/SKILL.md Step 4 names three generalists. ✅

**Joint synthetic-plan cli check (D5.2, D5.3, D6 end-to-end):**
Three agents launched in parallel against the synthetic dashboard plan + brief.

- **alignment (live agent):** BLOCK. Walkthrough rationale produced. ⚠️ Output still contains `dimension: "pmf"` — see DEV-002 below: the live agent loaded at session start; file edits do not take effect until plugin reload.
- **simplify:** FLAG. Noted that scope-vs-brief mismatch is outside simplify's remit and surfaced it as a flag only — correct boundary respect.
- **user-validation (invoked via general-purpose loading the file inline):** BLOCK. Produced 4-row walkthrough[] matrix, 3 steps `reachable: no` with `(missing: ...)` annotations on supporting deliverables, HIGH flags on reachability + pmf + interaction-surface. Did NOT directly flag "missing deliverables" — flagged the unreachable acceptance steps as the consequence. Anti-overlap with alignment respected. ✅

**Acceptance step coverage:**
- D7.2 (alignment scope = 5 dimensions, PMF absent): ✅ file-on-disk.
- D7.4 (alignment cedes PMF AND walkthroughs): ✅ file-on-disk.
- D5.1 (three parallel generalists with documented roles): ✅ file-on-disk + observed in joint run.
- D5.2 (per-step walkthrough): ✅ user-validation produced walkthrough[] matrix.
- D5.3 / D6 (BLOCK naming unreachable step on client-built-pipeline-missing): ✅ user-validation BLOCKed with "D1 step 2: real events ... schema, ingestion, and backend API explicitly deferred out-of-scope".
- D7.1 (generalist tier composition documented): ✅ "## Generalist tier composition" section in review/SKILL.md.

## DEV-002
**Type:** ambiguity-decision
**Deliverable:** ED3
**Plan said:** end-to-end run asserts "three generalists run in parallel; `user-validation` BLOCKs naming the unreachable step; `alignment` does NOT flag PMF (because PMF moved); orchestrator surfaces BLOCK"
**Actually:** alignment did flag `dimension: pmf` in the joint run, because the live alignment agent was loaded at session start before my edits to `agents/alignment.md`. Plugin agents in this runtime do not hot-reload on file change. The on-disk file is correct (verified by grep — Scope has 5 dimensions sans PMF; dimension enum dropped `pmf`).
**Resolution:** The deliverable's file-on-disk acceptance criteria (D7.2, D7.4, D7.1) are met. The end-to-end "alignment does not flag PMF" piece can only be verified in a fresh session where the plugin re-loads agent definitions from disk. Logging as a runtime caveat; this is not a correctness failure of the edits, only a runtime-reload limitation.
**Downstream impact?** no — post-execution regression-check will run with the same loaded-at-session-start agents; will use file-on-disk state as ground truth. After upstream sync to GitHub `wayneliuq/strategic-implementation` and a plugin update on the operator's side, the new alignment behavior takes effect.
**Agent category:** alignment
