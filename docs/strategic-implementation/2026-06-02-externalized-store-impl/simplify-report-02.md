# Simplify report 02 — externalized-store-impl (final pass)
_Target ref: `3d5e4c4...HEAD` (full feature diff) · Date: 2026-06-02 · Mode: graph-aware + read_

## Summary
- Files scanned: store scripts (common/bootstrap/store/cache.sh) + setup.sh/hooks.json + 8 SKILL.md
- Findings: 1 (high: 0, med: 0, low: 1)
- Categories: reuse-miss 0, dead-code 0, comment-hygiene 0, shape/naming 1

## Findings

### F-01 — shape/naming — low — identical routing-convention block duplicated across 8 SKILL.md stages
**File:** `plugins/strategic-implementation/skills/*/SKILL.md` (the appended "Record routing — externalized artifact store" section)
**Why:** the same ~10-line convention is repeated verbatim in 8 stages rather than referenced from one place.
**Suggested action:** keep — this is the **intentional** literal-repeated-prose decision endorsed at plan review (simplify ALTERNATIVE): 8 echoes are simpler to grep-verify and survive per-skill context loading better than a new include/indirection mechanism. Not a defect.

<!-- pm-disposition: dismiss -->

## Notes
Mid-execution report-01's findings all resolved: F-01 (`si_locator_exists` unused) is now wired into `store.sh put`; `cache.sh refresh` gained its caller via the routing convention; `--capabilities` is a deliberate external surface. No dead code, no reuse misses, comment hygiene clean (comments explain gh quirks / security intent). The four store scripts follow the `scripts/memory/` house style (shebang, `set -uo pipefail`, `HERE=`, degrade-to-silence).
