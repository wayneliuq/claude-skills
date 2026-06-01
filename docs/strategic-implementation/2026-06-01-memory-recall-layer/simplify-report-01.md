# Simplify report 01 — memory-recall-layer
_Target ref: `main...HEAD` · Date: 2026-06-01 · Mode: read-fallback (FLAG: code-review-graph unavailable; Python/markdown not graph-indexed anyway)_

## Summary
- Files scanned: 9 (6 new under `scripts/memory/`, 2 skill edits, README/registry)
- Findings: 3 (high: 0, med: 0, low: 3)
- Categories: reuse-miss 0, dead-code 0, comment-hygiene 1, shape/naming 2

No reuse-miss (the plugin had no prior Python; `parse_frontmatter` reuses nothing because bash+jq is the only precedent and is not callable from Python). No dead code: `test_build_index.py` exercises the full `ingest`→`build_index` path end-to-end and all module functions are on that path (the quick ref-count grep reported false zeros due to name truncation; manual trace confirms each is reached).

## Findings

### F-01 — shape/naming — low — `flag` record type ingested but absent from the manifest
**File:** `plugins/strategic-implementation/scripts/memory/ingest.py` (`_block_type`) + `MEMORY-DOCTYPES.md`
**Symbol / region:** `_block_type()` returns `"flag"` for `## FLAG (mocked-seam)` blocks; the `MEMORY-DOCTYPES.md` include table lists every other type but not `flag`.
**Why:** code/manifest divergence. `flag` (mocked-seam markers) is low recall value and undocumented as an indexed type, so the readable manifest under-describes what the index actually contains.
**Suggested action:** either add a `flag` row to the manifest table, or drop `flag` from `_block_type` (mocked-seam markers are post-exec signals, not precedent). Lean drop.

<!-- pm-disposition: defer -->

### F-02 — comment-hygiene — low — verbose module/inline rationale comments
**File:** `plugins/strategic-implementation/scripts/memory/ingest.py:1-40`, `build_index.py:1-20`
**Symbol / region:** module docstrings + several policy-rationale comments.
**Why:** comment volume is high relative to a first read; some lines restate adjacent code. Counterpoint: most encode the *why* (selection policy, no-vec0 rationale, generation-aware status) that the brief/plan treat as load-bearing, so trimming risks losing design intent.
**Suggested action:** keep the policy rationale; trim only the 2-3 lines that restate the next statement. Dismiss-eligible.

<!-- pm-disposition: dismiss -->

### F-03 — shape/naming — low — Phase-1b placeholder columns written in Phase-1a
**File:** `plugins/strategic-implementation/scripts/memory/build_index.py` (`index_meta` insert of empty `embedding_model_id`/`embedding_dim`)
**Symbol / region:** `index_meta` rows seeded empty now.
**Why:** mild speculative-for-current-phase. Justified: it lets D6 attach the vector leg without a schema migration (the D2 consumer audit explicitly promised "no migration"), so the placeholder is intentional forward-compatibility, not dead weight.
**Suggested action:** keep as-is; documented rationale. Dismiss.

<!-- pm-disposition: dismiss -->
