# Simplify report 01 — spec-user-first-and-leakage-review
_Target ref: `7a10664~1..6bde148` (my three commits) · Date: 2026-05-17 · Mode: read-fallback_

## Summary

- Files scanned (in-repo): 4 docs (feature folder) — no source.
- Files scanned (out-of-tree plugin cache, manual pass): 4
  - `skills/product-brief-drafter/SKILL.md` (edited)
  - `agents/user-validation.md` (new)
  - `agents/alignment.md` (edited)
  - `skills/review/SKILL.md` (edited)
  - `skills/strategic-implementation/SKILL.md` (one-sentence edit)
- Findings: 1 (high: 0, med: 0, low: 1)
- Categories: reuse-miss 0, dead-code 0, comment-hygiene 0, shape/naming 1

## Notes on scope

This feature's deliverable files live in `~/.claude/plugins/cache/wayneliuq/strategic-implementation/3.3.0/` — outside this axiph repo's git tree. `git diff <merge-base>...HEAD` for the in-repo commits returns only feature-folder docs (plan / checkpoint / validation log), which are not source. Out-of-tree plugin edits were read manually for this pass.

`mcp__code-review-graph__list_graph_stats_tool` would only cover the axiph codebase — the plugin cache is not graphed. Falling back to file-read inspection.

## Findings

### F-01 — shape/naming — low — Leakage gate prompt inlined as ~50-line block string inside drafter SKILL.md
**File:** `skills/product-brief-drafter/SKILL.md:110-155` (out-of-tree)
**Symbol / region:** The inline prompt block in `## Leakage gate (both modes)`.
**Why:** The Leakage gate's inline prompt is a long blockquote (~50 lines) inside a markdown skill file. Existing convention in this plugin is that long sub-agent prompts live in `agents/<name>.md` files (e.g., `alignment.md`, `simplify.md`, `tests.md`, the new `user-validation.md`). The brief's HARD DECISION explicitly chose "no standalone agent file" to keep the leakage reviewer cheap to maintain (one model-class override at call site, no plugin frontmatter assumption); simplify's earlier ALTERNATIVE adopted this. So this is shape divergence by design, not by accident. It is recorded here for visibility — if the prompt grows again (e.g., to add per-allowed-altitude examples), promote to `agents/leakage-reviewer.md` then.
**Suggested action:** Defer. Re-evaluate if the inline prompt grows past ~80 lines or accumulates examples that would be easier to maintain in a dedicated file.

<!-- pm-disposition: -->

## Notes on what was NOT flagged

- **Mirroring `alignment.md` structure in `user-validation.md`.** Deliberate structural parallelism (Adversarial stance / Scope / Do not review / Output schema / Escalation triggers / Processing learnings). Not a reuse miss — the agent file convention is exactly this shape.
- **PMF in alignment's "Do not review" line.** The word "PMF" still appears, but only in a now-cedes-to-user-validation context. Verified intentional.
- **`pmf` as a dimension string reused in user-validation's flag enum.** This is intentional semantic reassignment, documented in the plan's ED3 consumer audit. Not dead code.
- **The three-line addition to `strategic-implementation/SKILL.md` Step 4 narrative.** Minimal, single-sentence; no simplify dimension applies.
