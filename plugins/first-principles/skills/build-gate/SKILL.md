---
name: build-gate
description: Discipline for code being written right now — surgical edits, tracing one authoritative value end-to-end, checking every consumer before changing a producer, proving resources release on every exit path, refusing coexisting patterns, and matching existing conventions. Use while implementing a change, when about to modify a shared helper or a data shape, when a change is starting to sprawl beyond its stated scope, or when deciding whether a new abstraction or shared component is justified.
---

# build-gate

Applied while the code is being written, not after. Most of its checks are cheap
in the moment and expensive to retrofit.

Canon: `../principles/SKILL.md` — principles 2 (one state, one owner), 3 (fix the
class), and 4 (change exactly what was asked).

---

## Edit discipline

- Write the minimum that satisfies the stated criteria. Not the elegant general
  version — the minimum.
- Clean up only code **your own changes** made unused. Adjacent mess is not yours
  today.
- Do not improve neighboring code. Do not rename things you are passing through.
  Do not reformat files you touched incidentally.
- Match the surrounding conventions: naming, error handling, file layout, test
  style, comment density. If the codebase is consistently doing something you
  would not do, do it their way.
- When you notice a real problem outside scope, note it and keep going. Say it at
  the end; do not fix it silently.

## Trace one authoritative value end-to-end

Pick the value the change actually turns on — the resolved config, the selected
record, the computed permission — and follow it from where it is decided to where
it is used. The classic failure is a split between the deciding stage and the
acting stage: one resolves `A`, the other re-resolves and gets `B`.

**Validate at the point of use, not at the point of lookup.** If you check a thing
and then look it up again later to act on it, you validated a different thing.

**Scope by complete identity.** Any cache key, memo key, or dedup key must include
every axis that distinguishes the entries. A key missing one dimension is a
correctness bug that presents as "it shows the wrong one sometimes."

## Producer / consumer

Before changing what something returns, emits, or stores:

1. Find every consumer. Every one — not the ones you remember.
2. For each: **updated**, **unaffected because `<reason>`**, or **deliberately
   skipped because `<reason>`**.
3. Anything you cannot place in one of those three buckets is unfinished work,
   not a judgment call.

The same applies in reverse: before changing how something is read, check whether
you are the only reader or whether you are making one reader diverge from its
siblings.

## One state, one owner

- Two implementations of the same behavior must not both be live. If the new one
  is landing, the old one goes in the same change, or is explicitly disabled with
  a note. "Both for now" is how coexistence bugs are born.
- When two patterns in the codebase genuinely conflict, pick one for this change
  and **flag the other for cleanup**. Do not blend them into a third.
- Track when a value can go stale, and who is responsible for noticing.

## Every exit path releases

For anything acquired — locks, handles, connections, subscriptions, temp files,
in-flight flags, spinners, "is saving" state — prove it is released on **all four**
paths: success, error, cancellation, teardown. Cancellation is the one that gets
forgotten; teardown is the one that leaks in tests.

**Shared helpers and locks:** before factoring code that acquires a lock into a
shared helper, check whether any call site already holds it. A non-reentrant lock
re-acquired by a helper deadlocks, and it deadlocks intermittently, which reads
as a flake.

**Cleanup at the right lifecycle phase.** Pruning state during a phase where
something downstream still needs it is a bug that appears only under specific
ordering.

## Abstraction bar

Work the rungs from principle 4 before writing anything new. Then: a new shared
component or abstraction needs **two or more current, named consumers** — not two
hypothetical future ones. One consumer means it lives at the call site.

## Tests, while building

Write **one failing test for the thinnest next slice**, make it pass, repeat.
Do not write all the tests first and then all the implementation — that produces
a suite shaped like your plan rather than like the behavior, and it hides the
moment where an assumption breaks.

The test must fail on the unfixed code, **for the right reason**. A test that
passes before your change protects nothing. Check this explicitly; it is the
single cheapest way to catch a test that does not test what you think.

## UI work

- Show the edit **in place**, against the surrounding surface, not in isolation.
  When presenting a visual change, dim what is unchanged and mark what is new or
  changed.
- Verify at real viewports, including narrow. A layout that only exists at desktop
  width is not verified.
- Use real content rather than lorem, and no fabricated precision in numbers.

## Verdict

Findings with evidence, not reassurance. Report only what forces disclosure:

```
Consumers:  <n> found — <n> updated, <n> unaffected (<why>), <n> skipped (<why>)
Out-of-scope noticed: <list, unfixed>
Deliberate shortcuts: <what, its limit, upgrade path>
```

Anything that cannot be placed in one of those consumer buckets is unfinished work.
