# Session Plan: Skill Best-Practice Additions
_Implements: Implementation Plan § Session 4_
_Date: 2026-04-06_

## Goal
Apply four targeted best-practice improvements to skills: clarify fast-skip, reviser trigger precision, post-mortem Step 7 compression, and implementation-drafter subsection feedback format.

## Pre-conditions
- [ ] Prior sessions complete: Session 2 complete — `post-mortem/SKILL.md` has Session 2 file surfacing changes in Step 10 (verify before editing)
- [ ] Docs available: implementation plan at `docs/strategic-implementation/2026-04-05-plugin-skills-agents-improvement/implementation-guide.md`
- [ ] Read `plugins/strategic-implementation/skills/post-mortem/SKILL.md` before editing Step 7 and confirm both (a) Step 10 file surfacing blocks are intact and (b) count actual lines in the Step 7 block to determine whether any compression is needed before writing

## Steps

1. Add fast-skip path to `clarify/SKILL.md` [parallel group: A]
   - File: `plugins/strategic-implementation/skills/clarify/SKILL.md`
   - What: Between Step 1 and Step 2, insert a conditional block: if the request is fully specified with no ambiguity, skip to Step 4 and announce "The request is fully specified. Proceeding to scope assessment." Include the word "fabricate" (or equivalent — "invent", "manufacture") to prohibit inventing questions just to fill the format. The block must appear immediately before the `## Step 2` heading. Additionally, **remove** the existing escape clause at the bottom of Step 3 ("If everything is clear and no questions are needed, skip this step and say so explicitly") — the new pre-Step-2 block supersedes it and having two fast-skip paths for the same condition creates ambiguity.

2. Restructure Step 11 opening in `implementation-reviser/SKILL.md` [parallel group: A]
   - File: `plugins/strategic-implementation/skills/implementation-reviser/SKILL.md`
   - What: In Step 11, replace the opening sentence "If this revision round made changes that significantly restructure the spec — specifically, if two or more of the following are true:" with "If two or more of the following are true in this revision round:". The phrase "significantly restructure" must not appear anywhere in Step 11 after this change. The four bullet conditions and the `Then: silently re-run...` paragraph remain unchanged.

3. Compress Step 7 in `post-mortem/SKILL.md` [parallel group: A]
   - File: `plugins/strategic-implementation/skills/post-mortem/SKILL.md`
   - What: First, count the lines in the Step 7 block (from `## Step 7` to `## Step 8`, excluding the heading line; the `---` separator is not counted as content). If already ≤5 lines, skip this edit and log "no change required." If > 5 lines, rewrite to ≤5 lines while preserving both behavioral rules exactly: **(1)** extract 2–3 keywords from each deviation's "What actually happened" and search across all other `session-*-log.md` files; **(2)** if a pattern appears in 2+ other sessions, flag it as a potential multi-session pattern — advisory only, promotion to `#multi-session` requires explicit user confirmation. Do NOT touch Step 10 or any other step.

4. Add per-subsection feedback slots to Section 4 template in `implementation-drafter/SKILL.md` [parallel group: A]
   - File: `plugins/strategic-implementation/skills/implementation-drafter/SKILL.md`
   - What: In the Document Format template block (the fenced markdown block), locate Section 4 (`## 4. Detailed Specification`). Change both `### [Component or Concern Name]` and `### [Next component or concern]` headings to `#### [Component or Concern Name]` and `#### [Next component or concern]`. After each `####` subsection's content block (the field lines), add `> **Feedback:** _(leave blank, or type your thoughts, corrections, or questions about this section)_` before the next `####` heading. Every `####` heading must be matched by exactly one `> **Feedback:**` slot using this exact placeholder text. Then **remove** the section-level `> **Feedback:**` slot that currently closes Section 4 — each subsection now carries its own slot, making the section-level slot redundant.

## Deliverables & Tests
- [ ] Deliverable: `clarify/SKILL.md` has explicit fast-skip path; Step 3 escape clause removed
  Test: Read `clarify/SKILL.md` — text immediately before Step 2 contains a condition: if the request leaves nothing ambiguous, skip to Step 4 and announce "The request is fully specified. Proceeding to scope assessment." The word "fabricate" or equivalent appears in the instruction. `grep "no questions are needed" plugins/strategic-implementation/skills/clarify/SKILL.md` returns no results (Step 3 escape clause removed).

- [ ] Deliverable: `implementation-reviser/SKILL.md` Step 11 leads with count-based trigger
  Test: Read Step 11 — the opening sentence is "If two or more of the following are true in this revision round:" (or equivalent count-first phrasing). `grep "significantly restructure" plugins/strategic-implementation/skills/implementation-reviser/SKILL.md` returns no results. All four trigger-condition bullets are present following the opening sentence.

- [ ] Deliverable: `post-mortem/SKILL.md` Step 7 is ≤5 lines (or unchanged if already compliant)
  Test: Count lines in the Step 7 block (from `## Step 7` heading to `## Step 8` heading, excluding the heading line; the `---` separator is not counted as content) — ≤5 lines. Step 10 regression check: `grep "_saved to" plugins/strategic-implementation/skills/post-mortem/SKILL.md` returns ≥2 matches (the two write-block announcements added in Session 2).

- [ ] Deliverable: `implementation-drafter/SKILL.md` document format has `> **Feedback:**` slot after each `####` subsection in Section 4; section-level slot removed
  Test: Read the document format template in `implementation-drafter/SKILL.md` — the Section 4 block contains ≥2 `####` example headings; every `####` heading is followed by a `> **Feedback:** _(leave blank...)_` line before the next `####` or `---`; count of `####` headings exactly matches count of `> **Feedback:**` slots within that template block; no standalone section-level `> **Feedback:**` slot remains at the close of Section 4.

## Constraints
- Target: ≤ ~1000 LOC edited or written this session
- This is the final session — do not implement anything beyond what is listed here
- Flag any unexpected scope expansion to user before proceeding
- If a step reveals a pre-condition is not met: stop and surface to user before continuing
