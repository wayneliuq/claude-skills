# Execution Plan: Leaner skill — prune drift, add minimalism + taste

_Implements: product-brief_leaner-skill.md · Date: 2026-06-14_

## Context

Six deliverables against the strategic-implementation plugin: D1 removes the obsolete
drift/goal subsystem (pure subtraction); D2–D3 push proactive minimalism into plan
drafting and review; D4 adds two anti-rationalization tables; D5 brings taste discipline
fully in-plugin; D6 aligns docs and version. All edits are prompt/markdown/shell/JSON —
no application code. Net LOC is deletion-dominant.

## Library lifecycle audit

n/a — clarify declared `none`. No third-party runtime/SDK introduced. The only runtime
artifacts touched are bash hook scripts and `hooks.json` (validated by `bash -n` / `jq`).

## Deliverables (DAG)

### D1 — Remove drift/goal machinery
- **Integration-risk class:** d (shell/JSON edits, no external dependency)
- **User-acceptance steps (from brief):** jq validates hooks.json with no goal-evaluator
  prompt hook; grep for `active-goal|chapter|turn-cap|pending_chapter_rotation` returns
  nothing; `bash -n` passes on all hook scripts; a D-commit still flips `pending_simplify`;
  Stop orchestrator returns `{"ok":true}` with no behavioral flag pending.
- **Macro-deliverable:** false
- **Domains & file partition:** n/a
- **Validation method (chosen here):** cli — run, in order:
  `jq . plugins/strategic-implementation/hooks/hooks.json`;
  `bash -n` on `hook-stop-orchestrator.sh`, `hook-bash-counter.sh`;
  `grep -rn "active-goal\|chapter\|turn-cap\|pending_chapter_rotation\|goal evaluator\|current_chapter\|deliverables_done_in_chapter\|chapter_size" plugins/strategic-implementation/`
  → expect zero hits;
  reason through `hook-bash-counter.sh` that the simplify/loc thresholds still set
  `pending_simplify` with chapter logic removed. (cli, not tdd — the correctness here is
  "machinery absent + survivors intact," provable by grep + lint, not a unit test.)
- **Files:**
  - `plugins/strategic-implementation/hooks/hooks.json`
  - `plugins/strategic-implementation/scripts/hook-stop-orchestrator.sh`
  - `plugins/strategic-implementation/scripts/hook-bash-counter.sh`
  - `plugins/strategic-implementation/skills/executing-plans/SKILL.md`
- **Steps:**
  1. `hooks.json` — delete the Stop `prompt`/haiku goal-evaluator object (the second
     entry in the `Stop` hooks array). Leave the `command` orchestrator entry.
  2. `hook-stop-orchestrator.sh` — delete §1 chapter-rotation block (the
     `pending_chapter_rotation` branch, incl. the `<active-goal>` heredoc + turn-cap
     line) and the trailing "defer to goal evaluator" comment. Keep §2 simplify, §3
     thrash, §4 error-loop, §5 deviation-surface and the emit/exit logic.
  3. `hook-bash-counter.sh` — remove `deliverables_done_in_chapter` append, the
     `DONE`/`CHAPTER_SIZE` reads, and the chapter-complete `pending_chapter_rotation`
     block. Keep the simplify-counter increments, LOC delta, idempotency, and the
     simplify-threshold flag.
  4. `executing-plans/SKILL.md` — remove the `<active-goal>` emit (Step 1), the
     chapter-rollover paragraph, and the touched-file "drift" framing; reframe the
     touched-file announcement (if kept at all) as a plain constraint note, not a
     drift-detector input. In the state-schema JSON block, drop `current_chapter`,
     `deliverables_done_in_chapter`, `chapter_size`, `pending_chapter_rotation`.
- **Deps:** none
- **Pre-flight env check:** `jq`, `bash` available (both standard).
- **may-invalidate:** [README.md, docs/strategic-implementation/documentation-registry.md]
- **Visual contract:** n/a
- **Consumer audit:** required — removing state fields is a shape change to state.json.
  - `hook-stop-orchestrator.sh` (reads `current_chapter`, `chapter_size`,
    `pending_chapter_rotation`) — `updated-in-this-deliverable`
  - `hook-bash-counter.sh` (writes `deliverables_done_in_chapter`, reads `chapter_size`)
    — `updated-in-this-deliverable`
  - `executing-plans/SKILL.md` state-init block — `updated-in-this-deliverable`
  - `hook-helpers.sh` (`si_state_read`/`si_state_mutate`) — `unaffected-because-generic`
    (field-agnostic accessors)
  - other hooks (`edit-tracker`, `error-tracker`, `validation-log-watcher`) —
    `unaffected-because` they never read chapter fields (confirm by grep in validation)

### D2 — Ponytail YAGNI rule at draft time
- **Integration-risk class:** d
- **User-acceptance steps (from brief):** `execution-plan/SKILL.md` has a rule "0"
  ahead of deliverable authoring naming the full hierarchy.
- **Macro-deliverable:** false
- **Validation method (chosen here):** post-hoc — read the edited authoring-rules section;
  confirm rule "0" exists, precedes deliverable creation, and states
  YAGNI → stdlib → native → existing dep → one line → minimum.
- **Files:** `plugins/strategic-implementation/skills/execution-plan/SKILL.md`
- **Steps:**
  1. In Step 3 "Authoring rules," insert rule **0. Does this need to exist?** with the
     six-step hierarchy, applied to every proposed deliverable/abstraction before it is
     drafted. Fold the existing rule 6 ("Reuse before creating") into it as the
     "existing dependency" rung so the two don't overlap.
- **Deps:** none (but sequence after D1 to avoid same-session churn on sibling files)
- **Pre-flight env check:** none
- **may-invalidate:** none
- **Visual contract:** n/a
- **Consumer audit:** n/a — no shape change.

### D3 — Simplify review → deletion candidates against the hierarchy
- **Integration-risk class:** d
- **User-acceptance steps (from brief):** `agents/simplify.md` scope/output reference the
  ponytail hierarchy and a named deletion-candidate list.
- **Macro-deliverable:** false
- **Validation method (chosen here):** post-hoc — read the edited agent; confirm the
  hierarchy framing and that the output schema's `recommendations`/flags are expressed as
  named deletion candidates (deliverable id + reason).
- **Files:** `plugins/strategic-implementation/agents/simplify.md`
- **Steps:**
  1. Reframe the Scope section to score each new unit against the hierarchy from D2.
  2. Tighten the output: `recommendations` lead with `drop` candidates naming the
     deliverable id and the hierarchy rung it fails. Keep PASS/FLAG/ALTERNATIVE; keep
     "never BLOCK."
- **Deps:** D2 (shares the hierarchy wording — author once in D2, cite in D3)
- **Pre-flight env check:** none
- **may-invalidate:** none
- **Consumer audit:** n/a — no shape change (output JSON keys unchanged).

### D4 — Two anti-rationalization tables
- **Integration-risk class:** d
- **User-acceptance steps (from brief):** exactly two "excuse → rebuttal" tables exist at
  validation-method-honesty and consumer-audit-on-shape-change; no other gate gains one.
- **Macro-deliverable:** false
- **Validation method (chosen here):** post-hoc — read both gates; confirm one table each
  and none elsewhere.
- **Files:**
  - `plugins/strategic-implementation/skills/execution-plan/SKILL.md` (rules 7 + 8)
  - `plugins/strategic-implementation/skills/executing-plans/SKILL.md` (if the gate is
    restated there at build time — add the table at the canonical home only, cross-ref
    from the other; do NOT duplicate)
- **Steps:**
  1. Validation-method-honesty table (at rule 7): e.g. "unit tests are faster" → mocking
     the integration point is orthogonal-to-correctness coverage, not validation.
  2. Consumer-audit table (at rule 8): e.g. "probably nothing else uses this" → grep
     proves it; hand-waving is rejected by review.
- **Deps:** D2 (same file, execution-plan/SKILL.md — sequence to avoid edit collision)
- **Pre-flight env check:** none
- **may-invalidate:** none
- **Consumer audit:** n/a — no shape change.

### D5 — Frontend taste discipline, fully in-plugin
- **Integration-risk class:** d
- **User-acceptance steps (from brief):** `agents/frontend-quality.md` exists in-plugin;
  ui-mockup cites the slim rows, frontend-engineer the rich rows; a generated mockup
  passes the anti-tell check.
- **Macro-deliverable:** false
- **Validation method (chosen here):** post-hoc + one preview spot-check — read the three
  files for correct slim/rich allocation and no `frontend-design` reference; then have
  the orchestrator generate one sample `mockup.html` and grep it for the banned tells
  (em-dash `—`, `Scroll`, `BETA`/`INVITE-ONLY`, `lorem`, section-number eyebrows) →
  expect zero.
- **Files:**
  - `plugins/strategic-implementation/agents/frontend-quality.md` (NEW — full ruleset)
  - `plugins/strategic-implementation/skills/ui-mockup/SKILL.md` (cite slim subset)
  - `plugins/strategic-implementation/agents/frontend-engineer.md` (cite rich subset)
- **Steps:**
  1. Author `frontend-quality.md` with two clearly-labeled tiers:
     - **Slim (mockup-safe / legibility & IA):** em-dash ban; eyebrow restraint
       (≤1 per 3 sections); section-layout-repetition ban (≥4 layout types across 8
       sections); hero fits initial viewport; no fake-precise numbers; no scroll cues;
       no version-label tells; real content not lorem; off-black/off-white not pure.
     - **Rich (shipped UI / pixel quality):** font discipline (avoid Inter default —
       Geist/Outfit/Satoshi); LILA/purple-glow & neon-gradient ban; motion-must-be-
       motivated + `prefers-reduced-motion` gate; design-system selection table;
       image/asset strategy (no div-fake-screenshots).
  2. `ui-mockup/SKILL.md` — add an "Anti-slop (slim)" discipline rule citing the slim
     tier; keep the throwaway/no-pixel-fidelity mandate (HD4).
  3. `frontend-engineer.md` — add a quality-bar section citing the rich tier.
- **Deps:** none
- **Pre-flight env check:** preview tool available for the spot-check (fallback: post-hoc
  grep of a hand-generated sample if preview is down).
- **may-invalidate:** [README.md]
- **Visual contract:** n/a (the rules ARE the contract)
- **Consumer audit:** n/a — new file + additive references, no shape change.

### D6 — Docs + version alignment
- **Integration-risk class:** d
- **User-acceptance steps (from brief):** README drops drift/chapter/turn-cap prose;
  `plugin.json` reads 4.3.0; registry has no stale entry for removed machinery.
- **Macro-deliverable:** false
- **Validation method (chosen here):** post-hoc — grep README for `drift|chapter|turn-cap`
  → expect zero; confirm `plugin.json` version; review registry diff.
- **Files:**
  - `plugins/strategic-implementation/README.md`
  - `plugins/strategic-implementation/.claude-plugin/plugin.json`
  - `docs/strategic-implementation/documentation-registry.md` (iff an entry is stale)
- **Steps:**
  1. Grep README for the removed concepts; rewrite/delete those sections.
  2. Bump `plugin.json` version 4.2.1 → 4.3.0.
  3. Update `plugin.json` description string — drop "deterministic chapter rotation,
     goal evaluation" from the v3.6 clause.
  4. Update/remove any registry entry whose update-trigger D1–D5 invalidated.
- **Deps:** D1, D5 (docs describe behavior those change)
- **Pre-flight env check:** none
- **may-invalidate:** none (this IS the doc-sync deliverable)
- **Consumer audit:** n/a.

### D7 — Acknowledge open-source inspiration
- **Integration-risk class:** d
- **User-acceptance steps (from brief):** README has an "Acknowledgments — inspirations
  for v4.3.0" subsection naming ponytail, addyosmani/agent-skills, and taste-skill with
  links, the specific idea borrowed from each, and what heavyweight scope was rejected.
- **Macro-deliverable:** false
- **Validation method (chosen here):** post-hoc — read the new subsection; confirm all
  three repos, links, idea-taken, and idea-rejected per the existing v2.2/v3.1 format.
- **Files:** `plugins/strategic-implementation/README.md`
- **Steps:**
  1. Add an "Acknowledgments — inspirations for v4.3.0" subsection after the v3.1 block,
     matching the established format:
     - **ponytail (DietrichGebert)** — the "does this need to exist? → YAGNI → stdlib →
       native → existing dep → one line" hierarchy, imported into execution-plan draft
       rule 0 and the simplify reviewer (D2/D3). Rejected: the `ponytail:` deferred-debt
       ledger and per-shortcut comment machinery.
     - **agent-skills (addyosmani)** — anti-rationalization tables at two skip-prone
       gates (D4). Rejected: the ~100-line change-sizing norm (conflicts with our
       fitness-not-size gate), autonomous `/build auto`, and doubt-driven protocol.
     - **taste-skill (Leonxlnx)** — the anti-slop "AI Tells" checklist, split slim→mockup
       / rich→frontend (D5). Rejected: the motion/GSAP/dials/design-system machinery in
       the throwaway mockup path.
- **Deps:** D6 (same README region; sequence after to avoid edit collision)
- **Pre-flight env check:** none
- **may-invalidate:** none
- **Consumer audit:** n/a — additive doc section.

## Parallel groups & order

- **Group 1 (first, alone):** D1 — largest delete, heaviest on `executing-plans/SKILL.md`.
- **Group 2 (sequential, shared files):** D2 → D4 (both edit `execution-plan/SKILL.md`),
  then D3 (cites D2's hierarchy wording).
- **Group 3 (parallel-eligible with Group 2):** D5 — disjoint files (frontend surfaces).
- **Group 4 (last, sequential):** D6 → D7 — both touch README; D6 fixes behavior prose +
  version, D7 appends the acknowledgments subsection.

### Workflow decision
none — all deliverables decomposable / sequential. No macro-deliverable (no ≥2-domain
disjoint-output unit that loses e2e-validateability when split).

## Reused existing patterns
- Behavioral breakers (`pending_simplify`, `pending_error_loop`, `pending_thrash_pause`,
  `pending_deviation_surface`) — reused as-is; D1 deletes only the chapter sibling.
- `si_state_read`/`si_state_mutate` field-agnostic accessors — no change needed for the
  state-schema shrink.
- Existing `simplify` agent output schema (D3 sharpens wording, keeps keys).

## Risks & contingencies
- **R1: orphaned state read after D1.** Mitigation: the D1 grep gate + consumer audit
  catch any surviving reference before commit.
- **R2: D2/D4 edit collision on execution-plan/SKILL.md.** Mitigation: sequence D2→D4.
- **R3: preview unavailable for D5 spot-check.** Mitigation: fall back to grep of a
  hand-generated sample mockup (post-hoc), per autonomy rules.
- **R4: README describes drift in prose not caught by grep terms.** Mitigation: D6 reads
  README fully, not grep-only.

## Out of scope for this plan
- Deprecating/deleting the `frontend-design` skill.
- External artifact store, memory subsystem, learnings-benchmark changes.
- Any addyosmani device beyond the two anti-rationalization tables.
- taste-skill motion/GSAP/dials/design-system machinery inside the mockup path.
