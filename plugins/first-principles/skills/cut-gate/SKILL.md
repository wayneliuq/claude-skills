---
name: cut-gate
description: "Remove agent-written bloat from a change that already works — first the mocked-out tests, swallowed errors, and toy fallbacks that make every later check unreadable, then guards on unreachable states, stored derived state, forwarding hops, one-value parameters, duplicate paths, one-inhabitant abstractions, and comments that contradict the code. Also decides whether a test earns its keep: one that cannot fail for a reason a user would care about is ballast, one a correct refactor can break has negative value, and one asserting an invariant across every writer of a shared state is protected from pruning however redundant it looks. The one gate that edits rather than reports: it logs every finding before touching anything, attempts to refute each one, and closes only when no finding is left undisposed. Use when a diff looks bloated or over-engineered, when a change works but is larger than it should be, or when asked to simplify, trim, or cut down agent-written code. Not for finding defects (bug-gate) or for judging whether work is verified (done-gate)."
---

# cut-gate

The change works. This gate asks whether it is the smallest change that works,
and whether the code tells the truth about itself.

Canon: `../principles/SKILL.md` — principles 1 (verified beats assumed), 2 (one
state, one owner), and 5 (reversibility decides who acts).

Catalog: [`references/bloat-shapes.md`](references/bloat-shapes.md) — forty-seven
named shapes, each with the symptom it wears and the cheap check that clears it.
Use it as a hypothesis generator. Open-ended reading finds only what you already
expected.

Test value by layer: [`references/test-value-by-domain.md`](references/test-value-by-domain.md)
— what to prune and what is untouchable, per layer.

**Moment:** after the change works, before `done-gate`. Not after. Simplifying
code that has already been verified invalidates the verification; simplifying
before it means `done-gate` verifies what will actually ship.

---

## The premise

Bloat is **sedimented uncertainty.** Every defensive branch is a question the
author declined to answer — "can this be null?" answered by adding a guard rather
than by reading the producer. So this is an *answer-the-questions* pass. Each
question has three honest outcomes, and the third is what makes the gate worth
running:

| The state is | Then |
|---|---|
| impossible | delete the guard, record the proof |
| possible | keep the guard — and it owes a test |
| possible **and mishandled elsewhere** | that is a bug → route to `bug-gate` |

**The cost model is states eliminated, not lines removed.** Lines are the wrong
target: optimizing them produces nested ternaries and dense unreadable
expressions, which is more sediment, not less. A change that removes one
parameter with one distinct value eliminates more state than one that deletes
thirty lines of straight-line code.

## Why this gate may edit

Every other gate reports. This one applies, and the licence is principle 5:
deletions on a working branch are recoverable, so they are the agent's to make.

That licence is conditional on three rules, and without them this gate becomes
the thing it exists to prevent:

1. **Log before touching.** The complete finding list is written down before any
   edit. The log is what proves nothing was quietly dropped, and it is what makes
   bulk disposition possible.
2. **Deletions and substitutions only. No rewrites.** Remove a branch, inline a
   constant, delete a hop, replace a stored field with its computation. If a
   finding can only be addressed by rewriting the logic, it is out of scope —
   log it and leave it.
3. **Never widen.** Only files already in the diff under review. Adjacent mess is
   not yours today (`../build-gate/SKILL.md`).

## Scope — in-diff by default

Rule 3 is what keeps this gate from becoming a repo-wide audit, and it governs
test files exactly as it governs source.

| Mode | Reaches | Entered by |
|---|---|---|
| **in-diff** (default) | tests and source already in the diff under review | running the gate |
| **sweep** | test files anywhere; source nowhere | an explicit, named request |

**In-diff is the whole default path.** It is also the common agent case: an agent
wrote implementation *plus* tests, and the tests assert the shape of its own
bloat. Pass 0 already licenses rewriting those tests and the verdict already
reports them, so the test rules below need no new licence.

**Sweep mode audits an accumulated suite.** It suspends rule 3 for test files
only, and may not touch a source file for any reason — a source finding found
while sweeping is logged, never applied. It is out of the default path because it
is a *different task*: the diff is not the unit of work, so nothing bounds the
blast radius except the test/source line.

**Sweep mode cannot be entered by inference.** It requires the caller to name it —
`cut-gate sweep`, or an instruction to audit the existing test suite. "The diff
looks bloated", "the tests seem redundant", and "the suite is slow" are **not**
entry conditions. Under all three, stay in in-diff mode and log the rest for the
next `scope-gate`.

## Every finding gets a disposition

Four outcomes. Three are terminal.

| Disposition | Meaning |
|---|---|
| `applied` | deleted or substituted |
| `refuted` | the refutation attempt succeeded — the code is correct, nothing changes |
| `bug` | reachable *and* mishandled elsewhere — routed to `bug-gate`, not fixed here |
| `deferred` | **not a disposition — an open item** |

`deferred` means the reachability question was not answered: no input could be
constructed that reaches the branch, and no proof that none exists. It must be
converted before the gate closes — by tracing the producer, or by writing the
test that reaches it. Doing that work *is* the gate.

**If a deferred item cannot be converted, the gate closes red, naming it.** Not
green with a footnote. Deleting on inability-to-prove is how a simplification
pass turns correct code into incorrect code, which is the more expensive of the
two available errors (principle 4).

There is no cap on findings. A cap converts an audit into a sample, and a
sampled audit reads as completeness while leaving the rest to be inherited as
convention.

## Refute before you cut

§0 of `../build-gate/SKILL.md`, inverted for deletion. Before applying any
finding, attempt to defeat it:

- For a guard: **name an input that reaches it.** This is the whole oracle. A
  test that fails to reach the branch is not proof of unreachability — no test
  reaching it means *safe to delete* or *untested*, and green cannot tell those
  apart. Reverse the order: construct the input first, delete second.
- For a duplicate: what does the other copy handle that this one does not?
- For a forwarding hop or one-value parameter: is there a caller outside the
  search — a dynamic dispatch, a config-driven registration, a template?
- For a comment: is the claim it makes true, and is it recoverable from the code
  without it?
- For a **test**: the obligation inverts — name a defect it would **catch**, not an
  input that reaches it. See pass 0. Applying the guard form to a test is the
  characteristic error here: a test nothing reaches is not a test that catches
  nothing, and a test that catches nothing usually runs green on every input.

**A finding you cannot make fail is a resemblance, not bloat.** Mark it
`refuted` and move on. Refuted findings are a healthy output, not a failure of
the pass.

---

## The passes

Ordered by dependency, not by radius. Pass 0 changes what every later pass can
see; a deletion in pass 3 can dissolve several findings in pass 4 before they are
reached. Within a pass, apply in order of states eliminated.

### Pass 0 — Oracle

*Catalog tier 0 (1–8, 41–43), plus the test shapes in tier 1 (44–47).* Mocks of
the unit under test, mock-echo assertions, swallowed errors, toy fallbacks, mocks
of things that do not exist, edited CI, coverage without assertions,
shape-assertion and change-detector tests, self-generated oracles, tautological
type mirrors, import-only tests, duplicated conformance copies, happy-path-only
contract tests, mocked-collaborator interaction tests — and shape 47, which is a
**keep** this pass must protect rather than a cut.

**Nothing below is measurable until this pass is clean.** Agent-written tests
assert on the *shape* of agent-written bloat, so the suite locks in every
over-engineered structure with the authority of a green gate. A pass that cannot
rewrite tests will produce findings it can never apply.

Do not proceed to pass 1 with an open pass 0 finding.

#### Measure before you prune

Do this **first**, because it decides whether there is a pruning question at all.

A test deletion may not be justified by "the suite is slow" without a
measurement. **A suite-speed finding is a configuration finding until measured
otherwise.**

The canonical case: a 7.9-minute CI test step decomposed as environment 296s,
module import 165s, transform 40s, **running the tests 21s**. Assertions were ~4%
of accounted CPU, because a global `environment: "jsdom"` made 327 files pay for a
DOM most never touched. Deleting a thousand test cases would have saved seconds;
fixing one config line saved minutes and cost zero coverage.

Test count is the last suspect, not the first. Attributing runtime to test volume
without decomposing the step is the same error as blaming a smell inside an
expensive step without varying it.

**Prune on revealed preference, not on inspection.** A test that has never caught
a failure *and* has been repeatedly edited to stay green is a change-detector by
its own history. `git log --name-only` over test paths gives that ranking for
free, and it is stronger evidence than reading the assertions.

#### Does this test earn its keep?

The disposition table decides what happens to a *guard*. This decides what happens
to a *test* that is none of the named pathologies above — merely useless rather
than actively lying. Two questions, and a test must pass **both**:

1. **Can it fail for a reason a user would care about?** If no input or state
   change can turn it red for a real defect, it is ballast — zero value, non-zero
   cost.
2. **Can any *correct* refactor make it fail?** If a behaviour-preserving change
   turns it red, its value is **negative**: it taxes every future change and
   catches nothing.

|  | refactor-proof | breaks on a correct refactor |
|---|---|---|
| **can fail on a real defect** | **keep** — the only quadrant that earns its keep | rewrite to assert behaviour; delete if it cannot be |
| **cannot fail on a real defect** | delete — ballast | delete first — negative value |

Protection-against-regressions × resistance-to-refactoring
([`references/test-value-by-domain.md`](references/test-value-by-domain.md)). It is
why a change-detector is classified as *negative* value rather than merely low.

**"It passes" is not evidence of value, and "it is green on the fixed code" is not
evidence it could have caught the bug.** A test can pass, be non-vacuous, and
still be structurally unable to fail on the symptom it was written for. This is a
rule, not a caution — it is the failure mode of most agent-written regression
tests.

#### The refutation obligation inverts for tests

"Refute before you cut" still governs, but what you must construct is the
opposite:

| Finding | To keep it, name |
|---|---|
| a guard | an **input that reaches** it |
| a test | a **defect it would catch** |

Cannot name the defect → the test is ballast. Can name it → the finding is
`refuted` and the test stays.

#### Two exceptions that override everything above

- **Never delete a test written for a defect that actually shipped.** Regression
  tests compound. If git history, the test name, or a linked issue ties it to a
  real incident, it is `refuted` by default. The burden sits on the deletion, and
  "I cannot see what this covers" does not discharge it.
- **Delete, never skip.** Converting a finding to `.skip`, `.only`, `xit`, or a
  commented-out body is not a disposition — it is a green checkmark that asserts
  nothing, which is strictly worse than absence. Absence shows up in a coverage
  report; a skip shows up as a pass (catalog 6).

#### The keep-floor differs by layer

Not "how much to test" but **what the cost of being wrong is** — a wrong rendered
pixel is a bug report, a wrong computed number is a lost user. Read
[`references/test-value-by-domain.md`](references/test-value-by-domain.md) before
disposing of any test finding; it is what stops a UI-shaped pruning instinct from
being applied to a numeric core.

### Pass 1 — Reachability

*Catalog 29, 34, 35, 36.* Guards on unreachable states, repeated guards, layered
re-validation, pass-through catches.

The disposition table at the top of this file governs every finding here. This is
the highest-yield pass and the one that most needs the refutation rule.

### Pass 2 — State

*Catalog 30, 13.* Stored derived state, duplicated hardcoded tables.

Ask of each stored value: is it a pure function of state already present at read
time? If yes, it has a second owner and a staleness question that computing it
would not have.

### Pass 3 — Path

*Catalog 31, 15, 16, 39, 38, 17.* Duplicate paths, Guard-and-Go residue,
orphaned deletion residue, same-commit dead helpers, round-trips that compute
nothing, append-only additions beside code that should have been updated.

Guard-and-Go deserves specific attention: a replacement that left the old path
reachable behind a conditional is a migration that appears to have happened and
has not.

### Pass 4 — Fan-in

*Catalog 32, 33, 26, 22, 23, 24, 25, 27, 37.* Forwarding hops, one-value
parameters, one-inhabitant abstractions, parameter drilling, redundant
re-injection, speculative configuration, boolean-blind parameter lists,
single-call-site dependencies, single-element concurrency scaffolding.

Mostly mechanical. Count call sites, implementations, distinct argument values,
and config read sites — including tests, which are where the phantom second
caller usually hides.

### Pass 5 — Claims

*Catalog 40, 11, 9.* Comments, docstrings, and duplicate helpers.

A comment is an unfalsifiable claim the next reader inherits as a specification.
Sort every one four ways:

| The comment | Action |
|---|---|
| **contradicts the code** | fix or delete first — worse than no comment at all |
| restates the code | delete |
| makes a falsifiable factual claim | **convert** to a type, assertion, or test — then delete |
| records *why* a non-obvious choice was made | keep — rare and valuable |

Conversion is the anti-ratchet move. It turns an inherited assertion into
something that can fail.

### Pass 6 — Structural, log-only

*Catalog 10, 12, 14, 18, 19, 20, 21, 28.* Type escape hatches, near-identical
sibling files, complexity concentration, call-graph thinning, manager-class
centralization, modular mirage, dependency-rule inversion, per-feature stack
sprawl.

These are the highest-mass shapes in the catalog and **none of them can be fixed
by a deletion.** Every one requires restructuring, which rule 2 puts out of
scope. This pass exists so they are *searched for* rather than quietly omitted —
a shape with no pass is a finding that vanishes, which is the hanging thread the
no-cap rule exists to prevent.

Log each with its evidence and disposition `not attempted`. They are input to the
next `scope-gate`, not work for this gate. Naming them here is also the only
honest way to say what this gate does not do: it removes sediment, it does not
redistribute mass.

## Worked example — the deletion these rules stop

An agent implements account credits. The diff adds three writers of one balance —
`applyCredit`, `refundCredit`, `adminAdjustCredit` — three per-writer test files,
and touches `credits.invariant.test.ts`, which asserts over the public read path
that balance always equals the sum of ledger entries, parameterized across every
writer.

**The naive pass deletes the invariant test.** It reads as a duplicate path to the
same effect (shape 31) sitting beside three more specific tests that each cover one
writer; it is the slowest file in the directory; and every one of the four is
green. Every surface signal says redundant.

**Question 1 stops it.** Name the defect it would catch: `adminAdjustCredit` writes
the balance column and does not write a ledger row. The invariant test goes red.
The three per-writer tests stay green, because each asserts only its own return
value — none of them reads the ledger. So the invariant test is the *only* test in
the diff that can fail for a reason a user would care about, and their greenness
was never evidence that they could have caught it.

**Question 2 confirms the keep.** It asserts an invariant over a public read path,
so no behaviour-preserving refactor can turn it red. `can-fail / refactor-proof` —
the keeper quadrant, and shape 47 by name: one source of truth, N writers, so a
green test on the canonical path is false confidence.

**The findings invert.** The invariant test is `refuted` and protected. Two of the
three per-writer tests are mock-echo (shape 2) — the repository is mocked to return
a balance and the test asserts that balance. The third is happy-path-only (45). The
disposition is 2 deleted with the defect each could not have caught named, 1
consolidated into the parameterized invariant suite, 1 kept as a protected
invariant — and the suite got *smaller* while its failure surface got *larger*.

The general lesson: **a pruning pass ranks tests by how redundant they look, and
load-bearing invariant tests look maximally redundant.** That is the shape of the
mistake, and naming the defect is what catches it.

## Verdict

```
AUDIT LOG:    <path or inline> — <n> findings, all dispositioned

Pass 0 oracle:      <n> applied · <n> refuted · <n> consolidated   ← must be clean to proceed
  Tests:            <n> deleted · <n> consolidated into table-driven/parameterized suites
                    <n> kept as protected invariants (multi-writer / regression-for-shipped-defect)
                    for each deletion: the defect it could not have caught
  Suite cost:       <measured breakdown, or "not measured — no speed finding claimed">
Pass 1 reachability:<n> applied · <n> refuted · <n> bug
Pass 2 state:       <n> applied · <n> refuted
Pass 3 path:        <n> applied · <n> refuted
Pass 4 fan-in:      <n> applied · <n> refuted
Pass 5 claims:      <n> deleted · <n> converted · <n> kept
Pass 6 structural:  <n> logged, none applied — handed to the next scope-gate

Mode:               in-diff | sweep (named by the caller — never inferred)
States eliminated:  <what, concretely — not a line count>
Failure surface:    <preserved / increased — never a file or test count>
Routed to bug-gate: <findings, with the mishandling site>
Refuted:            <findings that survived the attempt to defeat them>
Deferred:           <must be empty — any entry means this gate closed RED>
Not attempted:      <findings needing a rewrite rather than a deletion>
```

`Refuted` and `Deferred` are the lines that make this gate honest. A run with
zero refutations was not attempting to defeat its own findings.

**The per-deletion justification is the anti-ratchet move**, mirroring pass 5's
conversion rule: if the sentence naming the defect the test could not have caught
cannot be written, the finding is `refuted` and the test stays. A deleted test with
no such sentence beside it is a coverage loss disguised as a cleanup.

Nothing is committed here. That is `../ship-gate/SKILL.md`.
