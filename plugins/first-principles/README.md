# first-principles

Coding discipline as **gates**, not as a workflow.

A gate answers one question, produces a verdict with evidence, and gets out of the
way. What the gates constrain is **what must be true before you may call something
done** — never how to get there.

One gate, `cut-gate`, also *acts*: it deletes rather than only reporting. Principle
5 permits that, because deletions on a working branch are recoverable — and it logs
every finding before touching anything, so acting never conceals what it found.

## The five principles

Every rule in every gate is a consequence of one of these. They live in
`skills/principles/SKILL.md`, and each gate references that file rather than
restating them.

1. **Verified beats assumed** — every real defect traces to something believed but
   not checked. Green tests are not correctness; a self-report is not evidence.
2. **One state, one owner** — most non-trivial bugs are two things owning one value.
3. **Fix the class, not the instance** — a bug at one call site almost always has
   siblings.
4. **Change exactly what was asked** — scope creep is the largest source of
   self-inflicted regressions.
5. **Reversibility decides who acts** — the agent does anything recoverable; the
   human presses anything irreversible. This is the collaboration boundary.

Plus a six-rule **security spine**: reading can never change doing · secrets never
enter context · capability minimalism · untrusted code runs sandboxed · public
writes need a human or mechanical reversibility with independent verification ·
suspected vulnerabilities route privately.

## The gates

| Skill | Moment | Question it answers |
|---|---|---|
| [`principles`](skills/principles/) | reference | What are the invariants? |
| [`scope-gate`](skills/scope-gate/) | before code | Do we agree what this is and how we'll know it worked? |
| [`build-gate`](skills/build-gate/) | while coding | Is this change disciplined and complete in its own terms? |
| [`cut-gate`](skills/cut-gate/) | after it works | Is this the smallest change that works, and does the code tell the truth about itself? |
| [`done-gate`](skills/done-gate/) | before "done" | Is it actually correct, verified against the real thing? |
| [`bug-gate`](skills/bug-gate/) | debug / audit | What is wrong here, and where are its siblings? |
| [`ship-gate`](skills/ship-gate/) | before it leaves | Safe to release, honestly described — and is this mine to press? |
| [`watch-gate`](skills/watch-gate/) | after release | Would we find out if this broke? |
| [`pr-review`](skills/pr-review/) | "review this PR" | Should this PR exist, is it the right shape, and is it now the PR we would have written? |

`pr-review` is the one composite: it runs bug-gate, cut-gate and done-gate over a draft PR, fixes what it finds in that branch, and never marks the PR ready. The gates are independent — none requires any other. Skip any of them when the work
is trivially small.

Two gates carry catalogs, and they are the plugin's densest assets:
[`bug-shapes.md`](skills/bug-gate/references/bug-shapes.md) (18 shapes) and
[`bloat-shapes.md`](skills/cut-gate/references/bloat-shapes.md) (47 shapes). Each
entry pairs a named shape with the symptom it wears and the cheap check that
clears it. Both work as hypothesis generators, because open-ended searching finds
what you already expected to find.

They divide cleanly: bug-shapes is *what is wrong*, bloat-shapes is *what is
unnecessary*. A bloat finding that turns out to be reachable and mishandled
elsewhere stops being bloat and routes to `bug-gate`. `bloat-shapes.md` is tiered
by blast radius, on the finding that some shapes — a suite that mocks its own
subject, a `catch` that returns success — destroy the oracle every other check
depends on, and so have to be cleared first.

## Worker definitions

[`agents/`](agents/) holds the four implementation workers that
`adversarial-delegation`'s triage dispatches to — Sonnet 5.5 and Opus 5.5, each at
medium and high effort. They exist because an Agent-tool call can pick a model but
not an effort level, and because the `sonnet`/`opus` aliases resolve differently per
provider, so the definitions pin full model ids. **The four share one system prompt
body; change all four together.**

## Telemetry

[`skills/watch-gate/scripts/agent-roi.py`](skills/watch-gate/scripts/agent-roi.py)
measures the real token cost of subagent fan-out by parsing
session transcripts directly — nothing in it trusts a component's report of its own
cost. Use it to retire automated checks that do not pay for themselves; `watch-gate`
explains the methodology (blind scoring, cache discounting, variance before
conclusions).

```bash
# measure every subagent this project fans out to
skills/watch-gate/scripts/agent-roi.py extract

# or narrow to specific agent types
skills/watch-gate/scripts/agent-roi.py extract --agents general-purpose,Explore
```

Deterministic, no network, no model. `extract` prints a per-agent cost table and
writes per-round slices; a blind value-classification pass goes between `extract` and
`roi` (the prompt template is printed by `extract`).

## Lineage

Distilled from [Steward-OS](https://nesquena.github.io/steward-os/) — an operating
model for AI agents as project co-maintainers — with the open-source-maintainership
half (issue triage, contributor credit, community management, autonomy ladders for
unattended fleets) stripped out, and its ~90 named rules reduced to the five
principles above plus the gates that operationalize them.

It replaces the retired `strategic-implementation` plugin, which imposed a linear
pipeline (clarify → brief → architecture → plan → execute). That pipeline stopped
earning its cost: every stage was a place the model had to march, and a model
optimizing for the artifact a stage demands is not optimizing for the code being
right. Six things from it survived the retirement and are carried here — the
never-block clarifying rule, the anti-goals / out-of-scope distinction, the
multi-flow invariant prompt, the load-bearing-vs-scaffolding test heuristic, the
secret-scan placeholder exclusions, and the ROI telemetry script.
