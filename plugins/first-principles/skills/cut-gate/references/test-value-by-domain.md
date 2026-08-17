# Test value by layer

The two-question value rule in `../SKILL.md` decides whether a single test earns
its keep. This file decides where the floor sits, because the floor is not the same
everywhere.

The organizing insight is not "how much to test." It is **what the cost of being
wrong is**, and that differs by layer:

- A wrong rendered pixel is a bug report. Someone sees it, says so, and it is fixed.
- A wrong computed number is a lost user. Nobody sees it. It is trusted, acted on,
  and discovered — if ever — long after the decision it corrupted.

So the layer with the least testable surface is often the one that most needs a
test, and the layer easiest to generate tests for is the one where generated tests
are worth least. A pruning instinct calibrated on UI tests, applied to a numeric
core, deletes exactly the wrong things.

## The table

| Layer | Prune | Never prune |
|---|---|---|
| **Numeric / algorithmic core** | example batteries that collapse into one table-driven case | anything with an external oracle; invariants (permutation, scale, degenerate input, monotonicity); tests at realistic units and magnitudes, not tidy integers |
| **Contracts / API boundaries** | hand-rolled shape mirrors (shape 42); happy-path-only cases (45); per-consumer copies of one contract (44) | semantics a schema cannot express — status codes, conflict and validation paths, idempotency, ordering, behaviour on rows written before a migration |
| **Backend service layer** | unit tests of forwarding controllers and repositories; mocked-session interaction tests (46) | migrations and data integrity against a **real** database; every auth and permission test |
| **UI** | rendering mechanics, prop plumbing, import-only mounts (43), canvas assertions inside a DOM shim | state-machine and multi-writer invariants (47); one browser-level smoke per critical journey |

Two clarifications the table compresses:

- **Tidy integers hide the bug.** A numeric test written over `1`, `2`, and `100`
  passes under unit errors, precision loss, and off-by-one scaling that realistic
  magnitudes would expose. Testing at the units and orders of magnitude the code
  actually receives is not extra rigour; it is the difference between a test that
  can fail and one that cannot.
- **An empty-database CI cannot catch a data-transform bug.** A migration test that
  runs against a schema with no rows in it verifies that the SQL parses. The defect
  lives in what the transform does to rows that already existed — which is why this
  row of the table says *real* database, and why the mocked version of the same test
  is shape 46.

## Two rules that fall out of the table

**Schema-valid is weaker than compatible.** A shared or generated type proves shape
and ignores values. It cannot tell you that a field arrives in the wrong unit, that
an enum gained a member consumers do not handle, or that a nullable field is now
always null. So deleting a shape mirror (shape 42) is correct **only** if the
semantic tests it sat next to survive. Delete the mirror and the semantics together
and the boundary is now guarded by a typechecker that was never checking the thing
that breaks.

**A property replaces many examples and catches what no example can.**
Consolidating a battery of examples into an invariant — output is a permutation of
input, scaling inputs scales output, the degenerate case returns the identity — is a
**substitution** that reduces file count while *increasing* failure surface,
because it holds over inputs nobody thought to enumerate. Prefer it to deletion
wherever it is available. This is the one move in this gate that makes the suite
both smaller and stronger; reach for it before reaching for a delete.

## Where the two axes come from

The value rule is Khorikov's first two pillars of a good test — **protection against
regressions** and **resistance to refactoring** — treated as independent axes rather
than as a single quality score (Vladimir Khorikov, *Unit Testing: Principles,
Practices, and Patterns*, Manning, 2020). Read as two axes, the four quadrants are
forced, and only one of them is a keeper.

That framing is also why a change-detector test is classified as **negative** value
rather than merely low: it scores zero on protection and zero on resistance, so it
imposes maintenance cost with no offsetting benefit. Google's testing group reached
the same conclusion independently and named it — "Change-Detector Tests Considered
Harmful," Google Testing Blog, 2015 — on the grounds that such a test fails
precisely when the code is being improved and passes precisely when it is being
broken in a way the test's own assumptions share.
