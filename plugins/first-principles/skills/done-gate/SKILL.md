---
name: done-gate
description: "The five-layer verification a change must survive before anyone says it is done — full test suite, independent review, an adversarial second pass, verification against the real running thing, and a fresh re-run immediately before merge. Also judges test quality: rejects vacuous tests, change-detector tests, source-shape assertions, and tests that pass on unfixed code. Use before declaring work complete, before merging, or whenever a claim of 'done' or 'tests pass' needs to be trusted."
---

# done-gate

"Done" is a claim about the world, and this gate is what makes it checkable.

Canon: `../principles/SKILL.md` — principle 1 (verified beats assumed).

The core insight: **a green suite is not correctness.** A passing run validates
only the contracts the tests describe. If the tests mock the seams where the code
actually lives, the suite measures something orthogonal to whether the thing
works. Layers 3 and 4 exist because layers 1 and 2 systematically miss.

Run the layers in order. A failure at any layer stops the gate — do not proceed
to the next and do not average the results.

**No layer closes on generated text.** A layer passes when something was *executed* —
a suite run, a flow driven, an artifact opened and looked at. A second model agreeing
with the first is not a verification event, and two models agreeing that a defect
exists is not evidence that it does.

---

## Layer 1 — the full test suite

- Run it **to completion. Never sampled.** "I ran the relevant tests" hides
  defects in exactly the paths you did not think were relevant, which is where
  unexpected coupling lives.
- Coverage ratchets one direction. Every fix ships with a regression test; the
  suite only grows.
- **A flake is a defect.** An intermittent failure is a real race, a real ordering
  dependency, or real shared state — in the product, not in the test runner.
  Re-running until green normalizes a live bug. Root-cause it or file it; never
  paper over it.
- Run the tests neighboring what you touched, not only your own new ones.

## Layer 2 — independent review of the diff

Review the actual diff in isolation, as if you had not written it and do not know
the intent. Read it for what it says, not for what you meant.

## Layer 3 — the adversarial pass

A **second, differently-tuned** pass whose job is to find what the first pass was
constitutionally unable to see. Not a repeat with more effort — a different
posture: assume the change is wrong and look for the reason.

Where the two passes disagree on the same finding, the *kind* of dispute decides the
tiebreak:

- **Adequacy** — is this tested enough, is this case handled, is this name clear:
  **the stricter verdict wins.**
- **Existence** — is this a defect at all: **the side holding evidence wins**, and
  where neither side has evidence, **null wins and nothing changes.** "Stricter" on
  an existence dispute means accepting the accusation, which is the mechanism by
  which a review turns correct code into incorrect code.

Cheap and effective in practice: a fresh reviewer with no knowledge of the
reasoning, prompted to refute rather than to confirm.

## Layer 4 — verify the real thing

Green tests plus a working feature are two different claims. Exercise the actual
scenario in the actual product:

- Perform the observable-done steps from the scope contract, in order, for real.
- For UI, capture before and after at real viewports and actually interact with
  the interactive parts.
- **Check reachability.** This is the failure mode that survives every other
  layer: the code exists, it is correct, its unit tests pass — and *nothing in the
  real user path ever calls it.* Built but not wired. Trace from the entry point a
  real user touches all the way to the new code. If you cannot, it is not done.
- **Do not trust a self-report as proof.** "The job reported success" is not the
  artifact existing. Go look at the artifact.
- **Stopping at the first green checkmark is not done.**

## Layer 5 — the authoritative re-run

Immediately before merge, run layers 1–4 **fresh**. Not the results from an hour
ago, not from before the last rebase. Trunk moved, the branch moved, and stale
green is the most convincing wrong answer available.

Special check: on any branch that has been open a while, **scan for unintended
whole-file rewrites.** A stale branch can silently revert recent trunk work in
files it never meant to touch. Diff against current trunk, not against the
merge-base you started from.

---

## Test quality

A test is an asset only if it would catch the thing going wrong. Reject these
(`../cut-gate/references/bloat-shapes.md` tier 0 covers the same ground in depth,
and is the place these get *rewritten* — this gate only refuses to count them):

- **The vacuous test** — passes whether or not the code is correct. The litmus:
  revert the fix; if the test still passes, it protects nothing.
- **The change-detector test** — asserts on incidental values that break on
  routine updates. Reject unless that exact data *is* the contract.
- **Testing code shape** — regex or string assertions against source files. That
  tests what the code looks like, not what it does. Extract the logic and test it
  directly instead.
- **The mocked seam** — on anything whose risk *is* the integration, a test that
  mocks that integration verifies nothing. Flag it explicitly rather than counting
  it as coverage.
- **Not verified against unfixed code** — the fix's test must fail on the buggy
  version, for the right reason. A test that cannot be made to fail means the finding
  was refuted, not fixed (`../build-gate/SKILL.md` §0).

And know which tests are load-bearing. A test named after a function, asserting
only on its return shape with synthetic inputs, is scaffolding. A test that walks
a named user through a real flow is the asset. Before crediting anything as
"tested," check that a flow-level counterpart exists — not just branch coverage on
a pure function.

Where an invariant is architectural — true across paths, enforced by no single
function — it needs a test that encodes it. **An invariant the tests do not
encode will be violated by a diff that is locally correct**, and no reviewer
reading that diff will see it.

## Verdict

```
Failed layer:  <which, or none>
Reachability:  traced <entry point> → <new code> | NOT REACHABLE
Verified:      <what, and how>
Refuted:       <findings that did not survive falsification — none is an answer>
Assumed:       <list>          ← anything here means not done
Gaps:          <admitted, explicitly>
```

`Assumed` and `Gaps` are the point of the gate. An empty `Gaps` line that is not
true is worse than a long one that is.

This gate reports; it does not silently fix what it finds, and it does not mark
itself green by lowering a bar. If something fails, say so with the output.
