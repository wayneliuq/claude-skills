---
status: in-progress
domains: [strategic-implementation, memory-recall, indexing, python-runtime]
outcome: TBD
supersedes: none
---
# Validation log
_Feature: memory-recall-layer · Started: 2026-06-01 · Autonomy: auto_

## APPROACH — D2
**Method:** integration-test
**Domains:** indexing, python-runtime, sqlite-fts5
**Approach:** `python3 test_build_index.py` builds a real SQLite/FTS5 index over a temp fixture tree covering all 3 schema generations + noise + a stub + a duplicate + cross-domain records, asserting acceptance (a)-(f) against real DB state (no mocked seam). Then `build_index.py --root docs/strategic-implementation` builds over the real 13-folder corpus (131 records, 0 noise) as a smoke check. Run from `plugins/strategic-implementation/scripts/memory/`.
