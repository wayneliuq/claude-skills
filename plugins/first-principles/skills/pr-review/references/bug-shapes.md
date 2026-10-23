# The bug-shape catalog

Eighteen recurring shapes, as hypotheses: for the symptom in front of you, ask which could
produce it and rule them out cheaply. Each is the shape, what it looks like, and the check.
Code that is unnecessary rather than wrong is in [`lean.md`](lean.md).

1. **Runtime coexistence** — two implementations of one behaviour are both live. *Looks like*
   it works sometimes, or differs by entry point. *Check:* count every definition and
   registration of the behaviour.
2. **Producer changed, consumer didn't** — a value's source, shape, name or unit changed; a
   reader still expects the old form. *Looks like* a blank, a zero, a plausible wrong number.
   *Check:* every reader of the changed value, against what it now receives.
3. **Persistence loss dressed as display** — data is lost in storage, seen in the view. *Check:*
   read the stored state directly; if it is not there, stop looking at the UI.
4. **Split ownership** — two layers each set one value and drift. *Looks like* two parts of the
   screen disagreeing, fixed by reload. *Check:* every write site; more than one owner is the bug.
5. **Environment divergence** — version, timezone, locale, file-name case, concurrency. *Check:*
   diff the environments on the axis the failing code touches.
6. **Vacuous test** — passes whether the code is right or not. *Check:* revert the
   implementation; if the test still passes, it tests nothing.
7. **A flake that is a bug** — a race, ordering dependency or shared-state leak. *Check:* run it
   alone, reordered, repeatedly; reproducible under stress means real.
8. **Instance fix, class left alone** — the reported site is patched, its siblings are not.
   *Looks like* the same bug under a new ticket. *Check:* search the whole repo for the shape.
9. **Helper that deadlocks under a held lock** — a factored helper takes a lock some caller
   already holds. *Check:* for each call site, is the lock held on that path?
10. **Cleanup at the wrong phase** — state is released while something downstream still reads
    it. *Check:* map where it is written, last read and cleaned; cleanup before last read is the bug.
11. **Stale branch reverts trunk on merge** — *Check:* diff against current trunk, not the old
    merge base, for files the work never meant to touch.
12. **An invariant no test encodes** — a cross-path rule broken by a locally correct diff.
    *Check:* name the subsystem's invariants; encode any held only by convention as a test.
13. **Built, never wired** — correct code nothing on the user's path calls. *Check:* trace from
    the entry point a user touches forward to the new code.
14. **Spec ambiguity posing as a defect** — the code does what was asked, not what was meant.
    *Looks like* the requester restating the same point. *Check:* restate it in one sentence and
    confirm before writing a repro.
15. **Released only on success** — a resource freed after its last use, not in a `finally`.
    *Check:* is the release reached on success, error, cancellation and teardown?
16. **Validation after the effect it gates** — saved or sent first, checked later. *Check:* the
    order on the real path, not in the source layout.
17. **Retry without a budget** — no cap, backoff or cancellation, or wrapping a non-idempotent
    call. *Check:* name the cap and backoff; is the wrapped call safe to run twice?
18. **Preflight that duplicates the real call** — an exists-check before the read it gates.
    *Check:* delete the first call and handle the real call's failure.
