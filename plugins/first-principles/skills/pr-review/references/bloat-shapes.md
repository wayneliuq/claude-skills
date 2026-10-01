# The bloat-shape catalog

Forty-seven recurring shapes in agent-written code. Use as a hypothesis generator: for
the diff in front of you, ask which shapes it could contain, then rule them out
cheaply. Each entry gives the shape, the symptom it wears, and the cheap check
that confirms or clears it.

Every shape here is a consequence of the same thing: **bloat is sedimented
uncertainty.** A defensive branch is a question the author declined to answer. A
duplicate helper is a search not performed. A mock is a seam not understood. The
pass that removes them is an *answer-the-questions* pass, not a shortening pass.

## Why the tiers

Tiers are **blast radius** — how far the damage travels beyond the line it sits
on — not frequency and not severity. Three observations set the order:

- **Some shapes destroy the oracle.** A suite that mocks its own subject, a `catch`
  that returns success, or a golden file the code under test wrote itself makes
  every later check unreadable. Nothing below tier 0 can be measured until tier 0
  is gone.
- **Every shape ratchets.** Each artifact becomes prior art the next agent
  imitates: duplicated logic gets replicated further, an escape hatch becomes a
  hole the next pass fills with invention, a wrong docstring is read as the
  contract. Comments are the most legible case of a general law, not a special
  one.
- **Instructions do not fix this.** Anti-bloat prompting lowers the starting
  volume and leaves the rate of accumulation unchanged. These have to be checked
  for, on the diff.

Clear tier 0 before anything else: it changes what every later check can even see.

Detection is marked **static** (text or AST), **graph** (call/type graph query),
or **reasoning** (needs judgment). Roughly two-thirds are mechanical; reserve
attention for the rest.

One entry — shape 47 — is a **keep** rather than a cut. It is here because a
pruning pass ranks candidates by how redundant they look, and the highest-value
test in a codebase looks maximally redundant. A catalog that only names things to
delete is a catalog that will delete it.

---

# Tier 0 — Oracle destroyers

Until these are gone, a green suite carries no information, and every finding in
tiers 1–4 is unverifiable.

## 1. Mocking the unit under test

The test mocks the module it exists to test, then asserts that the fake behaved
like a fake. The production path is never executed.

- **Wears:** thorough-looking coverage on a component that breaks in production;
  a test file with more mock setup than assertion.
- **Check (graph):** does the mock set intersect the unit under test? Any overlap
  is the shape. Then delete the mock and see whether the test still means anything.

## 2. Mock-echo assertion

A dependency is mocked to return `X`, and the test asserts the function returned
`X`. It passes for every implementation, including an empty one.

- **Wears:** a test that has never failed.
- **Check (graph):** trace dataflow from the mock configuration to the assertion.
  If nothing under test sits between them, the test asserts on its own setup.

## 3. Error-to-success coercion

A failure is converted into a success-shaped value — empty list, `{ok: true}`,
a default, stale cache — so no caller can tell the difference. The signal is
destroyed, not merely unhandled.

- **Wears:** "it silently does nothing"; failures that surface far downstream as
  missing data; in the worst reported case, failed payments recorded as succeeded.
- **Check (static):** every `catch` / `except` with no re-raise whose body returns
  a literal or default-constructed value. Distinguish from a guard: a guard adds
  a branch, this one *deletes the failure*.

## 4. Silent fallback substitution

Asked to implement `X`, the author implements `X` **plus** a simpler working path
that activates when `X` fails — alphabetical ordering when clustering fails,
keyword matching when the model fails. Tests and benchmarks pass while measuring
the toy.

- **Wears:** metrics that look plausible but never move with changes to the real
  implementation; a feature that "works" with its main dependency unreachable.
- **Check (graph):** a branch whose arms both reach the same return type, where
  one arm calls the expensive dependency and the other constructs a literal.
  Then break the dependency deliberately and see whether anything fails.

## 5. Hallucinated-then-mocked dependency

An external service that does not exist is invented, then mocked. The result is
an internally coherent test suite over nothing.

- **Wears:** a well-tested integration nobody can find in production.
- **Check (graph):** every mock target must resolve to a real definition. One that
  does not is this shape.

## 6. CI gaming

Tests removed, renamed, or skipped; coverage thresholds lowered; `|| true`
appended; a workflow step newly conditioned. The suite was edited to fit the code
rather than the code to fit the suite.

- **Wears:** a green pipeline that went green suspiciously soon after going red.
- **Check (static, diff only):** this shape is invisible in the tree. Diff the
  test and CI configuration against the previous state, every time.

**Delete, never skip.** A skip is this shape even when the intent was cleanup.
`.skip`, `.only`, `xit`, and a commented-out body are not dispositions of a test
finding — each is a green checkmark that asserts nothing, which is strictly worse
than absence: absence appears in a coverage report, a skip appears as a pass. If a
test should not run, delete it and name the defect it could not have caught.

## 7. Coverage illusion

High statement coverage with no meaningful assertions — code is executed but
nothing is checked. Coverage tooling reports this as success.

- **Wears:** near-total coverage alongside routine escaped defects.
- **Check:** mutation testing. Coverage cannot detect this; surviving mutants can.
  Cheap proxy (static): test bodies with zero assertion calls.

## 8. Shape-assertion and change-detector tests

Tests that assert on the structure of the code rather than its behavior — a
snapshot of everything, a regex over source, an assertion on an intermediate data
shape. Written against bloat, they lock that bloat in with the authority of a
green gate.

- **Wears:** tests that break on every refactor and never on a real defect; the
  feeling that a structure "can't" be simplified.
- **Check (static):** snapshot-assertion density; string or regex assertions
  against source files; assertions naming private intermediates. If simplifying
  the implementation breaks the test but no behavior changed, the test was
  asserting shape.

## 41. Self-generated oracle

A golden file, snapshot, or expected-value fixture produced by the code under
test. It can only detect that the answer *moved*, never that it is *wrong* — so a
defect present at generation time is certified correct forever, and the test
actively defends it.

- **Wears:** a fixture regenerated by a script in the same package; "update the
  goldens" as a routine step in the contributing guide; a review that approves a
  fixture diff without reading it.
- **Check (static → reasoning):** trace the fixture's provenance — who wrote these
  bytes. No external oracle (a spec, a reference implementation, a hand-computed
  value, a second independent tool) means the test measures change, not
  correctness. Tier 0 because it destroys the oracle in the most durable way
  available: the wrong answer becomes the definition of the right one.

## 42. Tautological type mirror

A runtime assertion re-asserting a shape that a shared or generated type already
guarantees — checking that a field exists and is a string when the schema says so.
The typechecker is the test; the duplicate is a change-detector with extra steps.

- **Wears:** assertions that enumerate keys; a test file that changes every time a
  type does, and never otherwise.
- **Check (graph):** does a shared or generated type define this shape? Then the
  assertion has no failure mode the compiler does not already own. Delete it —
  but see the schema-valid-is-weaker-than-compatible rule in
  `test-value-by-domain.md`: only correct if the semantic tests it sat beside
  survive.

## 43. Import-only test

Mounts, constructs, or renders and then asserts nothing but absence of a throw —
including anything asserting on a canvas or GPU surface inside a DOM shim that
cannot draw. It proves the module imported.

- **Wears:** `toBeDefined()` or `toBeTruthy()` as the terminal assertion;
  "renders without crashing"; a test whose whole body is a constructor call.
- **Check (static):** test bodies whose only assertion is existence, truthiness, or
  a bare `expect(() => f()).not.toThrow()`. Tier 0 because it reads as coverage of
  the component and is coverage of the import graph — the gap between those two is
  where the oracle goes.

---

# Tier 1 — Convention poisoners

Local cost is small. The cost that matters is that the next author reads these as
the house style and reproduces them.

## 9. Semantic duplicate helper

A helper functionally identical to one that already exists, under a synonym —
`formatCurrency` / `formatMoney` / `toCurrencyString` — with divergent edge-case
handling, because prior art was never searched for.

- **Wears:** the same bug fixed twice; two functions that disagree on `null`.
- **Check (reasoning; static for exact clones):** for every new helper, search for
  an equivalent by behavior rather than by name. Exact clone detection catches the
  easy half; the renamed half needs judgment or embeddings.

## 10. Type escape hatch

`as any`, `as unknown as T`, non-null `!`, `@ts-ignore`, `# type: ignore`. The
compiler is satisfied by removing the guarantee it existed to provide.

- **Wears:** runtime shape errors in code that type-checks.
- **Check (static):** grep. The most mechanically detectable shape in this
  catalog. Its real cost is second-order — an `any` is a hole the next pass fills
  with invented fields.

## 11. Docstring that contradicts the code

Not narration of what was done — a stated contract the code no longer honors.
The next reader generates callers against the documented signature, and the error
surfaces far from its cause. Wrong documentation is materially worse than none:
missing docs slow a reader down, wrong docs actively mislead.

- **Wears:** callers written against parameters that do not exist; a bug report
  quoting the docstring.
- **Check (reasoning; static proxy):** does the docstring name a parameter absent
  from the signature, a return type that does not match, or a raised error the
  body cannot produce?

## 12. Near-identical sibling files

Three endpoints, three route files, each a copy of the last with nouns swapped.
The per-file version of duplication, and the version most likely to be read as
the intended pattern.

- **Wears:** a change that has to be made three times; two of three files fixed.
- **Check (static):** AST similarity between files in the same directory.

## 13. Duplicated hardcoded table

A list or mapping baked into source in more than one place, where a single
derivation would serve. The copies drift, and both are usually incomplete.

- **Wears:** behavior that differs by entry point; a value present in one list
  and missing from the other.
- **Check (static for the duplication; reasoning for whether a derivation
  exists):** find literal collections with overlapping membership across files.
  Compare them — disagreement proves the drift already happened.

## 44. Duplicated conformance copy

N near-identical test files asserting one shared contract once per implementation,
usually template-scaffolded from the first one. The contract is stated N times and
owned nowhere, so adding an implementation now costs a directory of tests — the
suite makes the next feature *more* expensive, which is the opposite of what a
suite is for.

- **Wears:** a test directory whose file count tracks the implementation count;
  three of five copies updated when the contract changed.
- **Check (static):** filename and body similarity across sibling implementation
  directories. The fix is a **substitution** — one parameterized suite driven by the
  implementation registry, which yields the same coverage and gives new
  implementations the contract for free — so it is in scope under rule 2. Distinct
  from shape 12, which is source and log-only.

## 45. Happy-path-only contract test

Covers the boundary path the running application already exercises constantly, and
none of the error paths nothing exercises until a user does. The priority is
inverted: the covered case is the one that would have been caught in the first
minute of manual use.

- **Wears:** one test per endpoint, all asserting 200; no test naming a status
  code, a conflict, or a validation failure.
- **Check (reasoning):** list the boundary's failure modes, then check which have a
  test. Keep one happy path — it catches wiring breaks cheaply — and keep every
  failure mode you have actually been burned by. The finding is the *absence*, so
  the disposition is usually a substitution, not a deletion.

## 46. Mocked-collaborator interaction test

Asserts call order or call counts through a mocked boundary whose real risks — SQL,
constraints, migrations, serialization, transaction scope — are invisible to the
mock. You learn that the code called what it called.

- **Wears:** `toHaveBeenCalledWith` as the only assertion; a test that breaks when
  two independent calls are reordered.
- **Check (static → reasoning):** assertions on a mock's call record rather than on
  a returned value or observable state. Prefer real collaborators wherever they are
  fast and deterministic; where they are not, the test belongs at the layer that
  can use the real one. Related to shape 2, but distinct: the echo asserts on the
  mock's *output*, this asserts on its *input*.

## 47. Single-path test on multi-writer state — **a keep, not a cut**

The inverse shape, catalogued here so a pruning pass recognizes it. When one source
of truth has N writers, a green test on the canonical path is false confidence: it
proves the writer that was easiest to test is correct, and says nothing about the
other N−1.

- **Wears:** a state with several writers and tests named after only one of them; a
  bug report of the form "the balance is wrong after an admin action".
- **Check (graph):** count the writers of the state, then count which writers a test
  covers. A gap is a finding — and the fix is an **invariant test across every
  writer**, not a deletion.
- **Why it is in this catalog:** invariant-across-all-writers tests are the
  highest-value tests in a codebase *and* the ones most likely to look redundant to
  a pruning pass — they duplicate coverage the per-writer tests appear to provide.
  They are protected. Deleting one is the characteristic failure of a pruning
  pass.

---

# Tier 2 — Structural mass

These accumulate monotonically across sessions and are the reason a codebase
becomes unworkable rather than merely untidy.

## 14. Complexity concentration

Each new feature is patched into an already-complex function rather than
distributed. Complexity does not spread evenly — it piles onto the same few
callables until they cannot be reasoned about.

- **Wears:** one function everybody is afraid of; changes that require reading
  400 lines to alter 4.
- **Check (static):** rank functions by cyclomatic complexity weighted by size.
  Watch the *maximum* and the *count above threshold*, not the average — averages
  hide this completely.

## 15. Guard-and-Go

Asked to *replace* behavior, the old path is left in place and wrapped in a
conditional or fallback so it stays reachable. Tests pass because the new path
executes; nothing asserts the old one is gone. The migration appears to have
happened and has not.

- **Wears:** a completed migration with the old implementation still in the tree;
  behavior that reverts under an unusual flag or input.
- **Check (graph):** the diff introduces a conditional around a block that was
  previously unconditional, and both arms reach an equivalent effect. Ask what
  input selects the old arm. If none can, delete it; if one can, the migration
  is not done.

## 16. Orphaned deletion residue

The edit landed in the right place but removed only part of what it required —
leaving unreferenced symbols, half-migrated call sites, imports of nothing.

- **Wears:** dead symbols dated to the same change that was supposed to remove
  them.
- **Check (graph):** symbols with zero inbound edges whose last modification is
  the change under review.

## 17. Append-only editing

New behavior is added *beside* old code rather than by updating it. Nothing old is
ever touched, so the old thing stays live and the two coexist.

- **Wears:** two ways to do everything; a codebase that only grows.
- **Check (static):** blame-age of the changed lines. A change that adds a
  behavior while touching nothing older than itself did not integrate — it
  deposited.

## 18. Call-graph thinning

New code does not connect to what already exists. It re-derives, re-implements,
and re-fetches rather than calling the functions already present.

- **Wears:** a new module that imports almost nothing internal.
- **Check (graph):** count edges from new symbols to *pre-existing* symbols. Near
  zero means reuse did not happen, regardless of how the code reads.

## 19. Manager-class centralization

Logic is concentrated into a single coordinating class that reaches everything
and that everything reaches, instead of being delegated to the components that
own it.

- **Wears:** one class imported by every module; a name containing Manager,
  Handler, Service, or Helper with no narrower meaning.
- **Check (graph):** one node with both high fan-out across the module and high
  fan-in from it.

## 20. Modular mirage

Files split into many modules with no cohesion behind the split — structural
modularity without logical separation, so related behavior fragments across
boundaries.

- **Wears:** every change touching six files; module names that do not predict
  contents.
- **Check (reasoning; proxy static):** co-change coupling across module
  boundaries. Files that always change together are one module wearing three
  filenames.

## 21. Dependency-rule inversion

Responsibility lands in the wrong layer — authentication inside a wiring factory,
a client importing from the service layer, persistence reached from a formatter.

- **Wears:** a change in one layer requiring a change in a layer that should not
  know about it.
- **Check (static):** layer rules, mechanically. This is fully automatable and
  frequently is not automated.

---

# Tier 3 — Surface area

Each of these is small and permanent. They are obligations: once public, they
constrain every later change.

## 22. Parameter drilling

The same argument threaded by hand through every intermediate frame, each of
which only forwards it.

- **Wears:** a one-line behavioral change that edits forty files.
- **Check (graph):** an identically named and typed parameter at three or more
  consecutive call-graph depths where the intermediate frames only pass it along.

## 23. Redundant re-injection

A new parameter or constructor argument supplying a value that was already
reachable from a dependency the component holds.

- **Wears:** two routes to the same value inside one object.
- **Check (graph):** for each new parameter, ask whether its value is reachable
  from an already-present dependency. Distinct from a one-value parameter — this
  one is *available*, not merely constant.

## 24. Speculative configuration

Environment variables, feature flags, and options for scenarios the task did not
require. Worse than an unused parameter, because the knob is externally visible
and becomes a compatibility obligation the moment anyone might have set it.

- **Wears:** configuration documentation longer than the feature; flags nobody
  can explain.
- **Check (graph):** a config key with exactly one read site and no write site
  outside its default. A flag whose value is a constant is not a flag.

## 25. Boolean-blind parameter list

Several boolean parameters whose meaning is invisible at the call site —
`process(true, false, true)`. Added one per requested variant instead of modeling
a mode.

- **Wears:** call sites that cannot be read without opening the definition;
  arguments transposed in a bug.
- **Check (static):** functions with two or more boolean parameters. Strengthen by
  checking whether every call site passes literals.

## 26. One-inhabitant abstraction

An interface with a single implementation, a factory producing one type, a
generic instantiated at exactly one type. The surface style of a large codebase
without the conditions that justified it.

- **Wears:** navigating three files to find the one function that runs.
- **Check (graph):** implementations per interface; distinct instantiations per
  type parameter. One is the finding. This is fan-in-of-one at the type level —
  see shape 33 for the function-level form.

## 27. Dependency with one call site

A package added to the manifest for a single call that the standard library or an
existing dependency already covers.

- **Wears:** a lockfile growing faster than the feature set.
- **Check (graph):** for each dependency added, count call sites of its imported
  symbols. One means read what it does and consider inlining it.

## 28. Per-feature stack sprawl

Each feature arrives with its own infrastructure because each was built in
isolation — two queues, three HTTP clients, in one reported case multiple
databases in one application.

- **Wears:** operational surface that nobody can enumerate.
- **Check (static, then reasoning):** group dependencies by capability. More than
  one provider for a capability needs a stated reason.

---

# Tier 4 — Local sediment

Contained, high in volume, cheap to check. This tier is where "answer the
question" is most literal: nearly every entry is a decision the author deferred
by adding code.

## 29. Guard on an unreachable state

A defensive branch for a condition the producer cannot generate. The question
"can this be null?" was answered by adding a check instead of by reading the
producer.

- **Wears:** null checks on values that are constructed three lines above; a
  branch with no test and no reachable input.
- **Check (reasoning, with a hard rule):** **before deleting, name an input that
  reaches the branch.** Constructible → keep it, and it owes a test.
  Provably none → delete, with the proof recorded. Neither → this is a deferred
  item, and it must be resolved, not filed. If the state *is* reachable and
  mishandled elsewhere, it is a bug, not bloat.

## 30. Stored derived state

A value computed from others and then persisted in a field, cache, or variable
alongside its inputs — creating a second owner and a staleness question that did
not previously exist.

- **Wears:** two parts of the interface disagreeing; a value correct until a
  specific action; a `refresh()` that exists to paper over the gap.
- **Check (graph):** for each stored field, ask whether it is a pure function of
  other state present at read time. If yes, it should be computed at read.

## 31. Duplicate path to the same effect

Two routes producing the same outcome, both live. The narrower runtime form of
shape 17.

- **Wears:** "it works sometimes"; behavior differing by entry point.
- **Check (graph):** count distinct paths reaching the effect. More than one
  without a stated reason is the finding.

## 32. Pure forwarding hop

A function whose entire body is a call to another function with the same
arguments. It adds a frame, a name, and an indirection, and changes nothing.

- **Wears:** three files to follow one call.
- **Check (graph):** single-statement bodies that delegate with unchanged
  arguments. Delete the hop and retarget its callers.

## 33. One-value parameter

A parameter that takes the same value at every call site. It is a constant
wearing a parameter's costume, and it forces every reader to consider a variation
that does not exist.

- **Wears:** `verbose=False` at all nine call sites.
- **Check (graph):** distinct argument values per parameter across all call sites,
  tests included. One distinct value means inline it.

## 34. Repeated guard in sequence

The same predicate applied to the same binding more than once in a scope with no
mutation between — `if (xs && xs.length > 0)` three times in one function.

- **Wears:** dense, anxious-looking code.
- **Check (static):** duplicate predicates on one binding within a scope. A signal
  the author was not confident about the flow.

## 35. Layered re-validation

The same invariant re-established at controller, service, and repository. Each
check is individually defensible; the bloat is establishing the invariant N times
instead of parsing it once at the boundary and carrying it in the type.

- **Wears:** identical validation errors raisable from four depths.
- **Check (graph):** the same predicate applied to a value at more than one depth
  of a single call chain.

## 36. Pass-through try/catch

`try { f() } catch (e) { throw e }`. A frame and a nesting level for nothing. The
error-handling form of shape 32.

- **Wears:** nesting with no purpose.
- **Check (static):** catch bodies that are a bare re-raise of the caught binding.

## 37. Single-element concurrency scaffolding

`Promise.all` with one promise, a pool of size one, `gather` with one awaitable, a
batch endpoint called with one item. Concurrency machinery around a sequence with
no concurrency.

- **Wears:** async complexity with no async benefit.
- **Check (static):** exact and cheap.

## 38. Round-trip that computes nothing

Data moved to a new container and then verified to be there; a value serialized
and immediately deserialized; a loop whose only effect is an assertion about the
loop above it.

- **Wears:** a 150-line function that does the work of three.
- **Check (graph):** dataflow from `X` back to `X` with no transformation in
  between.

## 39. Same-commit dead helper

A function useful during the author's own exploration that no longer participates
in the result, left behind because work stopped at "tests pass."

- **Wears:** nothing — it is invisible until searched for.
- **Check (graph):** symbols introduced by the change under review with zero
  inbound edges as of that same change. Far stronger than a general dead-code
  sweep, because provenance makes it unambiguous.

## 40. Narration comment

A comment restating what the line below does. Harmless as prose, corrosive as
inheritance: the next reader treats it as a specification rather than a
description, and it outlives the code it described.

- **Wears:** comment density tracking line count rather than difficulty.
- **Check (reasoning), sorted three ways:** restates the code → delete. Makes a
  falsifiable factual claim → **convert** it into a type, an assertion, or a test,
  then delete. Records *why* a non-obvious choice was made → keep; this is rare
  and valuable. Conversion is the move that stops the ratchet. A comment that
  contradicts the code is shape 11 and outranks all of this.
