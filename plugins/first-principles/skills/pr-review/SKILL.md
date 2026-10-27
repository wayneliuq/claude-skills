---
name: pr-review
description: "Adversarially review a pull request, a change, or a whole codebase, and fix what the review finds, on the PR's branch or a review branch of its own. Use for \"review this PR\", \"review PR #n\", \"review this change\", \"review this codebase\", or \"adversarially review\" anything. Not a findings list: every proven defect is fixed and pushed as an atomic commit. Runs in order: map the target's intents; sweep every user-reachable combination in the running app and save it as a replayable matrix, with the gate, suite counts and timings it must hold; hand the owner a short hands-on test run, recorded automatically; then the primary phase, the constraint trace: follow every value the target touches to all its owners and readers across the whole repo and stored data (never bounded by the diff), count them before changing anything, and for each constraint either remove it by a shape that makes its failure impossible or leave exactly one owner, proven by a search and a test seen failing first; check every reader of every value a fix changes; put each consequential change to second-look models from another lineage, configured as swappable lanes; replay the matrix after every change. Cross-checks every open issue and, for a PR, rewrites it as one-screen release notes. Never marks a draft PR ready. The release stage (pre-release / alpha / GA) decides how much rebuild is allowed."
---

# pr-review

A change is a claim: *this problem exists, this change fixes it, and this is the right shape
for the fix.* A codebase is the same claim made by every change that built it. The review
attacks all three and repairs what it breaks, so what comes out is what the reviewer would have
written: correct, safe, smaller, and still a pleasure to use.

The target can be a PR, a few changed lines, or a whole codebase; the review is the same.
What it traces is never bounded by what changed: a three-line change can break a rule held in
twenty files, so the constraint trace (§5) follows values, not the diff.

Order of importance, as in every judgement below: **correct, safe, holds under real use,
tested, fast, lean.** Lean still matters: every extra line is read, tested and fixed later.

What finds bugs, measured on past reviews (axiph #825–#1040): the in-app combination sweep
found the most, second looks from another model the next most, outside oracles (R) backed the
numeric fixes, and the owner's own hands-on runs find what no agent knew to look for. What
escaped was a fix that changed a value and missed one of its readers. What cost effort and
found nothing was bookkeeping: filing and closing findings that had no failing case. What
simplified the most, in the owner's report of one session (2026-10-27), was a constraint trace
with counts taken first: each rule ended removed or with one owner, measured, not asserted.
The phases below spend effort accordingly.

**Sequence.** §2 applies throughout. The phases run in order, each the precondition of the
next: map and necessity (§3) → baseline (§4) → **constraint trace (§5), the primary phase** →
tests (§6) → close out (§7) → release notes (§8). Nothing waits on the owner. Decisions go in
the final report; the owner's hands-on run is handed over early and folded in if it arrives
before the end; anything still open at the end is listed in the report.

Canon: `../principles/SKILL.md` (proven / traced / suspected, fixing the class, test value,
what "verified" means). Leans on `../second-look/SKILL.md` for second looks,
`references/lean.md` for the smallest-change ladder and the bloat and test shapes, and
`references/bug-shapes.md` for bug hypotheses.

## 0. Inputs

State each in one line: given by the user, settled by project instructions, or defaulted.

| Input | Default |
|---|---|
| **Target** | a PR number; else a commit range or branch; else a path, or `.` for the whole codebase. With none given, the current branch's PR (`gh pr view`); with no PR, the current branch's commits against its base; on the base branch with nothing else named, stop and ask what to review |
| **Constraints** | the design doc that owns the target's subject, if it lists them; otherwise found in §5a |
| **Stage** | from project instructions; if silent, infer it (a production deploy, real users' data, a released version) and state the evidence; if nothing settles it, take **alpha** and list it under Needs your decision |
| **Subagents** | at most 3 at once (second-look lanes are outside processes and do not count) |
| **New tests** | none net-new unless the target adds a net-new component; a fix's regression test extends the unit's existing tests (§2b) |

| Stage | Rebuild budget |
|---|---|
| **Pre-release** (only test data) | Rebuild, rename, reshape freely. The cheapest refactor window the project will have; spend it. |
| **Alpha** | Reshape freely, but testers' data is real: a shape change carries their rows forward. |
| **GA** | A rebuild needs a migration and a compatibility story; file a large one as an issue instead. |

## 1. Hard rules

- **Never mark the PR ready.** Not by `gh pr ready`, not by the API, not "since everything passed".
- **One review branch.** For a PR, its head branch; for a branch target, that branch; for a
  path or the whole codebase, a new `review/<slug>` branch cut from the base. Never the base
  branch itself. Check it out in the main checkout, or, if that has uncommitted work, in a
  worktree of its own set up as the project's docs say (untracked env files copied over
  unread). Confirm the branch before the first edit. No other pushed branch, no new PR; a
  scratch worktree for an experiment is never pushed. If a push is refused (no rights, a fork),
  keep committing locally and say so in the report.
- **Find and fix.** Proven or traced → fixed, and pushed as you go, so a run that dies leaves
  its work. Suspected → one ledger line, promoted by a repro or dropped. **No concrete failing
  case, no finding**: a finding names the input or situation and the wrong result it produces.
- **No refactor before the baseline exists, and none lands without replaying its matrix rows.**
- **Atomic commits** pushed to the review branch: one concern each, a message saying what the user
  now sees, staged by explicit path, project conventions obeyed, never `--no-verify`.
- **Review bookkeeping is never committed** — no ledger, no finding lists, no "close N
  findings" commits. A living doc's decision record (§7) is not bookkeeping.
- **What cannot run is recorded, never waited on.** A matrix row that needs a browser, a sign-in
  or a service you cannot get (no browser, no test account in the project's seeds or
  fixtures) is checked through code where it can be, and is otherwise marked *not run* with the
  reason. It never counts as green and never blocks; the report lists it. A red check that
  three attempts cannot fix is recorded with what was ruled out (principles §3), and the
  review goes on.
- **Ambiguous fix → the simplest, recorded** in the commit message. Escalate only the owner's
  decisions (§2d), in the final report, and never stop for one.

## 2. Throughout the review

### 2a. The ledger

A long review is summarised mid-way, and what it had not covered is forgotten silently. Keep
state in `pr-review-<slug>.md` in the scratchpad (or another untracked place): the map, the
matrix and its latest results, the baseline checks and numbers (§4), the constraint table with
its search commands and counts (§5), every second-look finding and its outcome, and a disposition per file
per phase (*done*, *unaffected because …*, *skipped because …*; a blank is a miss). Update it as
items close. On resuming, read it first and continue from its first open cell.

### 2b. Every fix — every reader, every sibling

The escape class: a fix that changes how a value is produced, while another reader of that
value — a preview, a fallback, a cache, an export, a second renderer, rows saved before the
change — still computes it the old way. So before committing any fix that changes a produced
value:

- **Enumerate every reader and writer** (search, call graph, and rows written before the
  change). Each is updated, or unaffected because …. Put the list in the commit body as a
  `Readers:` line.
- **Search for the shape** of the defect, and fix its siblings in the same commit.
- **A regression test fails on the unfixed code**: run it there once, and say so in the body.
  It extends the unit's existing tests; a new test file only where the unit has none. Where
  readers can disagree, the test compares them (one input, every path, the same answer). The
  test is what promotes a traced defect to proven; where no test can reproduce it, say why.
- **If it resolves an open issue**, `Closes #n` in the body.

A finding the matrix missed is a missing row: add it.

### 2c. Second looks

Run, briefed and proven as `../second-look/SKILL.md` says; that skill owns the
brief, the lanes runner, file safety and the proving rule. Here only when, and what is reported.

**When:** every §5 change, and the final diff once the last code change is in (§7). A §5
look runs in the background while the review continues and is folded in when it lands (a lane
can take 15–20 minutes). Two looks are waited for, up to the lane's timeout: a §5 change
touching auth, keys, access, money or stored data, before the next change builds on it, and
the final look. A finding whose falsifier cannot be run is one ledger line, not acted on; each
lane's real-to-raised ratio goes in the ledger and the report. A skipped lane never blocks.

### 2d. Escalation

Only the owner's decisions: what the product does, what the user is told, whether a cost is
worth paying. Code shape is yours. Each escalation, in order: the decision in one plain
sentence; what each option means for the person using the product; your recommendation and
the tradeoff. Technical detail below, marked optional. Batch them into the final report, and
meanwhile keep the behaviour as it is (an intent of unclear value stays, an unclear fix takes the simplest
option). Ask the smallest number of genuine forks, the one that dissolves others first.

## 3. Map

Load, for a PR: `gh pr view <n> --json title,body,isDraft,baseRefName,headRefName,closingIssuesReferences,files`
(record `isDraft`); for any change: `git diff <base>...HEAD` and
`git log --reverse --format='%h %s%n%b' <base>..HEAD`; for a path or codebase: its tree, entry
points and the design docs that own its subjects. Then every issue it claims to close, its
premise **quoted**; **every** open issue (`gh issue list --state open --limit 1000 ...` — the
default 30 truncates silently); the project's docs index.

Build **intent → commits → files → units** (a unit is the smallest piece with a stated
interface). For a path or codebase, an intent is a feature a user can reach, and its commits
are the history of its files. A commit message is a claim: read each diff and flag any that does more, less or
other than it says. Flag **fix-on-fix chains** (a later commit patching an earlier one): the
strongest early sign the structure is wrong.

**Necessity, before anything is swept or fixed.** For each intent: revert it in your head (or
in a scratch worktree), name what the user would see differently, and trace a real input that
reaches it from an entry point a user touches. No visible difference, or no reachable input →
revert it, one commit, so no later phase spends effort on it. Reachable but of unclear value,
or explicitly asked for by the target or its issue yet unreachable → keep it, and escalate (§2d).

**Exit:** every commit has an intent, every file a unit, every mismatch and chain is flagged,
every intent is necessary (with the behaviour it protects), reverted, or escalated.

## 4. Baseline — see it work, and save what you saw

### 4a. The matrix

First record, on the base branch, every check the end must hold, so a red later can be told
apart from one that was already there: the project's full gate (its result, and the pass count
of each suite), and the median of several runs for any timing the project tracks or any hot
path the target touches. Label each number observed, with the command that produced it. §7
re-runs every one.

For each intent, name the surfaces it meets (features, types, modes, settings, data states)
and enumerate every combination a user can reach. A new plot type is swept against every other
plot type and every statistic on it; a fix against every surface where the fixed behaviour
appears. When the product is too large: every pair across all axes, and the full product on
the risky axes (changed by the target, touched by a chain, named by an open issue). Write down what
was cut. Each row: the combination, exact replay steps, the expected result in user terms, the
observed result.

Every open issue that names a surface the target touches is a row: what the issue says the user
sees.

Run it **in the running app** as a user would (if you cannot drive a browser, a subagent with
a shell does; sign in with the project's test accounts), and **in code** through the same entry points
(save, reload, migrate; every writer and reader agrees). Verify every pass adversarially,
whoever ran it: what would this look like if it were broken, and did it not look like that? An
empty state proves the surface, not the content.

### 4b. The owner's run

Hand the owner a task list of about 15 minutes: the rows where a person beats the agent (does
it look right, feel right, is the flow obvious without instructions, what happens on a slip).
Each task: one line of steps and the expected result, numbered so a recording can name it.
Give the owner the command to start the recorder, with the real path and URL filled in:
`cd <project> && node <plugin>/scripts/record-session.mjs <app url>` (any folder with Playwright
installed). Read what comes back: `summary.md` first, screenshots only at flagged or failing
moments. Every flag becomes a matrix row, then is fixed or answered. Hand it over as soon as
the matrix exists, so the run can land while the review continues; do not wait on it. If it has
not arrived by the end, the report carries the task list and the command; a recording that
arrives later is reviewed as a new run of this skill.

### 4c. Triage

Tier every failure. **Local cause** (one wrong value, structure sound) → fix now at the
producer, with its readers and siblings (§2b). An open issue's row that fails is fixed the
same way, with `Closes #n`. **Structural cause** (two owners of a value, a state the
design should not allow, a path that should not exist) → mark the row
**known-failure: structural** for §5; a patch now is work §5 throws away.

**Exit:** every reachable row green, known-failure: structural, or not run with its reason;
the gate green or its reds shown to pre-date the target; the matrix and the baseline numbers
saved and replayable.

## 5. Constraint trace — fewer ways to go wrong, measured, not asserted

The primary phase. **Outcome:** for every constraint, either (a) it is no longer needed,
because the shape makes its failure impossible, or (b) exactly one owner holds it, proven by a
code search. **A constraint enforced by a rule people must remember counts as not met.**

### 5a. Name the constraints, and trace past the diff

A constraint is a rule that must always hold for the product to be right: *every read of
stored data goes through one decoder*, *access needs a key*, *only the keyring calls the
crypto primitives*, *a total is computed in one place*. Collect them from the design doc that
owns the subject, from every guard, special case, ordering rule, retry, clamp, fallback, sync
step and flag in the target, from each fix-on-fix chain and structural known-failure (§4c), and
from the invariants of every value the target produces or changes.

Then trace each one outward, as §2b does for a fix: every writer and reader of the values it
governs, across the **whole repository and every stored row** — rows written before the current shape, caches,
exports, second renderers, other services. The trace ends where the values end, never where
the diff ends; a reader found three modules away is in scope. For a whole codebase, start from
the design docs and the values with the most writers, and let the ledger carry the trace
across sessions.

### 5b. Count before changing anything

Record in the ledger, before the first change, for each constraint:

| Column | What it holds |
|---|---|
| Owner(s) | every place that enforces it; more than one is a finding |
| Consumers | every place that relies on it, on every path |
| Legacy paths | readers of data stored in an older shape (markers like `TODO(...)`, version branches, fallbacks) |
| Bad states | states that can exist where the rule is broken (a nullable column, an optional field, a status no row should have) |
| Enforced by | shape (cannot be violated), one owner, or convention |
| Search | the exact command that produced each count, so it re-runs unchanged |

Every count is labelled observed. Classify each constraint: **essential** if it would exist in
the simplest design delivering the same end behaviour, otherwise **accidental** (the producer
is usually still wrong).

### 5c. Shape first, owner second

For each constraint, ask first: *what shape makes this constraint unnecessary?* Only then ask
who should own it. A candidate is kept only if it removes a state or a path — fewer states,
fewer owners of one value, fewer paths to one behaviour, at the same behaviour or better. The
shapes that most often do:

- **Old-data paths:** move every old row forward once (a migration the stage allows), then
  delete every legacy reader. The proof is that no old-shape row can exist.
- **One gateway per primitive:** callers ask for the effect ("save this item", "read this
  item"); one module turns that into the primitive calls. No caller holds the primitive or
  builds its inputs.
- **Resolved values in, never rebuilt:** consumers receive the decided value (a role, a
  locale, a price) from its owner and never recompute it.
- **Make the bad state unrepresentable:** give an in-between state its own shape (a pending
  table, a variant type), so the invalid row or object cannot be written. The proof is a
  database or type constraint, plus a test that fails when the old shape is written.
- **Fold the special case into the general one:** a second path for one kind of thing becomes
  an ordinary instance, if that removes the path without weakening what it protects.

Delete the old path in the same change, fallback included (principles §5). Performance fixes fold in here: a slow path is usually a shape problem. Fix constraints beyond
the target where the trace leads, as long as the stage allows the rebuild (§0); at GA a rebuild
that needs a data migration is filed instead, with its counts.

### 5d. Check first, one commit each

Before each change, write its acceptance check and **see it fail on today's code**: the
search from 5b with the count it must reach (zero, or one owner), plus a test that fails if
the removed state or path returns. Then make the change, see the check pass, and commit it on
its own with the before and after counts in the body. Every change gets a second look (§2c) on
one question: *which of these constraints exist only because of the structure, and what
structure needs none of them?* Replay the touched matrix rows after each change; green → red
is a regression in the change, never in the row.

### 5e. Re-count, then the small rungs

Re-run every 5b search and record the after counts beside the before. Only then climb rungs
2–6 of the ladder in `references/lean.md` unit by unit and run its shapes over each unit,
within its **Never cut** list.

**Exit:** every constraint removed, or held by one owner with the search to prove it, or filed
with its counts and the reason it cannot be done here (the stage forbids the rebuild); no
constraint enforced by convention alone; every structural known-failure fixed or filed the
same way; the matrix green.

## 6. Tests — load-bearing or gone

For every test the target adds or touches (for a whole codebase: the tests of every unit §5
changed): **can it fail for a reason a user would care about, and can a correct refactor leave
it green?** A test that broke under a behaviour-preserving
rebuild was pinned to structure. Remove spurious tests (mocks its own subject, asserts what it
set, guards a regression whose cause was never known, pins an undecided design or source text,
or guards a failure the root fix made unreachable); for each deletion write the one sentence
naming the defect it could not have caught, and keep it if you cannot. Never delete across a
layer whose floor `references/lean.md` says not to cross. Strengthen what survives: a property
over many examples, an invariant across every writer, a real boundary over a mock.

## 7. Close out

In this order, because each step can change code the next one checks.

1. **Remove** narration comments, dead and commented-out code, stale TODOs, generated
   artifacts, and scratch or planning docs. First fold anything that should persist (a
   constraint, a non-obvious reason, a trap) into the living doc that owns its subject; never a
   parallel doc. Record each design decision the review settles: what, why, the date, and what
   would reopen it.
2. **Bring the branch up to date** with its base: merge the base in and resolve conflicts so
   both sides' behaviour survives; where they want different product behaviour, keep the
   base's and escalate. The final checks then run on what will merge.
3. **The final second look** (§2c) on the whole diff against the base.
4. **Final sweep:** after the last commit, re-run every check §4 recorded: replay the whole
   matrix in the running app, the full gate with each suite's pass count, and every timing,
   which must be no slower than its baseline median. If any legacy path survived §5, rehearse
   its data move on a copy of real or staging data where one can be had; otherwise record it
   as not run. A lane that refused is not a pass. Send any red back to the phase that owns it,
   then push.

Any code change after step 4 (a late second-look finding, the owner's recording) reruns steps
2–4 on what it touched, at most twice; what is still open after that goes in the report.

**Exit:** every row green or not run with its reason, full gate green or its reds shown to
pre-date the target, every timing held, every second-look finding fixed or refuted,
everything pushed.

## 8. Release notes — the final step

For a target that is not a PR, the notes below go in the report instead of a PR body, and the
draft-state check is skipped; no PR is opened.

After the last push, **regenerate** the PR title and body from `git log <base>..HEAD` and the
final diff; never append, never narrate the review. Use the project's format if it has one;
otherwise:

```
## New features
## Fixes
## Improvements
## Behind the scenes
## Needs your attention   ← migrations, deploy effects, anything irreversible, open escalations
```

Omit empty sections. **One change per line, in user terms** ("Plots keep their colours after
reload"), `(Closes #n)` on the line that closes it, no filler adjectives, no hedging. **The
body fits on one screen.** Verification goes in a PR comment instead (what ran, the matrix size,
rows in the app, what was cut or skipped, each lane's findings), regenerated each review, not
appended.

**Open issues**, settled against the final branch (their bugs were matrix rows in §4): each
`Closes #n` confirmed in the code and the matrix; an issue in tension with a decision here →
reconcile its text or escalate; a feature whose premise changed → update its text; otherwise
leave it, no comment.

Apply with `gh pr edit`, re-read with `gh pr view`, and confirm the draft state is what §3
recorded.

## 9. Report

```
Target:      #n — title · draft: yes | commit range | path · stage · branch
Premise:     <quoted> → held | partly | did not hold: why
Map:         n intents · n commits · n units · n mismatches · n fix-on-fix chains
Baseline:    n rows (n in the app · n via code · n not run: why · n cut: why) · owner's run: n tasks, n flags → n fixed
             gate, suite counts and timing medians held at the end: yes | which not
Necessity:   n necessary · n reverted · n escalated
Constraints: one row each — constraint · owners before→after · consumers before→after ·
             legacy paths before→after · removed outright | one owner | filed: why ·
             proven by (search, database/type constraint, test) · not checked
             lines -n / +n · per rebuilt unit: old shape → new shape
Fixes:       n proven · n traced · n suspected dropped · each with its Readers: line
Second look: per lane: n raised, n real, n refuted | skipped: why
Tests:       n removed (each with the defect it could not catch) · n strengthened · n new
Issues:      closes #… · fixed #… · reconciled #… · escalated #…
Final:       n/n rows green · gate <command, result, what did not run> · n commits pushed
Needs your decision: <escalations, §2d format, including an inferred stage>
Still open:  <the owner's run if it has not arrived: the task list and the start command>
```
