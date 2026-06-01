# Precision A/B findings — memory-recall-layer (D5)
_The make-or-break gate. Source fixture: `plugins/strategic-implementation/scripts/memory/memory-fixtures/labeled-set.json` (thresholds + labels committed before this ran)._

**Verdict: PASS**

- precision@3 (mean over expect-nonempty queries): **1.0** (target ≥ 0.75)
- false positives (unrelated/aborted queries that returned anything): **none**
- mean recall-injection size: **126.5 tokens** (budget ≤ 400) — the cost recall pays to replace re-derivation

## Per-query

| query | returned | precision | injection (tok) | note |
|---|---|---|---|---|
| docker-e2e-repeat | 2 | 1.0 | 170 | ok |
| search-index-repeat | 1 | 1.0 | 83 | ok |
| unrelated-returns-nothing | 0 | — | 0 | ok |
| aborted-not-surfaced-as-precedent | 0 | — | 0 | ok |

## Scope (honesty)
- Measured here: recall **precision** and **injection cost** on a pinned labeled set.
- NOT measured here (post-hoc, after plugin reload — see `post-reload-verification.md`): the live 'agent adopts the recalled approach instead of re-deriving' behavior and the true point-of-use token delta vs a recall-disabled run. This script establishes that recall is precise + cheap enough to be net-token-negative; the live run confirms adoption.
