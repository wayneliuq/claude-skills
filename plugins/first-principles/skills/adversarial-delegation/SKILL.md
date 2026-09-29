---
name: adversarial-delegation
description: Run a first-principles gate (bug-gate / build-gate / done-gate) by delegating implementation to a Claude worker (Sonnet 5.5 or Opus 5.5, chosen by an automatic triage) while acting as its adversarial reviewer, and optionally commissioning a cross-lineage second look from grok via cursor-agent on one well-scoped decision or diff. Use when a task is large enough to hand off but too consequential to accept on trust, when several such tasks must run in parallel without colliding, or when a consequential decision deserves an independent adversary. Encodes whether to delegate at all, the worker triage, the Sonnet-specific brief rules, the file-safety rules that stop a worker destroying your uncommitted work, how to fence parallel streams and own the merges, how to write a brief it can refuse — including why its first action on any finding you did not prove is the test that would refute it — how to run grok as an adversary whose findings must fail a test before they count, and what the reviewer must verify rather than believe.
---

# Adversarial delegation

Two roles, never collapsed. The **worker** (a Claude subagent) writes code and runs gates.
**You** are the adversarial reviewer: you set the charter, then try to break what comes back.
The value is in the asymmetry — the worker is invested in its solution, you are not.

A third role is optional: the **second look** (grok via `cursor-agent`, §1b), a model from a
different training lineage that attacks one well-scoped decision or diff. It never implements.

Canon: `../bug-gate/SKILL.md`, `../build-gate/SKILL.md`, `../done-gate/SKILL.md`. This skill
is the delegation mechanics those gates assume you have.

---

## 0. Delegate at all?

Delegation costs a plan, a handoff and a merge that doing the work yourself gets for free.
Anthropic measured multi-agent setups at 3–10× the tokens of a single agent on equivalent
tasks, and in every case it measured where the work was one dependent chain or fit in one
context, the lead model alone **at lower effort** came out ahead. So the default is to do it
yourself, and delegation has to earn its place.

**Do not delegate:**

- work you can finish in a handful of tool calls;
- one dependent chain — step two needs the full output of step one;
- work that fits comfortably in your own context and has no bulky output to quarantine;
- two pieces that edit the same file;
- anything needing frequent back-and-forth with the human.

**Delegate when at least one holds:**

- **Independent, sizeable tracks** — several pieces with an empty collision set (§4).
- **Bulky output you only need the conclusion of** — test runs, logs, wide file sweeps. The
  worker absorbs it and returns a 1–2k-token summary.
- **Routine work with a cost tail** — a solvable task that occasionally spirals is cheaper to
  let spiral at worker rates.
- **Work larger than one context window.**

**Never delegate verification of your own work to another Claude.** Anthropic's guidance for
Opus 5 and later is explicit: do not use subagents to verify or double-check your own work —
it adds cost with no quality gain, because the model already self-checks. The reviewer role
(§7) is yours, done directly. The only second pair of eyes this skill sanctions is a
*different lineage* (§1b), on a decision worth its cost.

Before building a multi-worker plan, compare it with yourself at lower effort. A plan that
beats your default effort but loses to your low effort is not a saving.

## 1. Choosing the worker — the triage

Implementation goes to a **Claude worker**, dispatched through the Agent tool with one of the
plugin's worker definitions. The definitions exist because the Agent tool's `model` argument
cannot set effort — effort lives only in an agent definition's frontmatter — and because the
`sonnet` / `opus` aliases resolve to different models on different providers. The definitions
pin full model ids.

| `subagent_type` | Model / effort | Takes |
|---|---|---|
| `first-principles:worker-sonnet` | `claude-sonnet-5-5`, medium | Fully specified, bounded work where a test decides the outcome: a bug with a repro, a mechanical change across known sites (rename, thread a field, add a counter), read-only recon that returns evidence |
| `first-principles:worker-sonnet-high` | `claude-sonnet-5-5`, high | Same shape, but longer or harder — many sites, an unfamiliar area, a fix whose test needs design |
| `first-principles:worker-opus` | `claude-opus-5-5`, medium | Long-horizon or multi-file work; a port or shared-state change where the almost-correct form still compiles; research, design, or an experiment whose control has to be valid; migrations; **anything that computes or transforms a number a user will read** |
| `first-principles:worker-opus-high` | `claude-opus-5-5`, high | The subtle end of the Opus column — a numeric core, a concurrency or ordering invariant, a change you have already seen a worker get plausibly wrong |

Assign it yourself, per stream, before writing the brief. Do not ask the human which model.

**The tie-break is the failure mode, not the size.** When a stream could go either way, ask:
*if the worker reasons shallowly, would the result still pass the tests?* If yes — the
almost-correct version compiles and goes green — it goes to Opus. A cheap model's failure
there is not "unfinished," it is *plausible and wrong*, which costs more to review than to
have written. If shallow reasoning would fail loudly, Sonnet is correct and the review is
quick.

Why numbers go to Opus regardless of size: a wrong pixel gets a bug report, a wrong number
gets silently trusted. The review cost of a subtly wrong statistic is unbounded, so it never
goes to the cheaper tier to save money.

Why Sonnet runs at **medium, never low**: at `low`, Sonnet 5.5 sometimes reports a change as
done without running a check that exercises it, and on long tasks it stops to check in. A
delegated "done" with no check behind it is the exact thing this skill exists to prevent.
Sonnet 5.5 is half Opus 5.5's per-token price, so medium is still the cheap lane.

Anthropic's own positioning, for when the table is not enough: Sonnet 5.5 for "well-scoped
everyday tasks, fixing bugs"; "for the hardest long-horizon work, an Opus model is the better
choice." Escalate past Opus 5.5 only if it still falls short at `high`.

**A mixed slate gets a mixed assignment.** One model for every stream because it is simpler to
think about is how you overpay for a rename or under-resource a port.

**Operational running and measurement** — the model barely matters; the fences do. Sonnet.

### Transport facts

| | Agent-tool subagent |
|---|---|
| Isolation | `isolation: "worktree"` gives its own checkout — but branched from the *default branch*, not your HEAD (see the stale-base trap, §3). To start from a prepared tree, dispatch without `isolation` and fence the worktree path in the brief |
| Parallelism | many, safely, one per tree |
| Visible to you | task notifications; `SendMessage` resumes it with context intact |
| Survives session exit | **no — in-process state is lost** (§3) |
| Starts with | its own system prompt, your brief, CLAUDE.md, a git-status snapshot. **Not** your conversation, **not** your auto-memory, **not** your output style |

If the Agent tool is unavailable or the worker definitions do not resolve, fall back to
`subagent_type: "general-purpose"` with `model: "claude-opus-5-5"` (effort then follows the
session) and **report the downgrade** — a silent one makes two runs incomparable.

## 1b. The second look — grok as adversary, never as author

grok via `cursor-agent` is **not an implementation lane.** Its value is a different training
lineage, which catches errors a Claude reviewer shares assumptions with. Its measured profile
is the reason for every rule below:

- **Recall useful, precision poor.** In one independent test, 8 of 10 grok review findings
  were false positives (n=1 — treat as a direction, not a rate). Practitioner reports say it
  catches real bugs Claude models miss.
- **Not cheaper in practice.** List output price is below Sonnet 5.5's, but grok 4.7 burns
  roughly twice the output tokens of 4.6, which cancels most of it.
- **Weak on long-horizon work and unmeasured on math.** No independent numeric-reasoning
  result exists for 4.6 or 4.7.
- **An unreliable transport.** Dispatches have dropped mid-run with no output, twice in a row;
  a dropped stream can also leave the worker still writing files (§9).

**Use it for** one consequential, *well-scoped* question: a design decision about to be
committed to, a diff you are about to accept, a claim a fix rests on. The scope must be small
enough that every finding it returns can be checked. **Do not use it** for open-ended audits,
for anything on the critical path, as the final word on correctness, or as a substitute for
an external oracle on numeric code.

**The brief for a second look:**

1. **The artifact and the question, nothing else** — the diff or decision, the one claim to
   attack, the files that carry the constraint. Not your reasoning for the answer you favour.
2. **Report everything, with a confidence on each.** "Only high-severity" makes models
   silently drop real findings; you filter afterwards.
3. **Every finding must name the test or command that would fail if it is real.** A finding
   with no falsifier is a suspicion, and is tiered as one.
4. **Read-only.** It must not write, edit, checkout, restore, stash or commit. Enforce this in
   the brief — `--mode plan` returns nothing under `--output-format text`.
5. **Write the report to a named file as you go**, so a dropped transport leaves a partial
   file rather than nothing.

**Then you prove or refute each finding** — run the falsifier it named, against the current
code. Only a finding whose falsifier fails is acted on; the rest are logged as `Refuted`
(§10). Carry grok's refute rate across dispatches: a second look whose findings mostly refute
is costing review time without buying anything, and that is the signal to stop commissioning
it.

**No round closes on model agreement.** grok concurring with you is not evidence; neither is
grok disagreeing. An execution decides (§7).

### Invocation that actually works (`cursor-agent`)

```bash
cursor-agent -p --force --model grok-4.7-medium --output-format text "<prompt>"
```

Run through `zsh -l -c "..."` (node is only on PATH in a login shell) and background it.
Pass the brief from a file through a tiny runner script (`prompt="$(cat "$1")"`) — inlining it
in a double-quoted `zsh -c` breaks on backticks and `$`.

**Model: the newest grok generation at medium effort, never a `-fast` id.** As of 2026-09-28
that is `grok-4.7-medium`. Both the version **and the id's prefix** go stale — 4.6 was
`cursor-grok-4.6-medium`; 4.7 dropped the `cursor-` prefix — so treat the *rule* as the
instruction and the id as today's answer to it:

```bash
cursor-agent --list-models | grep -i grok   # newest generation wins; take its non-fast medium
```

- **Not every generation exposes every tier.** If the newest has no `medium`, take the lowest
  non-`fast` tier above it rather than dropping back a generation.
- **Never a `-fast` id.** Its failure mode is plausible and wrong. (4.7's fast labels also
  contain zero-width characters; copy ids from `--list-models`, never retype them.)
- **`xhigh` is not worth it here** — it roughly doubles tokens for a few points in the
  vendor's own numbers.

**`--force` is load-bearing and its absence is silent.** `--trust` trusts the *workspace*;
with `--trust` alone every shell call is rejected, so the worker can read but cannot run the
falsifier it proposes — and you will not notice except that it never mentions running
anything. `--force` (alias `--yolo`) permits execution; read-only is enforced by the brief.

Verify once per environment rather than assuming, with something it cannot guess:

```bash
cursor-agent -p --force --model grok-4.7-medium --output-format text \
  "Run: git rev-parse --short HEAD. Report the exact stdout. If you cannot run shell commands, reply SHELL_BLOCKED."
```

An unknown id fails fast, which is why the probe is worth its one call. If the probe or the
dispatch fails, **skip the second look and say so** — do not retry a transport that has
failed once with no output, and do not substitute a Claude reviewer (§0).

## 2. File safety — the rules that exist because they were broken

Any worker with a shell can run `git restore` — a Claude subagent dispatched without
`isolation`, and a `cursor-agent` second look under `--force`. Its blast radius is the whole
working tree it runs in.

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

**Give a lead a time budget when you can estimate one.** Opus 5.5 paces itself to an
`elapsed Ns / budget Ns` line and parallelises more to fit it. The budget is advisory — keep a
real timeout — and under pressure it may verify a little less, so do not use it on a numeric
stream.

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

### What a Claude worker needs that you would not think to say

A subagent starts blank: its own system prompt, your brief, CLAUDE.md and a git-status
snapshot. The worker definitions' system prompts already carry the generic rules — run a real
check before reporting done, finish the whole task, add nothing unrequested, launch no reviewer
subagents, never checkout/restore/stash/commit, write the report as you go. The brief carries
everything specific:

- **Paste in the memories that apply.** Auto-memory does not reach a subagent. If a
  memory records a trap in the area the stream touches, quote it; a pointer to the memory
  file is not enough.
- **Name the scope literally.** Sonnet 5.5 does what the brief says and does not infer what
  it leaves out. "Fix the three call sites" gets three; if you mean every site of the
  pattern, say "every site, found by `<search>`, with file:line for each."
- **Name the checks that count.** The definition tells it to run a real check; the brief
  names which — the exact test scope, the typechecker, the build. A worker left to choose
  runs the fast one and skips the one that catches its class of mistake.
- **Name the return.** The format of the report, its path, and its size (a 1–2k-token
  summary plus the evidence you asked for). Ask for everything it noticed with a confidence
  on each; "only report serious issues" makes it drop real findings silently.
- **Give the report a file path** and say *write it as you go*. A stalled worker then leaves a
  partial file; a refusing one leaves a complete one. Without it the two are
  indistinguishable.

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

- **Green tests are not a working feature.** Reachability — is the new code called from a real
  user path? — is `done-gate` Layer 4 and it needs the actual product. In this session the
  single worst defect of the day was found only by driving the app, after two independent code
  audits had passed clean.

### The browser is a delegation, not a limit

**Corrected 2026-08-17. This section used to say "no browser — that is yours." That was wrong in
the case that matters most.** When *you* cannot drive a browser — an unattended or scheduled run
is refused outright: *"Dev servers can't be started from unattended sessions"* — the restriction
is on your harness, not on your worker. A worker with a real shell can start a dev server, run
Playwright and report what it saw. So a visual question is not unanswerable; it is
**delegable**. Verified working (on a `cursor-agent` worker, 2026-08-17): a low-effort worker
logged into a local stack, drove the app, selected a node and returned DOM measurements plus a
screenshot that settled a question two prior runs had returned to the queue as unworkable.

Send observation to `first-principles:worker-sonnet`. Reading a rect, a computed style and a
scene graph is not a reasoning task, and the cost difference is real if you do it every run. A
Claude subagent's shell has not yet been verified to start a dev server from an unattended
session; if it is refused, a `cursor-agent` observation worker is the permitted fallback —
observation writes no product code, so it is not the implementation lane §1b rules out.

An observation worker gets its **own worktree** — its collision set with code streams is empty,
so it runs in parallel and costs no wall-clock.

Six things belong in every browser brief, each because omitting one cost a cycle:

1. **Build the workspace's shared type packages in that worktree first.** A dev server that
   cannot resolve a workspace package 500s on module requests and never mounts the app — which
   looks exactly like a failed login and sends the worker off diagnosing auth.
2. **Pin the port and the hostname**, and say why. If the backend's CORS allows one origin, any
   other port *or* the loopback IP fails every API call, and the symptom is indistinguishable
   from broken credentials.
3. **The page must authenticate itself** if the credential is an HttpOnly cookie — a shell-side
   `curl` login puts the cookie in curl's jar and leaves the browser anonymous.
4. **State the minimum viewport.** Responsive shells that replace the app below a breakpoint
   present as "the app did not load".
5. **Demand a machine-readable artifact** — a JSON report and a screenshot at paths you name.
   Read those yourself. The prose summary is the least reliable part of what comes back; the
   JSON is what you can quote.
6. **Ask for the falsifier, not a verdict.** "Report every conjunct's value", "report width and
   height", "if the chart object is absent, say so". A mounted element with zero height is a
   third answer that neither side of a disagreement predicts, and only a brief that asks for
   numbers will surface it.

**Two things this still does not buy.** A worker can establish that a surface mounted, is sized
and is visible; it cannot tell you whether a colour is *right* — that is taste, and taste stays
with the human. And a surface showing its empty state proves the surface, not the drawn content.
Report which of the two you actually got, because they are easy to conflate and only one of them
discharges Layer 4.

**Never let credentials into a brief, a report, or a file the worker leaves behind.** Point at a
path, require it be read programmatically, and require the copy be deleted.

## 9. Progress

**Agent-tool workers** run in the background and re-invoke you with a task notification when
they finish, so there is nothing to poll. Do reviewer prep (below) while they run, and review in
the turn the notification arrives. The rest of this section is for `cursor-agent` dispatches,
which notify nobody.

**Before staging anything after a `cursor-agent` run, confirm the process is gone**
(`ps -eo pid,command | grep '[c]ursor-agent'`). A dropped transport kills the output stream,
not the worker, which can keep writing files for minutes — a gate run and a `git add` in that
window commit work nobody reviewed. Stage by path, never `-A`.

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
Delegated:   <what, to which worker definition, and why the triage put it there>
Fence:       <what it owned — and whether it stayed inside>
Second look: <none | grok on <question>: N findings, N proven by a failing falsifier, N refuted>
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
