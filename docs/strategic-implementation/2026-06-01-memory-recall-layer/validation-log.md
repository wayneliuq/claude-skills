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

## APPROACH — D3
**Method:** integration-test
**Domains:** indexing, recall, sqlite-fts5
**Approach:** `python3 test_recall.py` builds a real fixture index then drives `recall.search` directly: asserts (1) a docker/login query returns the auth APPROACH with a source pointer, (2) a no-term-overlap query returns nothing (FTS5 MATCH relevance gate), (3) aborted records excluded unless `--include-demoted`, (4) `recall.sh` exits 0 + empty on a missing index (advisory-never-blocks). bm25() ranking, real DB, no mocked seam. recall.sh is the token-report.sh-style thin entrypoint that swallows any crash to silent exit 0.

## APPROACH — D5
**Method:** integration-test (precision/injection) + post-hoc (live adoption)
**Domains:** recall, precision-gate, success-signal
**Approach:** `python3 precision_ab.py --out <feature>/precision-ab-findings.md` loads the COMMITTED `memory-fixtures/labeled-set.json` (thresholds + corpus + per-query relevance labels pinned before the run), materializes the corpus, builds a real FTS5 index, runs recall per query. Result: precision@3=1.0 (≥0.75 target), 0 false positives (unrelated + aborted queries return nothing → aborted-exclusion proven), mean injection 126.5 tok (≤400 budget) → recall is net-token-negative vs re-derivation. The live "agent adopts recall instead of re-deriving" + true point-of-use token delta is post-hoc (post-reload-verification.md, check #2).

## APPROACH — D4
**Method:** post-hoc (cli grep now; live trial deferred per L-005)
**Domains:** skill-wiring, recall, point-of-need
**Approach:** cli grep confirms (a) executing-plans Step 2a carries the BM25-only "Point-of-need recall (advisory)" block calling `recall.sh` with informs-never-dictates semantics, and (b) execution-plan Step 6's former N-most-recent `grep` is fully replaced by a `recall.sh` call (old instruction grep count = 0), with "proceed silently" preserved in both. The live, in-session halves (recall fires before build; agent adopts it; plan-time surfacing) load only on plugin reload (L-005) and are scheduled in `post-reload-verification.md` (reviewer = PM; trigger = first run after reload).

## GOTCHA — D3
**Domains:** recall, corpus-maturity
**Lost time on:** expecting sharp relevance from the live real corpus today
**Do instead:** the real corpus has only 1 pre-existing APPROACH block, so BM25 returns loose matches now; relevance sharpens as the go-forward capture schema (D1) accumulates APPROACH/GOTCHA blocks. Pin the numeric threshold via D5's labeled fixture rather than tuning against today's sparse corpus.
