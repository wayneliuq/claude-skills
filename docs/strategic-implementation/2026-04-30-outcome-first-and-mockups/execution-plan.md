# Execution Plan: Outcome-First Brief + Optional UI Mockup + Doc Registry
_Implements: product-brief_outcome-first-and-mockups.md (v0.3) · Date: 2026-05-01_

## Context
12 deliverables implementing 21 brief items (merge mapping in each deliverable). All are markdown/skill content changes — no third-party runtime, no DB, no UI code. Each deliverable lands as one atomic commit. Alignment patches applied (D5 promoted to Phase 1; consumer audits expanded for D1/D12; D11+D14 coordinated; D6 format constraint).

## Library lifecycle audit
Omitted — clarify declared no integration-risk dependencies.

## Deliverables (DAG)

### D1 — Documentation registry file (foundation)
_Implements brief D12._
- **Class:** d · **Validation:** `cli` — file exists; cat shows purpose preamble + 5-column schema (`Path | Covers | Last Updated | Update Trigger | Owning Area`); first row = this brief; semantic anchors: "registry", "an index, not a knowledge base"
- **Files:** `docs/strategic-implementation/documentation-registry.md` (new)
- **Steps:**
  1. Create file: 1-paragraph purpose; 5-column markdown table; first row points to this brief.
- **Deps:** none · **Pre-flight:** none
- **Consumer audit:** new schema; consumers below MUST match field-for-field:
  - `D5 (registry-aware clarify)` reads at Step 1, upserts at Step 3 → reads `Path`, writes all 5 fields with `Last Updated = today`
  - `D8 (plan registry tagging)` loads at Step 2; consumes `Path`, `Covers`, `Update Trigger` to compute `may-invalidate` — `updated-in-D8`
  - `D9 (executing-plans registry bundle)` reads `Path` per `may-invalidate`, writes `Last Updated` on commit — `updated-in-D9`
  - `D10 (post-execution registry verify)` reads `Last Updated` to verify advance — `updated-in-D10`

### D2 — Plan-mode exit checks (defense-in-depth)
_Implements brief D17. Brief HARD DECISION mandates duplication; do not collapse._
- **Class:** d · **Validation:** `cli` — grep each file for entry-check block (semantic anchors: "plan mode", "ExitPlanMode", "execution-plan exempt"); orchestrator Constraints names the rule
- **Files:**
  - `plugins/strategic-implementation/skills/product-brief-drafter/SKILL.md` (Mode:draft + Mode:revise entries)
  - `plugins/strategic-implementation/skills/executing-plans/SKILL.md` (Step 0)
  - `plugins/strategic-implementation/skills/post-execution/SKILL.md` (each mode entry)
  - `plugins/strategic-implementation/skills/strategic-implementation/SKILL.md` (Constraints block L120-127)
- **Steps:**
  1. Add 2-line entry-check ("If plan mode is active, call ExitPlanMode before writing files. `execution-plan` is exempt.") to each file-writing sub-skill at its mode/step entry.
  2. Add Constraints bullet to orchestrator: "Before invoking product-brief-drafter / executing-plans / post-execution, exit plan mode if active. Never exit plan mode before invoking execution-plan."
- **Deps:** none · **Pre-flight:** none · **Consumer audit:** n/a

### D3 — Outcome-first framing in description + README
_Implements brief D5. Promoted to Phase 1 per alignment A1._
- **Class:** d · **Validation:** `cli` — orchestrator frontmatter `description:` and preamble both lead with "outcome-first" (semantic anchors: "outcome-first", "outside-in"); README intro + "How it works" reference outcome-first as headline; skill name `strategic-implementation` unchanged in `package.json` and `.claude-plugin/plugin.json`
- **Files:**
  - `plugins/strategic-implementation/skills/strategic-implementation/SKILL.md` (frontmatter L3 + preamble L8)
  - `plugins/strategic-implementation/README.md` (intro L1-14, "How it works" L38)
- **Steps:**
  1. Rewrite frontmatter `description:` lead clause: "Outcome-first orchestrator. Routes PM-described work outside-in — clarify → product brief → optional UI mockup → execution plan → deliverable-gated execution → post-execution."
  2. Rewrite preamble paragraph to lead "Outcome-first planning-to-execution orchestrator…"
  3. README intro: replace lead sentence with one naming "outcome-first" as the headline principle. Add 1-sentence reference in "How it works" about working-backwards from the user-observable outcome.
  4. Verify `package.json` and `plugin.json` not renamed.
- **Deps:** none · **Pre-flight:** none · **Consumer audit:** n/a

### D4 — Brief template restructure (spine + working-backwards + success-signal + boundaries split)
_Implements brief D1+D2+D3+D4. Merged per simplify (one template, one coherent edit)._
- **Class:** d · **Validation:** `cli` — section count 7; section names match (semantic: "Working backwards", "Success signal", "Boundaries"); no "Acceptance criteria" heading; discipline rules name release-note voice + outside-observable + anti-goals philosophy-level
- **Files:** `plugins/strategic-implementation/skills/product-brief-drafter/SKILL.md` (template block L39-78; discipline rules L17-25)
- **Steps:**
  1. Replace template (L39-78) with 7-section spine. Drop section 3 "Acceptance criteria"; renumber. Section 1 "Working backwards" includes inline ≤5-sentence + release-note-voice guidance. Section 3 "Success signal" includes outside-observable guidance + `TBD — open question` propagation rule. Section 4 "Boundaries" has 3 rows (in/out/anti-goals) with anti-goals discipline note.
  2. Update discipline rules (L17-25): rule 3 references "validation method = acceptance test"; new rule "Working-backwards is section 1; if clarify passed `working-backwards: TBD`, write 'TBD — open question' verbatim, do not fabricate."
- **Deps:** D2 (entry-check lands first to avoid same-file conflict) · **Pre-flight:** none
- **Consumer audit:** template shape change.
  - `execution-plan/SKILL.md` Step 2 reads "deliverables, acceptance criteria, scope boundary, hard decisions, document references" (L29) → `updated-in-D8` (drop "acceptance criteria"; rely on per-deliverable validation + Section 3 success-signal)
  - `post-execution/SKILL.md` goal-backward verification reads brief → `unaffected-because-success-signal-and-per-deliverable-validation-cover-prior-acceptance-criteria-role`
  - `clarify/SKILL.md` Output (L77-87) writes `working-backwards` + `success-signal` fields → `updated-in-D6` (clarify writes the new fields; drafter consumes here)
  - `strategic-implementation/SKILL.md` orchestrator Step 3 invocation passes "Clarified request" → `unaffected-because-passthrough`
  - `review/SKILL.md` + alignment agent prompts that read "acceptance criteria" → `explicit-skip-because-this-cycle-runs-pre-update; future briefs use new spine; review prompts read deliverable validation rather than separate AC section`
  - This brief itself (already v0.3 spine) → `unaffected`

### D5 — Registry-aware clarify (read at Step 1 + write at point of mention in Step 3)
_Implements brief D13+D20. Merged per simplify (read/write halves of same skill file)._
- **Class:** d · **Validation:** `cli` — Step 1 instruction loads registry if present (semantic: "documentation-registry.md", "load if present"); Step 3 doc-references subsection (L39-46) captures `covers` + `update-trigger` follow-ups inline AND upserts a registry row at point of mention
- **Files:** `plugins/strategic-implementation/skills/clarify/SKILL.md` (Step 1 L10; Step 3 doc-refs L39-46)
- **Steps:**
  1. Step 1: "If `docs/strategic-implementation/documentation-registry.md` exists, load it. Use known entries to ground the doc-references prompt — name the docs you already know about."
  2. Step 3 subsection B (Document references): "For each doc the PM names: (a) ask 'what does it cover (one line)?' (b) ask 'what changes would make it stale?'. Write/upsert a registry row immediately. If registry doesn't exist, create per D1 schema."
- **Deps:** D1 · **Pre-flight:** none · **Consumer audit:** n/a — registry schema unchanged

### D6 — Clarify outcome-paired prompts (working-backwards + success-signal)
_Implements brief D18+D19. Merged per simplify (paired ask in same step)._
- **Class:** d · **Validation:** `cli` — Step 3 has new subsection with both prompts (semantic: "if this shipped tomorrow", "outside-observable", "TBD — open question"); Output spec carries `working-backwards` and `success-signal` fields
- **Files:** `plugins/strategic-implementation/skills/clarify/SKILL.md` (Step 3 at L28-66; Output L77-87)
- **Steps:**
  1. Add Step 3 subsection "C. Outcome-paired prompts": prompt 1 *"If this shipped tomorrow, what's the one-sentence change to the user's life?"*; prompt 2 *"How would you know it worked from outside — a query, a behavior, a metric? Not 'the deliverable shipped.'"*; capture each as one-sentence answer or `TBD — open question`. Never block.
  2. Add `working-backwards` and `success-signal` fields to Output (L77-87).
- **Deps:** none · **Pre-flight:** none · **Consumer audit:** clarify output gains 2 fields. Drafter consumes → `updated-in-D4`. Orchestrator passthrough → `unaffected`.

### D7 — Clarify outcome playback in Confirm (Step 4)
_Implements brief D21._
- **Class:** d · **Validation:** `cli` — Step 4 emits one-line playback of working-backwards in PM's words (semantic: "to confirm", "when X happens for user Y"); on PM correction, captured phrasing is the canonical working-backwards
- **Files:** `clarify/SKILL.md` (Step 4 L67-76)
- **Steps:**
  1. Step 4: before output, play back: "To confirm — when X happens for user Y, you'll consider this shipped." (substitute from working-backwards). If PM corrects, capture corrected phrasing as canonical.
- **Deps:** D6 · **Pre-flight:** none · **Consumer audit:** n/a

### D8 — Execution-plan loads registry + tags `may-invalidate` + adds `Visual contract:` field (one template diff)
_Implements brief D14 + execution-plan portion of D11. Merged per alignment A4 (one template diff)._
- **Class:** d · **Validation:** `cli` — Step 2 instruction names registry load + per-deliverable tagging (semantic: "may-invalidate", "load registry"); Step 3 deliverable template includes both `may-invalidate:` and `Visual contract:` fields; Step 5 plan summary surfaces impacted entries
- **Files:** `plugins/strategic-implementation/skills/execution-plan/SKILL.md` (Step 1 inputs L8; Step 2 L26-36; Step 3 deliverable template; Step 5 presentation)
- **Steps:**
  1. Step 1 inputs: accept optional `Mockup path`.
  2. Step 2: "Load `docs/strategic-implementation/documentation-registry.md`. For each registry entry, judge whether deliverables in this brief might invalidate it (touches the path, area, or update-trigger). Tag each deliverable with `may-invalidate: [doc-paths]` or `may-invalidate: none`."
  3. Step 3 deliverable template: add `may-invalidate:` and `Visual contract: <mockup-path | n/a>` fields after Pre-flight env check. Drop "acceptance criteria" reference per D4.
  4. Step 5 presentation: surface union of impacted entries to PM.
- **Deps:** D1, D4 (drops AC reference) · **Pre-flight:** none · **Consumer audit:** plan template adds 2 fields. `executing-plans` → `updated-in-D9`; `post-execution` → `updated-in-D10`. Plans drafted before this cycle → `explicit-skip-because-pre-feature-plans-not-backported`.

### D9 — Executing-plans bundles doc updates into atomic commit
_Implements brief D15._
- **Class:** d · **Validation:** `cli` — build phase prompts when `may-invalidate` non-empty (semantic: "may-invalidate", "same commit", "bump Last Updated"); commit step (L100-110) bundles registry-tracked doc edits and bumps Last Updated
- **Files:** `plugins/strategic-implementation/skills/executing-plans/SKILL.md` (build L70-76; commit L100-110)
- **Steps:**
  1. Build phase: "If deliverable's `may-invalidate` is non-empty, after building primary changes, prompt PM (auto: surface; supervised: pause): 'This deliverable may invalidate <docs>. Update them now in the same commit?' Apply edits."
  2. Commit phase: atomic commit includes registry-tracked doc updates; bump registry row's `Last Updated` to today.
- **Deps:** D1, D8 · **Pre-flight:** none · **Consumer audit:** n/a

### D10 — Post-execution verifies registry + visual-diff prompt
_Implements brief D16 + post-execution portion of D11._
- **Class:** d · **Validation:** `cli` — regression-check Step 1 (L18-20) loads registry, verifies `Last Updated` advance per deliverable's `may-invalidate` (semantic: "Last Updated", "stale entry", "block close in supervised"); for deliverables with `Visual contract` non-empty, prompts manual visual-diff against mockup
- **Files:** `plugins/strategic-implementation/skills/post-execution/SKILL.md` (regression-check L18-63; cross-mode rules L113)
- **Steps:**
  1. Regression-check Step 1: load registry. For each deliverable's `may-invalidate` entries, check the row's `Last Updated` ≥ feature start. For each stale, surface: "Deliverable D<n> declared may-invalidate <path> but registry row not updated. Update now? (y/n/skip)."
  2. Add: for each deliverable with `Visual contract: <path>` non-empty, prompt: "Open <mockup-path> and compare against shipped UI. Match? (y/n/notes)." Capture in regression-check output.
  3. Cross-mode rules: stale registry entries block cycle close in `supervised`; surface but do not block in `auto`/`yolo`.
- **Deps:** D1, D8 · **Pre-flight:** none · **Consumer audit:** n/a

### D11 — New ui-mockup sub-skill (all modes shipped together)
_Implements brief D6+D8+D9+D10. Merged per simplify; format constraint per alignment A5._
- **Class:** d · **Validation:** `preview` for D6/D10 acceptance (open mockup in browser; simulate conflict). `cli` for D8/D9 file structure (semantic: "generate", "revise", "conflict-back-to-brief", "discovery order", "neutral fallback")
- **Files:** `plugins/strategic-implementation/skills/ui-mockup/SKILL.md` (new)
- **Steps:**
  1. Create directory + SKILL.md. Frontmatter: `name: ui-mockup`; description leads with "Generates a static HTML mockup as the visual contract for non-trivial UI work."
  2. Use `### Task` headings throughout (NOT `## Step N` + `---` separators) per L-003 line-budget learning.
  3. Sections: Discipline rules · Mode: generate (style discovery: glob CSS `:root { --` vars → glob `tailwind.config.*` → glob theme paths → documented neutral palette; output single inline-CSS HTML to `<feature-folder>/mockup.html` with comment header citing brief slug + discovery result; no `<script>` tags, no external assets) · Mode: revise (apply `<!-- pm: -->` comments inline + sibling `mockup-feedback.md`; remove applied comments; append revision-log block at top) · Mode: conflict-back-to-brief (before applying a comment, scan brief deliverables for textual conflict; on conflict, surface "this contradicts D<n>: <text>. Revise brief or abandon mockup change?"; on revise-brief choice, invoke `product-brief-drafter:revise`) · Handoff.
- **Deps:** none · **Pre-flight:** none — `preview` is "open mockup.html in browser" · **Consumer audit:** n/a (new artifact)

### D12 — Orchestrator Step 3.5 wiring + pre-flight scope estimate
_Implements brief D7._
- **Class:** d · **Validation:** `preview` — run skill on a brief introducing a new screen; orchestrator emits `~N lines, <small|medium|large>, reason: <trigger>` (semantic: "pre-flight", "scope estimate", "explicit confirm") between brief approval and execution-plan; on single-button brief no prompt
- **Files:** `plugins/strategic-implementation/skills/strategic-implementation/SKILL.md` (between L80 and L82, before Step 4)
- **Steps:**
  1. Add new "Step 3.5 — Optional UI mockup" section. Trigger criterion: brief introduces (a) a new screen, (b) a flow with ≥2 steps, or (c) an information-architecture change. Non-trigger: single controls, copy-only, style-only.
  2. On trigger: emit estimate `~<N> lines (<small|medium|large>), reason: <which trigger>`. Wait for explicit confirm (`yes`/`skip`). PM may always override either way.
  3. On confirm: invoke `strategic-implementation:ui-mockup` Mode: generate → mockup revision loop (PM `<!-- pm: -->` → invoke revise mode) mirroring brief revision loop. On approval: pass `Mockup path` as additional input to Step 4 (execution-plan).
- **Deps:** D11 · **Pre-flight:** none · **Consumer audit:** orchestrator passes new `Mockup path` field → `updated-in-D8`.

## Parallel groups & order

- **Phase 1 (parallel, foundations):** D1 (registry file), D2 (plan-mode exit checks), D3 (outcome-first framing).
- **Phase 2 (parallel):** D4 (brief template — after D2 to avoid same-file conflict), D6 (clarify outcome-paired prompts), D11 (new ui-mockup file).
- **Phase 3 (parallel):** D5 (registry-aware clarify — after D1), D7 (clarify playback — after D6), D8 (plan registry+visual-contract — after D1, D4), D12 (orchestrator Step 3.5 — after D11).
- **Phase 4 (parallel):** D9 (executing-plans registry bundle — after D8), D10 (post-execution verify + visual-diff — after D8).

## Reused existing patterns
- `<!-- pm: ... -->` comment-and-revise — defined in `product-brief-drafter` Mode:revise (L96-114); D11 reuses verbatim.
- Orchestrator step structure (Announce → Invoke → Loop) — D12's Step 3.5 mirrors current Step 3.
- Atomic commit per deliverable — D9 plugs into existing commit step at `executing-plans` L100-110.
- Frontmatter + Mode-block layout — D11 mirrors `product-brief-drafter`'s shape, with `### Task` instead of `## Step N`.
- HARD DECISION + tradeoff table convention — already in brief.

## Risks & contingencies
- **Trigger ambiguity (D12).** Mitigation: explicit trigger reason in pre-flight + PM override either way.
- **Style discovery (D11).** Mitigation: skill records what was found and what fell back; estimate surfaces this before generation.
- **Registry decay (D10).** Mitigation: D10 enforces `Last Updated` advance for flagged entries.
- **Same-file commit ordering.** D2 must land before D4 (both touch `product-brief-drafter/SKILL.md`). D11 must land before D12 (orchestrator references new sub-skill). D3's orchestrator edit (preamble L8) doesn't conflict with D12's Step 3.5 insertion (between L80-82); land D3 first to be safe.
- **D8 template diff size.** Two new fields (`may-invalidate`, `Visual contract`) + drop AC reference — single coordinated edit per A4.

## Out of scope for this plan
- Skill rename (locked HARD DECISION)
- Automated visual-diff
- Multi-file mockups, JS prototypes
- Cross-repo registry
- Backporting brief sections to historical briefs
- Adding clarify prompts beyond D6/D7

## Final steps on approval
1. Save execution plan → `docs/strategic-implementation/2026-04-30-outcome-first-and-mockups/execution-plan.md`
2. Exit plan mode
3. Invoke `strategic-implementation:executing-plans` with execution plan path, feature folder path, autonomy=auto
