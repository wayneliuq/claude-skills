# Documentation registry

Per-repo doc index. Populated at clarify time when the PM names a doc, read by execution-plan to compute `may-invalidate` per deliverable, updated by executing-plans inside each deliverable's atomic commit, and verified by post-execution. **The registry is an index, not a knowledge base** — `Covers` rows stay one line. If a `Covers` field grows past one line, that content belongs in the doc, not here.

| Path | Covers | Last Updated | Update Trigger | Owning Area |
|---|---|---|---|---|
| `docs/strategic-implementation/2026-04-30-outcome-first-and-mockups/product-brief_outcome-first-and-mockups.md` | brief for outcome-first/mockup/registry feature | 2026-05-01 | spec amendment, version bump | strategic-implementation |
