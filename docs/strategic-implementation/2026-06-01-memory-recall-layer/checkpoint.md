# Checkpoint — memory-recall-layer

## Done
- D1 — go-forward capture schema (status/domain frontmatter + GOTCHA block) — 8c749e2 — 2026-06-01
- D2 — index builder: typed/status-aware ingest + normalizer + backfill (BM25/FTS5) — 469c524 — 2026-06-01
- D3 — BM25 recall command (ranked snippets + pointers, threshold, status filter) — c798be0 — 2026-06-01
- D4 — wire recall at point-of-need (executing-plans Step 2a + execution-plan Step 6) — c9cbe43 — 2026-06-01
- D5 — precision A/B gate (make-or-break) — PASS: precision@3=1.0, 0 false-pos, 126.5 tok inject — e580ddf — 2026-06-01

- D6 — [Phase 1b] vector leg: model2vec + sqlite-vec, RRF fusion (plan-time) — 5e4ff15 — 2026-06-01

## In progress
- (none)

## Open decisions
- (none)

## Unresolved deviations
- (none — DEV-001 resolved: fastembed→model2vec substitution, no downstream impact)

<!-- complete: 2026-06-01 -->

