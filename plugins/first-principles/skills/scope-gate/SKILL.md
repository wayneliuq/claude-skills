---
name: scope-gate
description: Agree on what a change is before any code is written. Surfaces ambiguity, converts the request into an observable definition of done, enumerates the state the change touches, and states what it deliberately will NOT do. Use before starting a new feature, a non-trivial change, or any request whose shape is not already obvious — and whenever a request arrives phrased as a solution rather than a problem. Produces a short scope contract the human approves; the agent may not widen it later without coming back.
---

# scope-gate

The one gate whose output a human must actually read. Everything downstream
inherits its scope; if this is wrong, correct code is still the wrong code.

Canon: `../principles/SKILL.md` — principle 4 (change exactly what was asked) and
principle 5 (reversibility decides who acts).

Cost discipline: this gate is short — not an interrogation and not a document. If
the request is small and unambiguous — a typo, a copy change, a
one-line fix with an obvious success condition — say so and skip the gate. Running
it on trivial work is the fastest way to make it get ignored on real work.

---

## 1. Is this a problem or a solution?

Requests arrive as solutions constantly, and a solution hands you its own
assumptions pre-baked. If the request names a mechanism rather than an outcome,
offer exactly one alternative framing:

> This looks like a solution; the underlying need may be `<X>` — confirm or
> correct.

One framing question. Not a Socratic dialogue. If the answer is "no, I want it
this way," that is the answer — record it and move on.

## 2. Two questions, and the rule that makes them safe

Ask these, in the human's language, with no jargon:

1. **If this shipped tomorrow, what is the one-sentence change to someone's day?**
2. **How would you know it worked from the outside** — a behavior you could watch,
   a number that moves, a thing you could click? Not "the code was written."

**Never block.** If either question cannot be answered in one sentence, record
`TBD — open question: <the question>` and proceed anyway. Inability to answer is
itself signal: it usually means the outcome is genuinely not yet decided, and
stalling the work does not decide it. Carry the TBD forward visibly so it gets
answered by the first thing that forces the issue.

Then play it back for confirmation:

> To confirm — when `<X>` happens for `<named user>`, you will consider this shipped.

Name a **concrete user or caller**, not an abstraction. "Users" cannot observe
anything; "someone opening the report page on their phone" can.

## 3. Observable done

Write the success criteria as steps someone could physically perform, in order,
and see the result. Each step is a thing that happens in the real product, not in
a test.

Bad: "the endpoint returns the merged record."
Good: "open the item, edit the title, reload the page — the new title is there."

If a criterion cannot be written as an observable step, it is not a criterion yet.
Say so rather than inventing one.

## 4. State-space enumeration

Before touching code, list the dimensions this change spans. Miss a dimension
here and it becomes a bug report later. Work through them explicitly:

- **Inputs and shapes** — what data flows in, and what forms can it take?
- **Empty, one, many, too many** — what happens at each?
- **Failure, cancellation, teardown** — every exit path, not just success.
- **Who else reads this?** Every consumer of anything being changed.
- **Multi-flow invariant** — *is there a state more than one path can produce or
  change?* If yes, state what must be true regardless of which path ran. (E.g.
  "a companion record exists after creation, however the item was created.")
  This is where single-happy-path descriptions hide their bugs.
- **Existing conventions** — how does the codebase already solve this shape of
  problem? Survey one similar existing surface before inventing a new one.

If a convention in the codebase contradicts what was asked for, **surface the
conflict** — do not silently resolve it in either direction.

## 5. Three-way scope split

| | Meaning |
|---|---|
| **In scope** | this change delivers it |
| **Out of scope** | not now — legitimate, deferred, may come back |
| **Anti-goals** | we would reject this *even if it were free* |

The out-of-scope / anti-goal distinction is the load-bearing one, and most people
collapse it. "We are not doing offline sync yet" is deferral. "This will never
grow its own user accounts" is identity. Anti-goals let every future request be
declined without re-litigating the premise.

## 6. Verdict

Output the contract, as briefly as it can be stated:

```
SCOPE CONTRACT
Outcome:        <one sentence, user-facing>
Named user:     <who observes it>
Observable done: <numbered steps a person can perform>
State-space:    <dimensions covered; invariants named>
In scope:       <list>
Out of scope:   <list>       Anti-goals: <list>
Open questions: <TBDs, or none>
Conflicts:      <convention vs. request, or none>
```

Then stop and let the human respond. **This gate does not begin work.**

Once approved, the contract is the boundary. If implementation reveals the scope
was wrong — and it sometimes does — come back and say so explicitly rather than
quietly widening. Silent widening is the failure this gate exists to prevent.
