---
name: adversarial-delegation
description: Run a first-principles gate (bug-gate / build-gate / done-gate) by delegating implementation to a worker — a cursor-agent (grok) subprocess or an Agent-tool subagent in a worktree — while acting as its adversarial reviewer. Use when a task is large enough to hand off but too consequential to accept on trust, and when several such tasks must run in parallel without colliding. Encodes how to pick the worker and transport, the flags that actually give it a shell, the file-safety rules that stop it destroying your uncommitted work, how to fence parallel streams and own the merges, how to write a brief it can refuse — including why its first action on any finding you did not prove is the test that would refute it — and what the reviewer must verify rather than believe.
---

# Adversarial delegation

Two roles, never collapsed. The **worker** (a `cursor-agent` subprocess) writes code and runs
gates. **You** are the adversarial reviewer: you set the charter, then try to break what comes
back. The value is in the asymmetry — the worker is invested in its solution, you are not.

Canon: `../bug-gate/SKILL.md`, `../build-gate/SKILL.md`, `../done-gate/SKILL.md`. This skill
is the delegation mechanics those gates assume you have.

---

## 1. Choosing the worker

Two transports, and they are not interchangeable. Decide before you write the brief, because
the brief's fences differ.

| | `cursor-agent` subprocess | Agent-tool subagent |
|---|---|---|
| Isolation | none — your working tree | `isolation: "worktree"`, its own checkout |
| Blast radius | your uncommitted work (see §2) | its worktree only |
| Parallelism | one per working tree (§3) | many, safely |
| Visible to you | a log file you poll | task notifications, `SendMessage` to resume |
| Survives session exit | as a process, yes | **no — in-process state is lost** |
| Cost centre | separate CLI quota | this session's budget |

Pick the transport by **isolation need first, model second**. Parallel streams over one repo
want worktrees; a single sequenced task on the current tree can take either.

**Match the model to the failure mode, not to the task's size.** The question is what breaks
if the worker reasons shallowly:

- **A subtle port or a shared-state change** — many references to rewrite where each one has a
  correct and an almost-correct form, and the almost-correct form still compiles. Reach for the
  strongest model. A cheap model's failure here is not "unfinished," it is *plausible and
  wrong*, which costs more to review than to have written.
- **A mechanical, fully-specified change** — add a counter, thread a field, apply a rename
  across known sites. A cheap fast model is correct here and the review is quick.
- **Research, design, or an experiment whose control has to be valid** — strongest model. A
  flawed control produces confident numbers that send the whole stream the wrong way.
- **Operational running and measurement** — the model barely matters; the fences do.

A mixed slate should get a mixed assignment. Assigning one model to every stream because it
is simpler to think about is how you either overpay for a rename or under-resource a port.

### Invocation that actually works (`cursor-agent`)

```bash
cursor-agent -p --force --model cursor-grok-4.5-high --output-format text "<prompt>"
```

Run through `zsh -l -c "..."` (node is only on PATH in a login shell) and background it for
anything non-trivial.

**`--force` is load-bearing and its absence is silent.** `--trust` trusts the *workspace*;
with `--trust` alone every shell call is rejected, so the worker writes files but cannot run a
single test — and you will not notice except that it never mentions running anything. `--force`
("Force allow commands unless explicitly denied", alias `--yolo`) is what permits execution.

Verify once per environment rather than assuming, with something it cannot guess:

```bash
cursor-agent -p --force --model cursor-grok-4.5-high --output-format text \
  "Run: git rev-parse --short HEAD. Report the exact stdout. If you cannot run shell commands, reply SHELL_BLOCKED."
```

Models: `cursor-grok-4.5-{low,medium,high}` (the bare alias `grok` is invalid);
`claude-opus-4-8-medium`. `cursor-agent --list-models` enumerates. Other flags that matter:
`--sandbox <mode>`, `--approve-mcps`, `--mode plan` (read-only).

ACP is a *different* transport, for editor/client integrations that answer
`session/request_permission` with `allow-once`/`allow-always`. Print mode has nothing to answer
it, which is exactly why `-p` without `--force` blocks. You do not need ACP for delegation.

## 2. File safety — the rules that exist because they were broken

A worker with `--force` can run `git restore`. Its blast radius is your whole working tree.

- **Commit before dispatching.** Always. Uncommitted work is the only thing at risk.
- **Do not edit files while a worker is running.** An unexpected diff looks to the worker like
  its own contamination, and a conscientious worker will reset it to HEAD. That is how real
  work gets destroyed — not malice, a reasonable inference from an unexpected state.
- **If you must edit during a run, immunise it in the brief**, explicitly, by path:
  > You WILL see unrelated modified files in `git status` under `<paths>`. They are MINE and
  > intentional. LEAVE THEM EXACTLY ALONE — do not revert, reset, or clean up a diff you did
  > not create.
- Always forbid `git checkout` / `restore` / `stash` and committing. You commit, after review.

## 3. One worker at a time — per working tree

Two workers sharing **one working tree** collide even with disjoint file sets, because both run
the test suite and each sees the other's half-written state as a failure. That is the whole
mechanism, and naming it correctly matters: the hazard is the shared tree, not concurrency.

So: **one worker per working tree, as many trees as you like.** Give each parallel stream its
own worktree and the false-red problem disappears, along with the §2 file-safety hazard — a
worker that can only see its own checkout cannot revert your work by inference.

Corollary that survives: do not run the gate yourself in a tree a worker is working in.

**What worktrees do NOT isolate.** They isolate files. Everything else is still shared, and
this is where parallel delegation actually goes wrong:

- **A real database or store.** Two streams mutating one store make each other's measurements
  meaningless, and the damage is silent — you get numbers, they are just not about anything.
- **A rate-limited or metered external service.** Concurrent streams contend for one budget.
  If a stream's job is to *measure* throttling, a second stream sharing the provider has
  corrupted the experiment before it started.
- **Ports, fixture files, caches, lockfiles, a shared index.**

Before dispatching parallel streams, list the non-file resources each one touches. Streams that
share one are sequential no matter how disjoint their code is. Treat a resource appearing across
several streams as a capacity problem to schedule, not a dependency to order.

**The stale-base trap.** If worktrees branch from the remote's default branch and you integrate
locally without pushing, every worktree created after your first merge silently starts from code
that is missing it. The worker then writes correct code against a wrong base and the conflict
surfaces at merge, attributed to the worker. Either base worktrees on local `HEAD`
(`worktree.baseRef: "head"`), or rebase each branch onto current main before you review it —
and re-run the gate *after* the rebase, because a green suite on a stale base is stale.

**Background workers die with the process.** In-process subagent state does not survive a
session exit; the work is simply gone. So make each stream's state durable outside the process:
write the brief to a file before dispatching, and require the worker to commit to its branch as
it goes. A lost worker whose brief is on disk and whose branch has commits is re-dispatchable.
One whose entire context was in memory is a restart.

## 4. Parallel streams: fence at assignment, own the merge

Most collisions are prevented when you hand out the work, not resolved when it comes back.

**Fence by ownership, explicitly, in the brief.** Name the directories and files the stream owns
and state that it may not write outside them. "Work only in X" is the single highest-value line
in a parallel brief. Then name the shared files it must *not* touch even though its change
would be easier if it did — those are the ones that generate the merge you cannot review.

**Compute the collision set before dispatch.** For every pair of streams, list the files and,
where you can, the functions both need to modify. This is recon work (§5), not guesswork. Two
streams that both rewrite one central file are not parallel; one of them is second.

**You merge. Workers never do.** Workers commit to their own branch and stop. You rebase,
re-run the gate yourself, review the diff, and integrate. Merging is irreversible enough that
it sits with whoever is accountable for the whole tree — and pushing to a shared remote sits
with the human, not with you.

**Order the merges by contention, not by finish time.** The stream that owns the most-contended
file merges first; the others rebase onto it. Merging the cheap stream first because it landed
first just means the expensive stream rebases across a moving target.

**A stream blocked on a human decision still starts.** Give it the research and the design; hold
back only the code that the decision changes. What you must not do is let it implement both
branches of an unmade decision — two live implementations of one behaviour is the defect that
§2 of the canon exists to prevent, and shipping it "for now" makes the decision harder, not
easier.

## 5. Recon before briefs

You cannot write a brief the worker can refuse (§6) until you know which of your premises are
load-bearing. Buy that knowledge first, with read-only workers whose only deliverable is
evidence.

- **Fence recon hard: read-only, and forbidden from spending money.** No writes, no commits, no
  branch checkouts in a shared tree, no run that bills a provider. A recon agent that "helpfully"
  runs the expensive pass has pre-empted the experiment you were designing.
- **Demand evidence, not conclusions.** Ask for `file:line`, command output, actual query
  results. Explicitly forbid recommendations and plans — those are yours, and a recon agent's
  plan will be reasoned from less than you know.
- **Require it to say what it could not determine.** The gaps are where your brief needs a stop
  condition. A recon report with no "could not verify" section has probably guessed somewhere.
- **Ask it to check the claim your plan depends on, by name.** Not "look at the STM code" but
  "verify or refute that this channel is dead, and show me the evidence chain." Point it at the
  load-bearing fact.

**Verify a premise before escalating the decision it implies.** When a recommendation rests on
an unverified claim, do not take the decision to the human yet — if the claim fails, the options
change and you have spent their attention on a question that no longer exists. Verify first,
then ask. This is the delegation-scale form of *verified beats assumed*: the cost of an
unverified premise is not just a wrong patch, it is a human decision made about the wrong world.

## 6. Writing a brief the worker can refuse

The brief is the whole job. Two lines belong in every one of them, ahead of the task-specific
structure, because they are what a worker cannot infer from the task:

> Changing correct code is a worse outcome than leaving a suspected bug unfixed. When
> uncertain, refuse.
>
> For any finding here that I did not prove: your first action is the test that fails on the
> current code, for the reason stated. If it passes, the finding is **REFUTED** — stop and
> report it refuted. Do not implement it anyway; do not tune the test until it fails.

The second line is what makes the worker the auditor's adversary rather than its executor, and
it is the cheapest place to break an audit→fix loop — at round one, with nobody being smarter.

Then the structure that has worked:

1. **What is verified, and what is not.** Say "these findings are verified; do not re-litigate
   them" for what you proved, and mark everything else as a hypothesis to test. Workers waste
   entire runs re-deriving things you already established — or, worse, accept a wrong premise
   because you stated it confidently. **Tier every finding you pass on** — *proven*, *traced*,
   *suspected* (`../bug-gate/SKILL.md`). The worker may act only at the tier it can re-derive
   from the code, and never on a *suspected* one. An untiered finding is a guess laundered into
   a premise.
2. **Required reading, by path.** Name the files whose docstrings carry the constraint. Add:
   *do not trust comments as evidence of behaviour; trace to the code that runs.* Where a file
   carries a `CORRECTNESS:` note, name it: *this property is verified — a finding that
   contradicts it must refute the named proof, not the code around it.*
3. **The class, not the instance.** If you brief three symptoms you get three patches. Name the
   root cause and require a sibling sweep with file:line evidence for each site.
4. **Stop conditions.** The most valuable line you can write is a condition under which the
   worker must STOP and report instead of implementing. Use it wherever your premise might be
   wrong — a data shape you assumed, a granularity you have not checked.
5. **The over-correction case.** Every honesty fix can be over-applied. Require a test proving
   the *correct* case is still allowed. A fix that silences a true statement is as wrong as one
   that asserts a false one.
6. **Mutation, not just green.** For whatever survived falsification: introduce a one-line
   break, confirm the *named* test fails, restore, confirm restoration — and report the
   mutation→test pairs.
7. **Fences.** The directories this stream owns and may write in; files not to touch even where
   it would be convenient; patterns not to reintroduce; the exact baseline numbers
   (`N passed / 0 failed`); and "iterate until green — you have shell access, do not hand back
   red work." In a parallel slate, add the non-file resources it may not use (the real store,
   the metered provider) and that it commits to its own branch and never merges.
8. **Licence to refuse.** End with:
   > If a premise above is wrong about the code, STOP and say so with evidence rather than
   > implementing it.

   This pays for itself. Refusals of a bad brief are the highest-value output you get.

## 7. Reviewing: verify, do not believe

A worker's report is a claim. Check, in this order — cheapest disqualifying check first:

- **Re-run the gate yourself.** Never accept reported numbers. Rebuild any changed
  cross-package types first (in this repo, `common/shared-types`) or a green typecheck is stale.
- **Check scope and fence.** `git status` / `git diff --stat` — did it touch what it said, and
  did it stay inside the directories it was given? A write outside the fence is a finding even
  if the change is good, because in a parallel slate it is someone else's merge conflict.
- **Deletions, not just additions.** A port that takes the source branch's version of a file
  silently drops anything main added since. There is no conflict marker for "this whole feature
  is gone." Diff the symbol sets in both directions and check what the change *removed*.
- **Read the diff, not the summary.** Especially: did it reuse the shared helper you named, or
  hand-copy the predicate? A mirrored predicate is the defect it was sent to fix, relocated.
- **Verify the load-bearing claim independently.** Pick the one fact the whole fix rests on and
  prove it from the code yourself. This is where wrong premises surface.
- **Look for what it left.** Reports have a "noticed, not fixed" section. Read it as the most
  interesting part. Decide each item: fix now, file, or accept — and say which.
- **Check the oracle's dimension.** A test can pass, be non-vacuous, and still be unable to fail
  on its named defect because it asserts the wrong axis (existence when the bug is position, or
  value, or order). Mutation testing does not catch this if the mutation shares the oracle's
  axis. Name the defect's dimension, then confirm the assertion reads *that*.
- **Correct your own findings out loud.** If your "genuine miss" turns out to be a misread,
  say so plainly and fix whatever misled you — usually a docstring that overstated its contract.

**A second round is a stop, not a step.** Delegation is stateless per dispatch, which is exactly
why loop degradation is invisible: round two audits round one's *output* as though it were the
original, with no access to the artifact it started from. So any artifact entering a second
audit→fix round **with no external symptom reported in between** stops and comes to the human.
Diff every round against the last human-approved revision, never against the previous round.
This is `bug-gate`'s three-strike rule lifted from the hypothesis to the loop.

**No round closes on model output alone.** A round ends at an execution — a suite you ran, a
flow you drove, an artifact you opened — never at a second model's agreement. Two models
concurring that a defect exists is not evidence that it does.

## 8. Where the worker cannot go

Know this before you plan, or you will brief work that cannot be done:

- **No browser.** Driving a real app, an authenticated session, or a fixture harvest is yours.
  Split such tasks: worker does code, you do the interaction, one commit at the end.
- **Green tests are not a working feature.** Reachability — is the new code called from a real
  user path? — is `done-gate` Layer 4 and it needs the actual product. In this session the
  single worst defect of the day was found only by driving the app, after two independent code
  audits had passed clean.

## 9. Progress

Background the worker, then watch it with a `Monitor` loop rather than polling by hand:

```
while kill -0 <pid> 2>/dev/null; do
  echo "running — $(wc -c <"$out") bytes, $(git status --porcelain | wc -l) files changed"
  sleep 180
done
echo "FINISHED"
```

The file-count is the useful signal: bytes-of-output stays 0 while it reads, and the first file
change tells you it has started writing. A worker touching a file you fenced off is a reason to
look immediately.

### Do not yield the turn while a worker runs

Use the **`Monitor` tool**, not a one-shot backgrounded wait. The difference decides who does
the scheduling:

- `Monitor` turns every stdout line into an event, so each 180s poll **re-invokes you**. You
  stay attached to the run.
- A backgrounded `until … done` wait emits **one** notification, at the end. Nothing pulls you
  back mid-run, so there is no progress signal and no reason to stay engaged.

**Never end a turn with "still running, waiting on it."** That sentence hands the human your
job. They then have to type "resume" to advance the loop — once per worker, for as many
workers as the task takes — and each poke is a turn where you reported nothing they could act
on. Observed failure: eight consecutive "resume" prompts across one session, every one of them
avoidable.

While the worker runs, do reviewer prep in the same turn instead of idling:

- write the verification commands you will run the moment it lands;
- read the code the change will touch, so the diff review starts warm;
- re-read your own brief and note which claims you intend to check rather than accept.

Then review as soon as the finish event arrives — in that same turn, without being asked.

Two reporting rules that follow from the mechanics:

- **Report file-count, not byte-count — but read the bytes the moment they appear.** In print
  mode (`-p`) output stays 0 for most of the run while the worker reads, so quoting "log: 0
  bytes" as status is quoting a constant. It does NOT stay 0 until process exit, though:
  the report lands while the process is still alive, and shell wrappers can linger for
  minutes after. So the first non-zero byte count is your cue to `cat` the log and start
  reviewing — do not wait for the process to disappear.
- **Match your `pgrep` pattern to THIS worker, not to the CLI.** A pattern like
  `cursor-agent.*-p --force` also matches other sessions' workers and the `zsh -c` wrappers
  that outlive the run, so a "still running" watch can hang long after your worker finished.
  Capture the pid at dispatch, or grep for something unique to your invocation.
- If you must state the worker is still running, pair it with something the human can act on —
  a fenced file it touched, a decision you need, a finding from your own prep. Bare "waiting"
  is not a status report.

## 10. Verdict

Report as the reviewer, not as the worker's spokesperson:

```
Delegated:   <what, to which model, on which transport>
Fence:       <what it owned — and whether it stayed inside>
Gate:        <numbers YOU ran, after any rebase>
Accepted:    <what survived review>
Changed:     <what you overrode, and why>
Corrected:   <where the worker was right and you were wrong>
Refuted:     <findings dispatched that could not be made to fail — unimplemented, with the test>
Left:        <noticed-not-fixed items, each dispositioned>
Merge:       <where this sits in the merge order, and what it blocks>
```

`Changed`, `Corrected` and `Refuted` are the point, and the three of them together are the
score — not `Changed` alone. A stream that ends in `Refuted: 2` did its job as fully as one that
ends in a merge; a stream whose only non-empty line is `Accepted` either rubber-stamped the work
or briefed something too small to delegate.

Carry the refuted count per source across dispatches. **An auditor whose findings mostly refute
is not a source to keep dispatching from** — that rate is the only signal you get that a
generator is producing resemblances rather than defects, and it is invisible inside any single
round.

Across a parallel slate, report per stream and never blend them into one verdict. One green
stream does not license merging its neighbour, and a summary that averages them hides exactly
the stream you should be worried about.
