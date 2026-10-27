# Lean: the smallest-change ladder, the shapes of bloat, and where tests may be cut

## The ladder

Take the first rung that fully works (after ponytail, DietrichGebert/ponytail, MIT):

1. **Does it need to exist?** Skip features, options and flexibility nobody asked for. In
   pr-review this rung is §3's necessity check and §5's constraint trace; the rungs below are
   §5e.
2. **Already in this codebase?** A helper, component, service or pattern: use it the way the
   surrounding code does. A house component beats a native widget.
3. **The platform or the standard library?** Use it, unless the project has its own.
4. **An installed dependency?** Use it. Never add a dependency for a few lines.
5. **One line a reader gets at a glance?** One line. A one-liner that needs decoding is not short.
6. **Otherwise the least code that works**, in the structure the codebase already has.

Lazy about the solution, never about the change: every caller, test and fixture the change
breaks is part of it. Code that is moved or merged keeps its error handling and validation.
Between options of equal size, take the one correct on edge cases.

**Never cut:** validation at trust boundaries, error handling that prevents data loss,
security, accessibility, anything the user asked for or sees, a test with an external oracle. A
shortcut with a known limit stays when it says so in a `shortcut: <limit>, <when to upgrade>`
comment.

## Why bloat matters

Bloat is sedimented uncertainty: a defensive branch is a question the author declined to
answer, a duplicate helper a search not performed, a mock a seam not understood. Each one
becomes prior art the next agent copies. Removing it is an answer-the-questions pass, not a
shortening pass, and it is checked on the diff, because instructions alone do not stop it.

## The shapes, by blast radius

Clear tier 0 first: it decides whether any later check can be trusted. Each line is the shape,
then the cheap check.

**Tier 0 — destroys the oracle**
- Mocking the unit under test → the test's subject is a mock; delete the mock or the test.
- Mock-echo assertion → asserts the value the mock was told to return.
- Error coerced to success → a `catch` that returns ok or a default; a silent fallback value.
- Self-generated oracle → a golden file or snapshot the code under test wrote itself.
- CI gaming and coverage illusion → skipped or always-true checks; lines run, nothing asserted.
- Change-detector, shape-mirror, import-only test → pins source text, a type's shape, or that
  a module loads.

**Tier 1 — poisons the conventions**
- Semantic duplicate helper → search by behaviour, not by name, before writing one.
- Type escape hatch → `any`, casts, `# type: ignore` on a changed path.
- Docstring that contradicts the code → read both; the code is the truth, fix the doc.
- Near-identical siblings and duplicated tables → two copies that must change together: merge.
- Happy-path-only contract test, mocked-collaborator interaction test → asserts calls, not results.

**Tier 2 — structural mass**
- Complexity concentration → one function doing several jobs: split by job, never by line count.
- Guard-and-go → a guard added at the consumer for a wrong value the producer still makes.
- Append-only editing → new branches stacked beside old ones; deletion residue left behind.
- Manager classes, modular mirage, inverted dependencies → layers with one caller, modules
  that all import each other.

**Tier 3 — surface area**
- Speculative configuration, one-inhabitant abstraction, one-value parameter → an option
  nobody sets, an interface with one implementation, a parameter every caller passes the same.
- Parameter drilling, boolean-blind parameter lists, a dependency with one call site.

**Tier 4 — local sediment**
- A guard on a state that cannot occur; repeated or layered re-validation of one fact.
- Stored derived state → a value kept that could be computed from its owner.
- Duplicate path to one effect; pure forwarding hop; pass-through try/catch; a round trip that
  computes nothing; a preflight that duplicates the real call.
- Concurrency scaffolding around one element; a dead helper added in the same commit.
- Narration comments ("previously", "fix for #n").

**A keep, not a cut:** a test that drives several writers of one piece of state looks
maximally redundant and is often the most valuable test in the suite. Never prune it for
looking like the others.

## Where the test floor sits, by layer

A wrong pixel is a bug report; a wrong number is a lost user, because nobody sees it. So the
floor differs by layer:

| Layer | Prune | Never prune |
|---|---|---|
| **Numeric core** | example batteries that collapse into one table or property | anything with an external oracle; invariants (permutation, scale, degenerate input); tests at realistic magnitudes, not tidy integers |
| **Contracts / APIs** | hand-written shape mirrors; happy-path-only cases | status codes, conflict and validation paths, idempotency, ordering, rows written before a migration |
| **Backend services** | tests of forwarding controllers; mocked-session interaction tests | migrations and integrity against a real database with real rows; every auth test |
| **UI** | rendering mechanics, prop plumbing, mounts that only import | state machines and multi-writer invariants; one browser smoke per critical journey |

A property that replaces many examples makes the suite smaller and stronger at once: reach
for it before a delete. Deleting a shape mirror is right only if the semantic tests beside it
survive. The two test questions are Khorikov's protection against regressions and resistance
to refactoring, read as separate axes (*Unit Testing*, 2020); a change-detector scores zero on
both, which is why it is negative value.
