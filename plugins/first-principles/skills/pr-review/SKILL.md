---
name: pr-review
description: "Adversarially review a pull request and fix what the review finds, in that PR's branch. Use for \"review this PR\", \"review PR #n\", or \"adversarially review\" a PR. Not a findings list: every proven defect is fixed and pushed as an atomic commit. Runs in a fixed order, each phase with an exit criterion tracked in a review ledger: map the PR's intents to its commits, files and units; establish a working baseline by sweeping every user-reachable combination in the running app (adversarially verified, saved as a replayable matrix); realign intent — for each feature, separate constraints the user needs from constraints that exist only because the structure was wrong, and rebuild to the structure that needs fewer of them; then simplify component by component (correctness, performance, tests, bloat, living docs), replaying the matrix after every change. Cross-checks every open issue and rewrites the PR title and body as user-facing release notes. Never marks a draft PR ready. The release stage (pre-release / alpha / GA) decides how much rebuild is allowed."
---

# pr-review

A PR is a claim: *this problem exists, this change fixes it, and this is the right shape
for the fix.* The review attacks all three, then repairs what it breaks — in the PR
branch, commit by commit — so the PR that comes out is one the reviewer would have
written.

The phases run in a fixed order because each one is the precondition of the next:

1. **Map** — know what the PR intends, and where each intent lives.
2. **Baseline** — see it working in the real thing, and save that observation as a matrix
   you can replay. Nothing is refactored before this exists: a refactor is only safe
   against a behaviour you have watched work.
3. **Realign intent** — per feature, keep the constraints the user needs, and rebuild away
   the ones that exist only because the structure was wrong.
4. **Simplify** — component by component, on the realigned structure.
5. **Close out** — issues, final sweep, gate, release notes.

Every phase ends at an **exit criterion**, not at the end of its steps. A phase is done when
its criterion holds, however much work that takes.

Canon: `../principles/SKILL.md` — proven / traced / suspected, fixing the class, test value,
and what "verified" means. Mechanics this skill leans on rather than restates:

- `../adversarial-delegation/SKILL.md` — every subagent, every browser worker, and every
  grok second look.
- `references/bug-shapes.md` — the bug catalog.
- `references/bloat-shapes.md` and `references/test-value-by-domain.md` — the bloat catalog,
  and where the test-value floor sits per layer.

---

## 0. Inputs — read them, default them, state them

Open the review by stating each input in one line. If the user gave it, use it; if the
project's instructions (`CLAUDE.md`, `AGENTS.md`, contributing docs) settle it, use that;
otherwise take the default and say so.

| Input | Default |
|---|---|
| **PR** | the PR for the current branch (`gh pr view`); ask only if there is none |
| **Stage** | read from project instructions; if silent, **ask** — it changes what may be rebuilt |
| **Mode** | **find and fix** |
| **Subagents** | at most **3 concurrent**, dispatched through adversarial-delegation |
| **New tests** | none net-new unless the PR adds a net-new component |

**Stage decides the rebuild budget:**

| Stage | What that permits |
|---|---|
| **Pre-release** — no users; all data is test data | Rebuild, rename, reshape freely. No migration cost, no backward compatibility. This is the cheapest window the project will ever have for a refactor, and the review should spend it. |
| **Alpha / private testers** | Reshape freely, but data a tester created is real: a shape change owes a migration that carries their rows forward. API compat still not owed. |
| **GA** | Rebuilds need a migration *and* a compatibility story; propose a large rebuild as an issue rather than landing it in someone's PR. |

## 1. Hard rules

- **Never convert the PR from draft to ready.** Not with `gh pr ready`, not via the API,
  not as a last step "since everything passed". That is the owner's call, every time.
- **Work in this PR's branch only.** No other branch, no base branch, no new PR. Check out
  the PR head (`gh pr checkout <n>`) and confirm `git branch --show-current` before the
  first edit.
- **Find and fix, not findings-only.** A proven or traced defect is fixed and pushed. A
  suspected one is either promoted by a repro or logged as suspected — never fixed on a
  hunch (principles §2).
- **No refactor before the baseline** (§4 exit). No refactor lands without the matrix
  replayed after it.
- **Atomic commits, pushed to the PR branch.** One concern per commit, a message that says
  what the user now sees, staged by explicit path. Obey the project's commit conventions
  (trailers, hooks); never `--no-verify`.
- **Ambiguous fix → pick the simplest, and record the choice** in the commit message and
  the verdict. Escalate only what is genuinely the owner's decision (§9).
- **No net-new unit tests** unless the PR introduces a net-new component. Otherwise, make
  the existing tests more load-bearing (§6c).

## 2. The review ledger

Exhaustive fails silently: a long session is summarised, and what it had not yet covered
is forgotten rather than skipped on purpose. So the review keeps its state in a file, not
in context.

Create `pr-review-<n>.md` in the scratchpad (or another untracked location — never commit
it). It holds:

- **The map** (§3): every intent, every commit, every changed file, every unit.
- **The matrix** (§4): every combination, how to run it, and its latest result.
- **The intent ledger** (§5): per feature, every constraint and its disposition.
- **A disposition per file per phase**: each mapped file is marked for baseline, realign and
  simplify — *done*, *unaffected because …*, or *skipped because …*. A blank cell is a
  miss.

Update it as each item closes, not at the end of a phase. After a context summary, or on
resuming, re-read the ledger before doing anything else and continue from its first open
cell.

## 3. Map — what the PR intends, and where

Load, before judging anything:

1. `gh pr view <n> --json title,body,isDraft,baseRefName,headRefName,closingIssuesReferences,files`
   — and confirm `isDraft`. Record it; §1 depends on it.
2. The full diff against the merge base, not the last commit: `git diff <base>...HEAD`, and
   the commit list: `git log --reverse --format='%h %s%n%b' <base>..HEAD`.
3. Every issue the PR claims to close, and the PR's own stated premise, **quoted** — you
   are about to test it, so write down exactly what it says.
4. **Every** open issue: `gh issue list --state open --limit 1000 --json number,title,body,labels`.
   The default limit is 30, and a truncated list is a silent miss. Issues are behaviour real
   users hit: the ones that touch this PR's surfaces feed the matrix (§4) and the intent
   ledger (§5). Their dispositions are settled in §7.
5. The project's living docs index and the rules the project holds itself to.

Then build the map: **intent → commits → files → units.**

- **Intents** are the user-visible things the PR sets out to do — one line each, in user
  terms. Derive them from the commit messages and the PR body, then check each against
  its diff.
- **A commit message is a claim, not the truth.** Read each commit's diff (`git show <sha>`)
  and flag every commit whose diff does more, less or other than its message says. Those
  mismatches are where unannounced changes hide; each gets an intent of its own.
- **Flag fix-on-fix chains**: a later commit in the PR that patches an earlier one — a guard
  added after the feature, a special case for an input the first version mishandled, a
  revert-and-redo. A chain is the strongest early sign that the structure is wrong; each one
  goes into the intent ledger as a constraint to examine in §5.
- **Messages too vague to map** ("wip", "fix", "address review") → cluster the files by what
  their changes do, and name the intent yourself.
- **Contract-bounded units** — the smallest pieces with a stated interface (a module, a
  service, a component with its props/events, a table with its readers). Every changed file
  belongs to at least one unit; every later phase works per unit.

**Exit:** every commit maps to an intent, every changed file to a unit, every mismatch and
fix-on-fix chain is flagged — all in the ledger.

## 4. Baseline — see it work, and save what you saw

The baseline is a real-user sweep, run first and exhaustively, because everything after it
is judged against it. A refactor is only proven safe by replaying an observation of working
behaviour; without one, simplification is guesswork.

### 4a. Build the matrix

A feature or fix is judged against everything it touches, not just itself. For each intent,
name the **surfaces** it meets — the features, types, modes, settings and data states it can
be combined with — and enumerate **every combination a user can reach**.

Example: a new plot type is reviewed against every other plot type it can be plotted with,
and every statistic is checked on the new type. A fix is swept the same way, across every
surface where the fixed behaviour appears.

When the full product of axes is too large to run, cover **every pair** of values across all
axes, and the **full product on the risky axes** — the ones the PR changed, the ones a
fix-on-fix chain touched, the ones an open issue names. Write down which combinations were
cut and why; an uncovered combination is never silent.

Each row records: the combination, the exact steps to run it (so it can be replayed by
someone with no context), the expected result in user terms, and the observed result.
Unreachable combinations are named as such, with the reason.

### 4b. Run it — for real, and verified adversarially

- **In the running app**, as the user would: the browser, the CLI, the actual UI. Use real
  data and real interactions; a mocked path does not count as a sweep. When you cannot
  drive the browser yourself, it is a delegation (adversarial-delegation §8), not a gap.
- **In code**, through the same entry points: contracts, APIs, persistence — save, reload
  and migrate each combination; every writer and reader of a changed value still agrees.
- **Every result is verified adversarially, whoever produced it.** A worker's sweep is
  reviewed under adversarial-delegation §7 — read its machine-readable artifacts, re-run a
  sample of rows yourself, check the oracle's dimension. A sweep you ran yourself gets the
  same scrutiny: for each pass, ask what the observation would have looked like if the
  feature were broken, and confirm it did not look like that. An empty state proves the
  surface, not the content.

### 4c. Triage the failures

Tier every failure (principles §2), then split by **where the cause lives**:

- **Local cause** — a wrong value at one site, the structure otherwise sound → fix it now,
  at the producer, with its siblings. One commit per concern.
- **Structural cause** — the failure exists because of how the unit is shaped (two owners of
  one value, a state the design allows but should not, a path that should not exist) →
  do **not** patch it here. Mark the row **known-failure: structural**, and add the cause to
  the intent ledger for §5. A band-aid now is work §5 throws away.

### 4d. Gate

Run the project's fast gate (typecheck, lint, the changed packages' tests). Failures are
triaged as in 4c.

**Exit:** every reachable row is **green** or **known-failure: structural** with its cause in
the intent ledger; the gate is green; the matrix is saved and replayable. Only now may
anything be refactored.

## 5. Realign intent — needed constraint, or structural artifact?

For each feature (each intent in the map), step back from the code. The question is not
*is this code right* but *does this constraint need to exist at all?*

### 5a. Necessity — does this change need to exist?

**Do not trust the premise.** The PR description and the linked issue are the author's
belief, not evidence. For each intent:

1. **Revert it in your head** (or actually, on a scratch branch). What user-facing
   behaviour changes? Name it concretely: what the person would see, click, or be told
   differently.
2. **Would a real user notice?** Picture the actual user of this product doing their
   actual job. If nobody would ever see the difference, the change is ballast.
3. **Can the problem actually occur?** Trace the input that reaches the fixed branch, from
   a real entry point — the matrix tells you which combinations reach it. A problem with no
   reachable input is theoretical — do not keep a fix for it.

Dispose every intent as **necessary** (with the user-visible behaviour it protects),
**unnecessary** (revert it, one commit, and say what was reverted), or **ambiguous** —
reachable but only under conditions you cannot confirm, or visible but of unclear value.
Ambiguous goes to §9. Do not guess on the owner's behalf.

### 5b. The intent ledger — essential or accidental

For each necessary intent, write in the ledger:

- **The end behaviour**, in user terms — what must be true for the person using it.
- **Every constraint the implementation carries**: each guard, special case, ordering rule,
  retry, clamp, fallback, sync step, flag, and every fix-on-fix chain and structural
  known-failure from §3–§4.
- **A label for each:**
  - **essential** — the user or the domain imposes it; it would exist in any correct design
    (a unit must be non-negative because negative mass is meaningless);
  - **accidental** — it exists only because of how the code is structured; it would vanish
    in a from-scratch design (a cache must be invalidated in three places because three
    places own the value).

  The test: *would this constraint exist in the simplest design that delivers the same end
  behaviour?* If not, it is accidental. A guard at the consumer, a retry, a clamp, a special
  case for one input — these are usually accidental: the producer is still wrong.

### 5c. Rebuild to the structure that needs fewer constraints

Where a unit carries accidental constraints, design its from-scratch structure **as
abstractly as possible** — its states, the owner of each value, the flows between them — not
its code. Then compare with what exists. The rebuild wins when it has **fewer states, fewer
owners of one value, fewer paths to the same behaviour, or fewer constraints** — and delivers
the same end behaviour or better — not when it is merely different or shorter. Every
accidental constraint it removes, and every structural known-failure it fixes, is the
evidence.

- **Performance fixes fold in here.** A slow path is usually a shape problem.
- **Scope:** a rebuild may reach beyond the PR's units only where an accidental
  constraint's cause lives there. Otherwise, file it as an issue with the ledger entry as
  its body.
- **Get a second look on every rebuild decision** via adversarial-delegation §1b (grok
  through `cursor-agent`). Give it the unit's end behaviour, its constraints and the current
  code — not your preferred answer — and one question: *which of these constraints exist only
  because of the structure, and what structure would need none of them?* Tell it the stage
  in plain words — for pre-release: "we are pre-release, with no users and only test data;
  this is the best window for any refactor or rebuild; do not weigh refactor cost, migration
  cost, or backward compatibility." Its findings are hypotheses: only those whose named
  falsifier fails, or whose simpler shape you can actually write, are acted on.

**Implement the simpler shape** within the stage's budget (§0). Delete the old path in the
same change — two live paths for one behaviour is never acceptable, including the form where
the old path survives behind a fallback. Use subagents when a rebuild is large enough to
hand off — through adversarial-delegation's triage, at most three at once, each fenced to
disjoint files, each reviewed rather than believed.

**After each rebuild, replay the matrix rows it touches.** A row that was green and is now
red is a regression in the rebuild — fix the rebuild, not the row. A structural
known-failure the rebuild was meant to fix must now be green.

**Exit:** every intent is necessary-with-behaviour, reverted, or escalated; every constraint
is labelled; every accidental constraint is removed by a rebuild, or escalated, or filed with
a reason it could not be removed in this PR; no structural known-failure remains; the matrix
is green.

## 6. Simplify — component by component

Now, on the realigned structure, go unit by unit through the map. For each unit, run every
pass below, mark it in the ledger, and **replay that unit's matrix rows before moving on**.

### 6a. Correctness

Run the bug catalog over the unit and its reachable neighbours as a hypothesis generator,
every finding tiered. Two checks always run, because they are where PRs most often go wrong:

- **Every writer, every reader.** For each value the PR changes the shape of, enumerate every
  producer and consumer — including rows written before the change, cold reloads, and
  migrations. Each is **updated**, **unaffected because …**, or **skipped because …**.
- **Every sibling.** A defect at one call site has siblings; search for the shape and fix
  them together.

A finding the matrix did not catch is a missing row: add it.

### 6b. Simplification

Run the bloat catalog over the unit: duplicated logic, a hand-copied predicate where a
shared helper exists, indirection with one caller, configuration nobody varies, a branch
for a state the realigned structure no longer allows. Reuse what exists; prefer the change
that removes a branch or a state over the one that adds a guard.

### 6c. Tests — load-bearing or gone

Apply the two test-value questions to every test the unit's changes add or touch:

1. Can it fail for a reason a user would care about?
2. Can a correct refactor leave it green?

The rebuild in §5 makes this pass sharper: a test that broke under a behaviour-preserving
rebuild was pinned to structure, not behaviour.

**Remove spurious tests.** Spurious means any of:

- a "regression" test for a regression whose cause was never known — it guards a guess;
- a test that is not honest — it mocks its own subject, or asserts what it just set;
- a test that is not load-bearing — no user-relevant defect would turn it red;
- a test written for a bug that is now fixed at the root, where the root fix makes the old
  failure unreachable — unless it asserts an invariant that still holds and could break;
- a change-detector — it pins an undecided design, an implementation detail, or source text.

For every deletion, write the one sentence naming the defect it could not have caught. If
that sentence cannot be written, the test stays.

**Refactor what survives** toward more load-bearing coverage: collapse example batteries
into one property, move a canonical-path test to assert the invariant across every writer,
replace a mocked boundary with the real one. **No net-new unit test** unless the PR adds a
net-new component — and then the smallest set that can fail on that component's contract.

A regression test that stays or is rewritten must fail against the unfixed code. Run it
there once, and record that you did.

### 6d. Historical bloat and living docs

**Remove from the branch:** comments narrating history ("previously", "was changed to",
"fix for #n"), dead code and unreachable arms, commented-out code, stale TODOs, generated
artifacts, and planning or scratch docs that describe work rather than the system.

**Before deleting anything, extract what should persist** — anything that affects future
development or maintenance: a constraint, a non-obvious reason, a trap someone fell into.
Fold it into the living doc that owns that subject, found through the project's docs index.
Never create a parallel doc where one already owns the topic.

**Update the living docs** the unit's change touches, so they describe the system as it now
is. **Record each design decision the PR settles** — including each essential constraint
from the intent ledger whose reason is not obvious from the code — as a locked-in decision
that can be revisited: what was decided, the reason, the date, and what evidence would reopen
it. A decision without its reopen condition reads as permanent and stops being questioned.

**Exit:** every unit in the map has a disposition for every pass in the ledger, and its
matrix rows are green.

## 7. Open-issue dispositions

The issues were read in §3. Settle each one against the branch as it now is:

| The issue is | Do |
|---|---|
| **resolved by this PR** | confirm it against the code and the matrix, not the title; add `Closes #n` so it closes atomically when the PR merges — one `Closes` per issue, on the release-notes line of the change that resolves it (§10) |
| **in tension with a decision this PR made** | reconcile it — adjust the code or the issue text — if the right answer is clear; otherwise escalate (§9) |
| **a real bug, unfixed** | reproduce it; proven or traced → fix it in this branch with `Closes #n`, and add its row to the matrix; suspected → comment what you tried, leave it open |
| **a net-new feature** | if this PR changed a premise the issue rests on, update the issue text to match; otherwise leave it alone |
| **unrelated** | leave it alone; no comment |

Most issues are unrelated. Report only the non-trivial dispositions.

## 8. Final sweep, gate, push

Simplification breaks things too, and a per-unit replay misses interactions between units.

1. **Replay the whole matrix**, every row, in the running app — verified as in §4b.
2. **Run the project's full gate** after the last commit. A lane that refused is not a pass.
3. Any red → back to the phase that owns it (local defect → fix; structural → §5), then
   replay again.
4. Push to the PR branch.

**Exit:** full matrix green, full gate green, every commit pushed.

## 9. Escalation

Escalate only what is the owner's decision: which behaviour the product should have, what
the user should be told, whether a cost is worth paying. Differences only in code shape are
yours — pick one and note it.

Write each escalation in this order, with the technical detail **below** it and marked
optional:

1. **The decision, in one plain sentence.** No file paths, no API names.
2. **What each option means for the person using the product** — what they would see, or
   stop seeing. If an option changes nothing visible, say so.
3. **Your recommendation**, and the tradeoff you are accepting.

Batch escalations; do not block on them. Keep fixing everything else and bring them all at
the end, smallest number of genuine forks first — and if one answer dissolves others, ask
that one and say so.

## 10. Rewrite the PR message as release notes — the final step

Last, after every commit is pushed, because the message describes what the branch *now*
does, not what the author first intended or what the review changed along the way.

**Regenerate, never append.** Build the body from `git log <base>..HEAD` and the final diff.
A change the review reverted leaves the notes with it; review narration ("addressed
feedback", "reviewer found") never enters them.

**Structure.** If the project prescribes a release-notes format, use it exactly. Otherwise:

```
## New features
## Fixes
## Improvements
## Behind the scenes        ← refactors, tests, docs, CI, chores
## Verification             ← what ran, and what did not
## Needs your attention     ← migrations, deploy-affecting changes, anything irreversible, open escalations
```

Omit an empty section rather than writing "none".

**Each line:**

- **One change, one line, in user terms** — what the person using the product now sees or
  can do, not which function moved. "Plots keep their colours after reload", not "fix
  colour-scale cache invalidation in restyle path".
- **`(Closes #n)` inline on the line of the change that closes it** — one per issue, never a
  grouped list, so each issue closes with exactly the change that fixed it.
- **Concise.** No preamble, no summary paragraph restating the list, no filler adjectives
  ("robust", "seamless", "comprehensive"), no hedging. Positive phrasing: say what now
  works, not what no longer breaks, where both are true.
- **Honest.** `Verification` states what actually ran — the matrix size, how many rows ran
  in the app, which were cut — and a skipped lane is written as skipped. Nothing claims more
  than the commits, the matrix and the gate show.

**Title:** a plain summary of the user-visible change, matching the project's title
convention if it has one.

Apply with `gh pr edit <n> --title … --body-file …`, then re-read it with `gh pr view <n>`
to confirm what landed.

**Confirm the PR is still a draft** (`gh pr view <n> --json isDraft`). If it somehow is not,
say so first in the report.

## 11. Report

```
PR:          <#n — title> · draft: yes · stage: <stage> · branch: <head>
Premise:     <quoted claim> → <held | partly held | did not hold: why>

Map:         <n> intents · <n> commits · <n> units · <n> message/diff mismatches · <n> fix-on-fix chains
Baseline:    <n> rows (<n> in the app · <n> via code · <n> unreachable · <n> cut: why)
             <n> local fixes · <n> structural → realign
Realign:     <n> necessary · <n> reverted (what the user would have lost: nothing) · <n> escalated
             constraints: <n> essential · <n> accidental → <n> removed · <n> filed · <n> escalated
             <per rebuilt unit: old shape → new shape — states/owners/paths/constraints removed>
  Second look: <grok on <question>: N findings, N proven, N refuted | skipped: why>
Simplify:    correctness <n> proven fixed · <n> traced fixed · <n> suspected logged
             tests <n> removed (each with the defect it could not catch) · <n> refactored · <n> new (new component only)
             bloat/docs <removed> · <folded into <doc>> · <decisions recorded>
Issues:      closes <#a, #b> · fixed <#c> · reconciled <#d> · escalated <#e>
Choices:     <ambiguous fixes where the simplest was picked, one line each>
Final sweep: <n>/<n> rows green · gate <command, result, what did not run>
Commits:     <n pushed, one line each>
PR message:  <rewritten as release notes — title, sections used>

Needs your decision:
  <escalations, §9 format>
```
