# Simplify report 02 — memory-recall-layer (final pass)
_Target ref: `main...HEAD` · Date: 2026-06-01 · Mode: read-fallback (FLAG: code-review-graph unavailable; Python not graph-indexed)_

## Summary
- Files scanned: 11 source (6 Python modules, 3 test modules, recall.sh, schema.sql) + skill/doc edits
- Findings: 2 (high: 0, med: 0, low: 2)
- Categories: reuse-miss 1, dead-code 0, comment-hygiene 1, shape/naming 0

Cross-module reuse is good: `load_vec_extension` (build_index) is imported by `recall._vector` rather than duplicated; `_filter_sql` is shared by `_bm25`/`_vector`; `embed_one` wraps `embed`. No dead code — every module function is on a test-exercised path (D2/D3/D5 resident, D6 venv, all green). The report-01 findings F-01 (`flag` type vs manifest) and F-03 (Phase-1b placeholder columns) remain as dispositioned (defer/dismiss); F-02 (comment volume) is unchanged and still dismiss-eligible (policy rationale is load-bearing).

## Findings

### F-04 — reuse-miss — low — `_w` fixture-writer duplicated across two test modules
**File:** `plugins/strategic-implementation/scripts/memory/test_vector.py` (`_w`) vs `test_build_index.py` (`_w`)
**Symbol / region:** identical `def _w(p, text): p.parent.mkdir(...); p.write_text(...)`.
**Why:** `test_recall.py` already imports `make_fixture` from `test_build_index`; `test_vector.py` redefines `_w` instead of importing it. Trivial duplication in test scaffolding (not shipped code).
**Suggested action:** `from test_build_index import _w` in test_vector.py. Low value; defer.

<!-- pm-disposition: defer -->

### F-05 — comment-hygiene — low — carried from report-01 F-02 (module rationale comments)
**File:** `ingest.py`, `build_index.py`, `embed.py` headers
**Symbol / region:** module docstrings encoding selection policy / no-vec0 rationale / fastembed→model2vec rationale.
**Why:** high comment-to-code ratio, but each block encodes design intent the brief/plan treat as load-bearing (and DEV-001's substitution rationale belongs near the code). Trimming risks losing the "why".
**Suggested action:** keep; dismiss (consistent with report-01 F-02 disposition).

<!-- pm-disposition: dismiss -->
