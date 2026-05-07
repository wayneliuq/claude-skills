# Simplify report 01 — context-mode-and-simplify
_Target ref: `main...HEAD` · Date: 2026-05-07 · Mode: read-fallback (graph empty for this meta-repo, 0 nodes)_

## Summary
- Files scanned: 6 source files (5 SKILL.md, 1 bash script) + 5 docs files (excluded from review)
- Findings: 3 (high: 0, med: 1, low: 2)
- Categories: reuse-miss 0, dead-code 0, comment-hygiene 1, shape/naming 2

## Findings

### F-01 — shape/naming — med — Tone discipline block duplicated across 5 SKILL.md
**File:** `plugins/strategic-implementation/skills/{clarify,execution-plan,executing-plans,post-execution,simplify}/SKILL.md` (each `## Tone discipline` section)
**Symbol / region:** the 5-line shared block (terse-output rule + carve-outs)
**Why:** literal duplication of a 5-line block across 5 files. In a code repo this would be a refactor candidate. Acknowledged in the execution plan as a HARD DECISION ("duplicating a 5-line block in 5 files is cheaper than introducing an include mechanism the harness doesn't support natively"). Flagging anyway so any future skill-template mechanism (if it lands) is a clean candidate to dedupe against.
**Suggested action:** none for v1; revisit if/when the plugin gains a shared-prompt include or template mechanism.

<!-- pm-disposition: defer -->

### F-02 — shape/naming — low — `rtk` jq aggregation path uses placeholder fallback (`?`)
**File:** `plugins/strategic-implementation/scripts/token-report.sh:107-126`
**Symbol / region:** the `RTK_SECTION` jq filter
**Why:** the jq path uses `.total_saved // .saved // "?"` and similar. When `rtk gain --format json` returns a shape that doesn't match either, the section fills with `?` placeholders rather than a useful number. Functional (graceful), but cosmetic. The brief's HARD DECISION says the script must be deterministic and never spend model tokens — that holds — but a follow-up should pin the actual rtk output schema and update the jq path.
**Suggested action:** follow-up: capture a real `rtk gain --format json` output sample, update the jq path to match, drop the `?` fallback.

<!-- pm-disposition: defer -->

### F-03 — comment-hygiene — low — schema-pin comment is good but undocumented bump procedure
**File:** `plugins/strategic-implementation/scripts/token-report.sh:11-14`
**Symbol / region:** `TRANSCRIPT_FORMAT_VERSION="v1 (2026-05)"`
**Why:** the format-pin comment is right and necessary, but doesn't document **how to bump it** when Claude Code's JSONL schema changes. Future maintainer would have to infer.
**Suggested action:** add one-line procedure: "to bump: capture a fresh sample, diff against the jq paths used here, update version + paths in same commit."

<!-- pm-disposition: defer -->

---

_Generated manually as Step 7a of post-execution because the freshly-written `simplify` skill is not loadable mid-session. The skill's logic was applied by hand; future runs (after plugin reload) will produce this artifact via the skill itself._
