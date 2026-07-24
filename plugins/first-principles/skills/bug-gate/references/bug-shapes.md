# The bug-shape catalog

Fourteen recurring shapes. Use as a hypothesis generator: for the symptom in
front of you, ask which shapes could produce it, then rule them out cheaply
before opening an investigation. Each entry gives the shape, the symptom it
usually wears, and the cheap check that confirms or clears it.

---

## 1. Runtime coexistence

Two implementations of the same behavior are both live. One shadows the other, or
they interleave.

- **Wears:** "it works sometimes," "it reverted itself," behavior that differs by
  entry point.
- **Check:** search for every definition and registration of the behavior, not
  just the one you were editing. Count them.

## 2. Producer changed, consumer didn't

A value's source, shape, name, or units changed; a downstream reader still expects
the old form. Often silent — the reader gets `undefined`, a default, or a plausible
wrong number.

- **Wears:** a field that is blank or zero, a default appearing where real data
  should be.
- **Check:** find every consumer of the changed thing. Compare what each expects
  against what it now receives.

## 3. Persistence loss wearing a presentation costume

Data is lost at the storage layer, but the symptom appears where it is displayed.
Debugging concentrates on the renderer, which is innocent.

- **Wears:** "it doesn't show up," "it disappears on refresh."
- **Check:** read the persisted state directly, at the source of truth, bypassing
  the UI entirely. If it is not there, stop looking at the view layer.

## 4. Split ownership of one piece of state

Two layers each set the same value independently. They agree at first and drift.

- **Wears:** two parts of the screen disagreeing; a value correct until a specific
  action; state that resyncs on reload.
- **Check:** find every write site for the value. More than one owner is the bug.

## 5. Environment divergence

Passes in one environment, fails in another — different versions, missing
dependency, different timezone or locale, different filesystem case sensitivity,
different concurrency.

- **Wears:** "works on my machine," CI-only failures.
- **Check:** diff the environments on the axis the failing code touches, rather
  than re-running hopefully.

## 6. The vacuous test

A test passes regardless of whether the code is correct.

- **Wears:** a bug shipping in code that has coverage.
- **Check:** revert the implementation. If the test still passes, it never tested
  anything.

## 7. The flake that's actually a bug

An intermittent test failure is a real race, ordering dependency, or shared-state
leak in the product.

- **Wears:** "just re-run it."
- **Check:** run it in isolation, then in a different order, then repeatedly.
  Reproducible under stress means real. Treat every flake as a defect until it is
  proven to be one in the harness.

## 8. The instance fix that left the class alone

The bug is patched at the site that was reported; identical flaws remain at
sibling sites.

- **Wears:** the same bug reappearing under a new ticket weeks later.
- **Check:** search for the pattern — the same call shape, the same missing guard
  — across the whole repo before fixing.

## 9. The shared helper that deadlocks under a held lock

Code was factored into a helper that acquires a non-reentrant lock. Some call site
already holds it.

- **Wears:** intermittent hangs, timeouts, a "flake" that is really a deadlock.
- **Check:** for each call site of the helper, ask whether the lock is already held
  on that path.

## 10. Cleanup at the wrong lifecycle phase

State is pruned or released during a phase where something downstream still needs
it.

- **Wears:** failures only under specific ordering, on second run, or on the
  fast/slow path.
- **Check:** map the lifecycle and mark where the state is written, read last, and
  cleaned. Cleanup before last-read is the bug.

## 11. The stale branch that reverts recent work on merge

A long-open branch carries old versions of files it never intended to change.
Merging silently reverts recent trunk work alongside the intended change.

- **Wears:** a fix disappearing after an unrelated merge.
- **Check:** diff the branch against **current trunk**, not the original
  merge-base, and look for files changed that the work never touched.

## 12. The invariant the tests don't encode

An architectural rule — true across paths, owned by no single function — is
violated by a diff that is locally correct. No reviewer reading that diff can see
it.

- **Wears:** production breakage from a change that reviewed cleanly.
- **Check:** name the invariants of the subsystem. Ask whether any is enforced only
  by convention. Encode it as a test.

## 13. Client-built, pipeline-missing

The code exists, is correct, and its unit tests pass — but nothing in the real
user path ever invokes it. Built, never wired. This shape survives every review
that asks "does this code work" instead of "is this code reached."

- **Wears:** "it's implemented" and yet the feature does nothing.
- **Check:** trace from the entry point a real user touches, forward, to the new
  code. If the trace breaks, the feature does not exist.

## 14. Spec ambiguity masquerading as a code defect

The code does what was asked. What was asked was not what was meant. Debugging
cannot fix this and will burn hours proving the code correct.

- **Wears:** the requester re-explaining the same thing in different words; a fix
  that satisfies the letter of the report and not the reporter.
- **Check:** scan the last several messages from the requester. If they have
  restated the same point more than once, suspect the specification. Stop, restate
  your understanding in one sentence, and get it confirmed before writing a repro.
