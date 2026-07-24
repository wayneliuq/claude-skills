---
name: bug-gate
description: Find what is actually wrong — in a reported bug, a failing test, or existing code being audited. Runs a fourteen-shape bug catalog as a hypothesis generator instead of reading hopefully, requires a deterministic repro before theorizing, checks first whether the real defect is in the spec rather than the code, and always widens a fix to the whole class before it lands. Use when debugging, when a test fails or flakes, when reviewing existing or unfamiliar code for defects, or when asked whether code is correct.
---

# bug-gate

Two modes, same machinery: **debug** (a specific symptom) and **audit** (existing
code, no symptom yet). The catalog is the engine of both — a named shape list beats
open-ended searching, because open-ended searching finds what you expected to find.

Canon: `../principles/SKILL.md` — principles 1 (verified beats assumed) and 3 (fix
the class).
Catalog: `references/bug-shapes.md` — fourteen shapes with symptoms and cheap
checks. Read it before hypothesizing.

---

## 0. Is the defect in the spec?

Do this **before** building a repro. It costs one read and saves hours.

Scan the last several messages from whoever reported this. **If they have restated
the same point more than once, suspect the specification, not the code.** Someone
re-explaining themselves is telling you the understanding is broken, not the code.

If triggered: stop. Restate your understanding of the desired behavior in one
sentence, get it confirmed, and only then decide whether there is a bug at all.

## Debug mode

### 1. Deterministic repro before hypothesis

Build a reproduction that fails reliably, then theorize. Reversing this order
produces a confident fix for a bug you never observed.

If you cannot reproduce it, say that plainly and describe what you tried. A fix for
a bug you cannot trigger cannot be verified, and shipping one is worse than
shipping nothing — it consumes the evidence.

### 2. Shape-match against the catalog

Read `references/bug-shapes.md`. For this symptom, name the shapes that could
produce it. Run each shape's cheap check to rule it in or out — checks first, deep
investigation only for what survives.

Symptom shortcuts:

| Symptom | Check these shapes first |
|---|---|
| "Doesn't show up" / "disappears on refresh" | persistence-loss, producer/consumer |
| "Works sometimes" / "two places disagree" | coexistence, split ownership, flake-is-a-bug |
| Intermittent hang or timeout | shared-helper deadlock, flake-is-a-bug |
| CI-only failure | environment divergence, lifecycle-phase cleanup |
| Reviewed clean, broke in production | unencoded invariant, built-not-wired |
| "It's implemented" but nothing happens | built-not-wired |
| A fix reappeared as a bug later | instance-not-class, stale branch |
| Bug shipped in code that has coverage | vacuous test |

### 3. Rank causes, rule out the top ones first

State the ranked hypotheses with your confidence in each. Then eliminate — cheapest
disqualifying check first.

**Layer ownership before fixing.** When state is lost, establish *which layer lost
it* — persistence, transport, or presentation — before changing anything. Read the
source of truth directly, bypassing the layers above it. Fixing the renderer for a
storage bug is the most common wasted day in debugging.

### 4. Failure protocol

Debugging fails in a recognizable way, and the recovery is mechanical:

1. State the current root-cause hypothesis in **one sentence**.
2. Classify it: **determinate** (you can prove it from the code) or
   **assumption-based** (it rests on something you believe but have not checked).
3. If assumption-based, list the assumptions with confidence in each, and check the
   lowest-confidence one first.
4. Attempt a fix. If it fails, **re-examine before attempting again** — do not
   retry a variation of the same idea.
5. **Three consecutive failed attempts: stop.** Do not try a fourth. Write up what
   was ruled out, what remains, and which assumption you could not verify, and
   bring it to the human. Continuing past three is where a debugging session turns
   into damage.

Tag any temporary debug logging with a unique prefix — `[DBG-a4f1]` — so removing
all of it later is one search rather than an archaeology exercise.

## Audit mode

No symptom; you are looking for what is wrong in code that appears to work.

1. Establish what the code is *supposed* to do, from the code's consumers rather
   than its comments.
2. Walk the catalog top to bottom against this code. Shapes 1, 2, 4, 8, 12, and 13
   are the productive ones in audits — they are the shapes that do not announce
   themselves.
3. Name the subsystem's invariants and check which are enforced only by convention.
   Every convention-enforced invariant is a future shape-12 bug.
4. Check reachability of anything recently added — shape 13.
5. Sample the tests for vacuity — shape 6. Coverage percentage tells you nothing
   about this.

## Reviewing someone's proposed fix

- **Verify the claim against the codebase.** Does the described bug actually exist?
  Trace the code path; do not take the description on faith.
- **A wrong premise beats bad code.** A change resting on an incorrect model of how
  the system works is a worse problem than a change with ugly code, and it is much
  harder to see. Check the premise first.
- **Verify the test against unfixed code.** It must fail on the buggy version, for
  the right reason.
- **Reject model-compensation changes** — open-ended repair layers, retries, or
  normalizers that exist to absorb an upstream component's misbehavior. They mask
  non-compliance and become permanent. Surface the root failure instead.
- **Salvage over reject.** Prefer cherry-picking, rebasing, or rebuilding onto a
  fresh base over bouncing work back. When you must bounce it, give an exact,
  reproducible fix-spec — not a direction.
- **Scan for unintended whole-file rewrites** on any stale branch — shape 11.

## Always: widen to the class

Before the fix lands, search for the same shape elsewhere and fix the siblings in
the same change. This is not optional cleanup; it is the difference between fixing
a bug and deferring most of it.

If a sibling genuinely cannot be fixed here, name it explicitly as remaining work.

## Verdict

```
Spec check:   clear | AMBIGUITY SUSPECTED — <evidence>
Repro:        <deterministic steps> | NOT REPRODUCIBLE — <what was tried>
Root cause:   <one sentence>  [determinate | assumption-based: <assumptions>]
Class sweep:  <n> sibling sites found — <n> fixed, <n> remaining (<why>)
Regression test: <verified failing on unfixed code for the right reason>
```

Never rewrite history to hide a failed attempt. Fixes land as new commits.
