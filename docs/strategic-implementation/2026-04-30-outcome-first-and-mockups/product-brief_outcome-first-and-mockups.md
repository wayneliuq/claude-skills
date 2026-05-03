# Product Brief: Outcome-First Brief + Optional UI Mockup + Doc Registry
_Slug: outcome-first-and-mockups · Date: 2026-04-30 · Autonomy: auto_

## 1. Working backwards (≤5 sentences, release-note voice)
> The strategic-implementation skill now leads every feature with an outside-in outcome paragraph: a one-paragraph "if this shipped tomorrow" announcement that forces the PM and drafter to articulate what the change *feels* like before any planning. Clarify is updated to prime that paragraph at the cheapest possible moment — it asks the PM directly for the one-sentence outcome and the outside-observable success signal, and plays the outcome back in their words before handing off to the drafter. The brief itself is reorganized along that spine — the standalone "Acceptance criteria" section is gone (each deliverable's validation method *is* its acceptance test), and a new "Success signal" section names the observable outcome distinct from any single deliverable. For features touching the UI in non-trivial ways, the workflow now offers an optional HTML mockup phase between brief approval and execution planning, gated by an explicit pre-flight scope estimate the PM confirms; the mockup uses the repo's existing design tokens and becomes the visual contract the plan and implementation must match. Finally, the skill now maintains a per-repo documentation registry — populated at the moment a doc is first mentioned in clarify (with `covers` and `update-trigger` fields captured then), read by later phases for context, flagged for update where this work may invalidate it, and refreshed as part of the deliverable's atomic commit.

## 2. What the user does / sees
| # | Deliverable (user-observable) | Validation |
|---|---|---|
| D1 | Brief template is reorganized along the working-backwards spine: 7 sections — Working-backwards · What the user does/sees · Success signal · Boundaries · Decisions · Risks · References & revision log. The standalone "Acceptance criteria" section is removed | `cli`: regenerate a brief on a sample request; section count is 7, names match, no separate Acceptance Criteria heading |
| D2 | Brief includes a "Working backwards" section at the top: ≤5 sentences, release-note voice, written before any deliverables are listed | `cli`: regenerate brief; section is present, ≤5 sentences, voice check (no "we will," uses "the X now does Y") |
| D3 | Brief includes an explicit "Success signal" section, distinct from per-deliverable validation — names a thing observable from outside the system (a query, a behavior, a metric) | `cli`: regenerate brief; section names an outside-observable signal, not an internal state or deliverable restatement |
| D4 | Brief's "Boundaries" section has three rows: In scope / Out of scope / Anti-goals. Anti-goals are philosophy-level ("we deliberately will not") not deferred items | `cli`: regenerate brief; all three rows present, anti-goals contain at least one philosophy-level statement |
| D5 | Skill description and orchestrator preamble lead with "outcome-first" framing | `cli`: read updated SKILL.md files; description and preamble both name "outcome-first" as the headline principle. Skill name `strategic-implementation` is unchanged |
| D6 | New `ui-mockup` sub-skill at `plugins/strategic-implementation/skills/ui-mockup/SKILL.md`, wired into the orchestrator between brief approval and execution-plan invocation | `cli`: invoke skill on a sample UI feature; orchestrator emits the pre-flight scope estimate and waits for explicit confirmation |
| D7 | When orchestrator detects non-trivial UI scope in an approved brief, it emits a pre-flight estimate (`~N lines, small/medium/large, reason: <trigger>`) and waits for explicit PM confirmation before invoking ui-mockup | `preview`: run end-to-end on a sample brief that introduces a new screen; verify prompt fires with estimate and requires confirmation |
| D8 | ui-mockup writes a single static `mockup.html` to the feature folder, discovers and reuses the repo's existing design tokens (CSS variables → Tailwind config → theme file), and falls back to a documented neutral palette if none exist. No JS framework, no build step | `preview`: open generated `mockup.html` in browser; visual check — uses repo styles where present, neutral fallback otherwise |
| D9 | PM revises mockup via `<!-- pm: ... -->` comments embedded in the HTML or in a sibling `mockup-feedback.md`; drafter applies and removes them, same pattern as brief revision | `cli`: add a `<!-- pm: -->` comment, invoke revise mode, comment is addressed and removed |
| D10 | If mockup iteration reveals the brief is wrong, the workflow loops back to brief revision (not forward to plan); ui-mockup detects this case and surfaces the conflict | `preview`: simulate a mockup change that contradicts a brief deliverable; verify orchestrator routes back to brief revision |
| D11 | Execution plan and implementation cite the approved `mockup.html` as the visual contract for each UI deliverable; post-execution regression-check includes a manual visual-diff step against the mockup | `cli`: inspect a generated execution plan for a UI feature; mockup path is referenced in each UI deliverable's row |
| D12 | Per-repo documentation registry exists at `docs/strategic-implementation/documentation-registry.md` — a single table tracking: doc path, what it covers, last-updated date, update-trigger conditions, owning area. Created if missing on first run | `cli`: invoke skill in a repo without a registry; file is created with the documented schema and a header explaining its purpose |
| D13 | `clarify` reads the registry to ground its questions; when PM points out a doc at any phase ("the auth flow is in /docs/auth.md"), the skill writes/updates a registry row inline rather than only capturing it in the current brief | `cli`: in a clarify pass, mention a new doc path; verify registry gains a row with non-empty "covers" and "update-trigger" fields |
| D14 | `execution-plan` identifies which registry entries this work may invalidate, marks them per-deliverable, and surfaces the list to the PM in the plan | `cli`: generate a plan for a feature touching an area covered by a registry entry; plan shows the entry as "may need update" |
| D15 | `executing-plans` prompts to update the tracked doc as part of the deliverable when the deliverable touches a flagged registry entry; the doc update lands in the same atomic commit | `cli`: run a deliverable flagged in D14; verify commit includes both the code change and the doc update |
| D16 | `post-execution` regression-check verifies flagged registry entries were updated (last-updated date moved forward); flags any that weren't and asks before closing the cycle | `cli`: complete a feature where a flagged doc was not updated; regression-check surfaces the gap |
| D17 | All skills that write files (`product-brief-drafter`, `executing-plans`, `post-execution`) check at entry whether plan mode is active; if so, they exit plan mode before writing. Orchestrator also checks before invoking each | `cli`: invoke brief drafter while plan mode is active; verify plan mode exits before any file is written, with a one-line announcement |
| D18 | `clarify` Step 3 prompts the PM with a working-backwards question: *"If this shipped tomorrow, what's the one-sentence change to the user's life?"* If PM cannot answer in one sentence, clarify flags it and proceeds — the drafter sees the flag and writes "Working backwards: TBD — open question" rather than fabricating one | `cli`: run clarify on a sample request; verify the prompt fires and the answer (or its absence) is in the clarify output passed to the drafter |
| D19 | `clarify` Step 3 prompts the PM for the success signal: *"How would you know it worked from outside — a query, a behavior, a metric? Not 'the deliverable shipped.'"* If PM has no answer, the brief Section 3 gets "Success signal: TBD — open question" rather than being silently absent | `cli`: run clarify; verify prompt fires and PM's answer (or "TBD") propagates to the brief's Success signal section |
| D20 | When PM names a doc anywhere in clarify, clarify asks two follow-ups inline: *"what does it cover (one line)?"* and *"what kinds of changes would make it stale?"* — the answers populate that doc's row in the documentation registry at point of mention, not later | `cli`: in a clarify pass, mention a new doc path; verify follow-ups fire and registry row gains non-empty `covers` and `update-trigger` fields immediately |
| D21 | `clarify` Step 4 (Confirm) plays the outcome back in the PM's own words before handing off: *"To confirm — when X happens for user Y, you'll consider this shipped."* PM confirms or corrects in one line. The confirmed phrasing is what the drafter receives | `cli`: complete a clarify pass; verify the playback line is emitted and the confirmed phrasing appears verbatim in the brief's Working-backwards section |

## 3. Success signal
A PM running the skill on a non-trivial UI feature sees, in order: clarify asking the one-sentence outcome question and the success-signal question, clarify playing back the outcome in their words before drafting, a brief whose Working-backwards paragraph echoes that confirmed phrasing, a Success signal section that uses their answer (or explicitly says "TBD"), anti-goals that aren't just deferred items, a pre-flight mockup-scope prompt with an estimate, an HTML mockup styled with repo tokens, a plan that references the mockup file, and — at execution time — a prompt to update the relevant registry-tracked documentation as part of the deliverable, in the same commit. None of these requires the PM to remember a step the skill should be tracking.

## 4. Boundaries
**In scope:**
- Brief template reorganization (7-section spine, drop standalone Acceptance Criteria, add Working-backwards + Success signal + Anti-goals)
- Clarify Step 3/4 changes: working-backwards prompt, success-signal prompt, doc-registry capture at point of mention, outcome playback before handoff
- New `ui-mockup` sub-skill + orchestrator wiring + pre-flight scope estimate
- Per-repo documentation registry file + integrations into clarify, execution-plan, executing-plans, post-execution
- Plan-mode exit checks in all file-writing sub-skills + orchestrator
- Description/README updates leading with outcome-first

**Out of scope:**
- Renaming the skill
- Automating visual-diff between mockup and shipped UI (manual step in regression-check)
- Mockup iteration via direct PM HTML edits (only `<!-- pm: -->` comments / sibling feedback file)
- Multi-file mockups, JS-driven prototypes, design-tool integration (Figma, etc.)
- Backporting new brief sections into already-approved briefs
- A new sub-skill dedicated to the documentation registry — the registry is a file; existing skills interact with it via small sections in their SKILL.md
- Cross-repo registry / global registry — registry is per-repo, lives in the repo

**Anti-goals (philosophy-level — we deliberately will not):**
- Build a mockup phase that becomes the most expensive phase of the workflow. The mockup exists because it is cheaper than implementation; if it ever isn't, it has failed its purpose.
- Make any of the new brief sections mandatory for the fast-path. Fast-path stays one-page.
- Let the mockup become a binding spec the PM can't escape. If iteration reveals the brief is wrong, the workflow always loops back to brief revision rather than forcing the PM to live with a flawed plan.
- Add fields to the brief just because successful companies have them. Each addition must earn its place by catching a class of misalignment the current brief misses.
- Treat the documentation registry as documentation itself. The registry is an index, not a knowledge base — if a registry entry's "covers" field grows past one line, that content belongs in the doc, not the registry.
- Spawn a sub-skill for every new responsibility. Lightweight cross-cutting concerns (like the registry) live as sections in existing skills.
- Add more than three new prompts to clarify. Clarify is one pass; each new question must earn its place by feeding a specific downstream artifact. JTBD, anti-goals, and appetite questions are all tempting but redundant with existing brief sections — they will not be added.
- Block the workflow when the PM can't answer a clarify prompt. Inability to answer is itself signal — propagated as `TBD — open question` to the brief, not a gate.

## 5. Decisions
| Decision | Choice | Status |
|---|---|---|
| Skill rename | Keep `strategic-implementation`; lead description/preamble with "outcome-first" | `[HARD DECISION]` |
| Brief reorganization | 7-section spine; drop standalone Acceptance Criteria; add Working-backwards + Success signal + Anti-goals | `[HARD DECISION]` |
| Mockup phase placement | Between brief approval and execution-plan invocation | `[HARD DECISION]` |
| Mockup gating | Explicit PM confirmation after pre-flight scope estimate emitted by orchestrator | `[HARD DECISION]` |
| Mockup format | Single static HTML file, inline CSS, no JS framework, no build step | `[HARD DECISION]` |
| Mockup-vs-brief conflict handling | Loop back to brief revision (not forward to plan) | `[HARD DECISION]` |
| Token cap on mockup | None. Pre-flight estimate orients the PM; mid-flight surprises trigger a flag, not a cancel | `[HARD DECISION]` |
| Documentation registry scope | Per-repo, single file at `docs/strategic-implementation/documentation-registry.md`. No new sub-skill | `[HARD DECISION]` |
| Plan-mode exit checks | Defense-in-depth: orchestrator + every file-writing sub-skill checks at entry | `[HARD DECISION]` |
| Clarify additions | Three new prompts (working-backwards, success-signal, doc-registry capture at mention) + one playback line in Confirm. No JTBD / anti-goals / appetite prompts | `[HARD DECISION]` |
| Unanswerable clarify prompts | Propagate as `TBD — open question` to the brief; never block | `settled` |
| Mockup iteration mechanism | Inline `<!-- pm: -->` comments OR sibling `mockup-feedback.md` | `settled` |
| Trigger criterion for mockup | New screen, ≥2-step flow, or IA change. PM can override either way | `settled` |
| Repo style discovery order | CSS variables → Tailwind config → theme file → neutral fallback (documented) | `settled` |
| Doc registry update timing | Updated as part of the deliverable's atomic commit; verified in post-execution | `settled` |

<!-- HARD DECISION tradeoff tables -->

**Brief reorganization — tradeoffs**
- Keep 8 sections, add new ones additively: smaller diff but redundancy stays (Acceptance Criteria largely restates what deliverables + validation already say).
- Reorganize to 7-section working-backwards spine: tighter, drops redundancy, signals the philosophy in the structure itself. **Chosen.**

**Documentation registry scope — tradeoffs**
- Per-feature (lives in feature folder): no persistence, gets recreated every cycle, no memory across features.
- Per-repo (single file at known path): persists, becomes a cumulative map of the codebase's docs. PM's mental model of "where docs live" is preserved across cycles. **Chosen.**
- Cross-repo / global: out of scope — different repos have different docs.

**Plan-mode exit checks — tradeoffs**
- Single check at orchestrator: simple but fails if a sub-skill is invoked directly by the PM (bypassing orchestrator).
- Defense-in-depth, every file-writing sub-skill checks at entry: belt-and-suspenders; small per-skill cost; robust to direct invocation. **Chosen.**

**Clarify additions — tradeoffs**
- Add JTBD + working-backwards + success-signal + anti-goals + appetite questions: comprehensive but bloats clarify into a multi-pass interview; many questions duplicate brief sections.
- Three targeted prompts (working-backwards, success-signal, doc-registry capture at mention) + one playback line: each feeds a specific downstream artifact (Brief Section 1, Brief Section 3, Registry rows, Brief Section 1 confirmed phrasing). 30-second cost in clarify, removes guesswork in drafter. **Chosen.**
- No additions: drafter has to infer outcome and success signal from feature descriptions; brief Section 1 reads like rephrased deliverables.

## 6. Risks & unknowns
- **Trigger ambiguity at the edges.** "New screen" vs "modal that's basically a screen" will be argued. Mitigation: PM override on either side; the prompt makes the trigger reason explicit.
- **Repo style discovery is fragile.** Mixed-convention repos (Tailwind + custom CSS) may produce off-looking mockups. Mitigation: skill names what it found and what it fell back to; PM sees this in the pre-flight estimate.
- **Registry decay.** If the registry isn't kept honest, its rows become lies. Mitigation: post-execution verifies last-updated dates moved forward for flagged entries; stale-flagging surfaces aging entries.
- **PMs who don't comment in HTML.** Mitigation: skill accepts chat feedback too — captured to `mockup-feedback.md` and applied the same way.
- **Mockup drift from shipped UI.** No automated visual diff in v1. Accepted risk; flagged for future automation.
- **Plan-mode check fires when it shouldn't.** If a sub-skill is *meant* to run inside plan mode (`execution-plan` is), the check must distinguish. Mitigation: the check is per-skill — only file-writing skills exit plan mode; `execution-plan` keeps its plan-mode entry.

## 7. References & revision log

**Document registry entries this work touches:**
- The registry itself is a deliverable here (D12); first row in it will track this brief's location.
- `plugins/strategic-implementation/skills/strategic-implementation/SKILL.md` — orchestrator (touched by D5, D7, D17)
- `plugins/strategic-implementation/skills/product-brief-drafter/SKILL.md` — brief template (touched by D1–D4, D17)
- `plugins/strategic-implementation/skills/clarify/SKILL.md` — clarify (touched by D13, D18, D19, D20, D21)
- `plugins/strategic-implementation/skills/execution-plan/SKILL.md` — plan drafting (touched by D11, D14)
- `plugins/strategic-implementation/skills/executing-plans/SKILL.md` — execution (touched by D15, D17)
- `plugins/strategic-implementation/skills/post-execution/SKILL.md` — regression-check (touched by D11, D16, D17)
- New: `plugins/strategic-implementation/skills/ui-mockup/SKILL.md` (D6, D8, D9, D10)
- `README.md` — outcome-first framing in description (D5)

**Other doc references:**
- Architecture: the seven existing sub-skill SKILL.md files (above)
- UX/PMF: n/a — skill change has no end-user UI surface
- Security policy: none
- Schema/ERD: n/a

**Revision log:**
- v0.1 · 2026-04-30 · initial draft
- v0.2 · 2026-05-01 · reorganized to working-backwards 7-section spine; dropped standalone Acceptance Criteria; added doc registry deliverables (D12–D16); added plan-mode exit checks (D17); added registry/plan-mode hard decisions and tradeoff tables
- v0.3 · 2026-05-01 · added clarify deliverables D18–D21 (working-backwards prompt, success-signal prompt, doc-registry capture at point of mention, outcome playback in Confirm); added "Clarify additions" hard decision and tradeoff table; added "Unanswerable clarify prompts → TBD" settled decision; added two new anti-goals (≤3 new clarify prompts; never block on unanswerable prompts); updated Working-backwards and Success signal sections to reflect clarify's role
