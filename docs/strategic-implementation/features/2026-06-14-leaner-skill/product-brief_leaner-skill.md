# Product Brief: Leaner skill — prune drift machinery, add minimalism + taste discipline

_Date: 2026-06-14 · Target version: strategic-implementation 4.3.0 · PM: wliu_

## Problem

The skill carries an obsolete self-management subsystem (long-running-session drift
prevention) that modern models no longer need, it tends to **add** architectural bloat
rather than resist it, and its UI mockups/frontend output read as generic "AI slop."
Three peer skills (ponytail, addyosmani/agent-skills, taste-skill) each hold a small,
proven device worth grafting in — but most of their surface is duplicate or conflicts
with this skill's philosophy and must be rejected.

## Target user

A maintainer/PM running a feature through strategic-implementation end-to-end. They
should get a *smaller, sharper* skill: less machinery, plans that resist over-building,
and frontend output that doesn't look auto-generated.

## Success signal (outcome-level)

Running a representative feature through the skill after this change, the maintainer
observes all of:
1. No `<active-goal>` / chapter / turn-cap machinery fires, and **no per-turn haiku
   goal-evaluator call occurs** — while the simplify, error-loop, thrash-pause, and
   deviation-surface breakers still fire on their behavioral triggers.
2. The execution-plan draft **and** the simplify review both apply the YAGNI hierarchy
   and the review returns named **deletion candidates**.
3. A freshly generated `mockup.html` contains **zero** of the listed AI-tells
   (em-dashes, eyebrow over-use, repeated section layouts, fake-precise numbers, scroll
   cues, version-label tells, lorem filler).
4. The plugin still loads: `hooks.json` is valid JSON, every hook script passes
   `bash -n`, and the Stop hook returns valid JSON with the goal-evaluator removed.

**Net-LOC guardrail:** the change ships *less* than today (deletion-dominant overall).

## Deliverables (outcome contracts)

### D1 — Drift/goal machinery removed; behavioral breakers intact
The whole long-running-session drift subsystem is gone: `<active-goal>` blocks, the
haiku goal-evaluator Stop prompt, chapter rollover, turn-cap, and the touched-file
"drift" framing. The simplify-counter, error-loop, thrash-pause, deviation-surface, and
per-deliverable atomic gating are untouched.
- **How a user verifies:** (1) `jq . hooks.json` succeeds and contains no goal-evaluator
  prompt hook; (2) `grep -rn "active-goal\|chapter\|turn-cap\|pending_chapter_rotation"`
  over the plugin returns nothing; (3) `bash -n` passes on every hook script; (4) a
  D-commit still flips `pending_simplify` after the threshold; (5) Stop orchestrator
  returns `{"ok":true}` when no behavioral flag is pending.

### D2 — Plan drafting enforces "does this need to exist?"
`execution-plan` gains a first authoring rule applying ponytail's hierarchy
(YAGNI → stdlib → native → existing dep → one line → minimum) per deliverable/abstraction.
- **How a user verifies:** open `execution-plan/SKILL.md`; rule "0" precedes deliverable
  authoring and names the full hierarchy. A drafted plan visibly justifies each new
  abstraction against it.

### D3 — Simplify review returns deletion candidates against the hierarchy
The `simplify` agent scores the plan against the explicit ponytail hierarchy and returns
**named deletion candidates**, not prose flags.
- **How a user verifies:** open `agents/simplify.md`; scope/output reference the hierarchy
  and a deletion-candidate list. A review run on a padded plan names specific deliverables
  to drop.

### D4 — Two anti-rationalization tables at the highest-skip gates
Exactly two "excuse → rebuttal" tables: validation-method-honesty and consumer-audit-on-
shape-change. No third.
- **How a user verifies:** the two tables exist at those gates; no other gate gains one.

### D5 — Frontend taste discipline, fully inside this skill
A shared `agents/frontend-quality.md` owns the full taste ruleset. `ui-mockup` references
the **slim** subset (legibility/IA, throwaway-safe); `frontend-engineer` references the
**rich** subset (pixel quality, motion, font/color discipline). No dependency on the
`frontend-design` skill.
- **How a user verifies:** `frontend-quality.md` exists in-plugin; ui-mockup cites the
  slim rows, frontend-engineer the rich rows; a generated mockup passes the D-level
  anti-tell check (success signal #3).

### D6 — Docs + version aligned
README, `plugin.json` version (→ 4.3.0) and its description string, and any registry
entry invalidated by D1–D5 are updated in the same change.
- **How a user verifies:** README no longer describes drift/chapter/turn-cap behavior;
  `plugin.json` reads 4.3.0 and its description drops "chapter rotation, goal evaluation";
  `documentation-registry.md` has no stale entry pointing at removed machinery.

### D7 — Open-source inspiration acknowledged
The three peer skills whose ideas were incorporated (ponytail, addyosmani/agent-skills,
taste-skill) are credited in the README's Acknowledgments section, in the established
"import the high-leverage idea, leave the heavyweight stack behind" format — naming the
specific idea borrowed and the heavyweight scope deliberately left out.
- **How a user verifies:** README has an "Acknowledgments — inspirations for v4.3.0"
  subsection naming all three repos with links, the specific idea taken from each, and
  what was rejected.

## Scope boundary

**In:** the six deliverables above, confined to the strategic-implementation plugin.

**Out / anti-goals:**
- Deprecating or deleting the `frontend-design` skill (separate, later).
- Any change to the external artifact store, memory subsystem, or learnings-benchmark.
- Adopting addyosmani's change-sizing norm, autonomous mode, or doubt-driven protocol.
- Adopting taste-skill's motion/GSAP/dials/design-system machinery *into the mockup*.

## Hard decisions

| # | Decision |
|---|---|
| HD1 | **No new agents, skills, or commands.** Every change sharpens an existing surface. |
| HD2 | **No LOC budgets / change-sizing gates.** Preserve "fitness is a gate, not size." (Rejects addyosmani's ~100-line norm.) |
| HD3 | **All frontend quality lives inside strategic-implementation.** No reference to `frontend-design`. |
| HD4 | **ui-mockup stays throwaway.** Slim anti-slop only; no motion/GSAP/dials/design-system table in the mockup path. |
| HD5 | **Anti-rationalization tables capped at 2.** |
| HD6 | **Behavioral breakers are preserved** (error-loop, thrash-pause, deviation-surface, per-deliverable gating). turn-cap is NOT one of these — it is pruned. |

## Document references
- Source skill: `plugins/strategic-implementation/`
- Peer skills: ponytail (DietrichGebert), agent-skills (addyosmani), taste-skill (Leonxlnx)
- Prior brainstorm: this conversation (scope locked 2026-06-14)
