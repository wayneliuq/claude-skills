---
name: pr-review
description: "Adversarially review a pull request and fix what the review finds, in that PR's branch. Use for \"review this PR\", \"review PR #n\", or \"adversarially review\" a PR. Not a findings list: every proven defect is fixed and pushed as an atomic commit. Runs in order: map the PR's intents; sweep every user-reachable combination in the running app and save it as a replayable matrix; hand the owner a short hands-on test run, recorded automatically; shrink each feature to the fewest states, owners and lines that deliver it (the smallest-change ladder); check every reader of every value a fix changes; put each consequential change to second-look models from another lineage, configured as swappable lanes; replay the matrix after every change. Cross-checks every open issue and rewrites the PR as one-screen release notes. Never marks a draft PR ready. The release stage (pre-release / alpha / GA) decides how much rebuild is allowed."
---

# pr-review

A PR is a claim: *this problem exists, this change fixes it, and this is the right shape for
the fix.* The review attacks all three and repairs what it breaks, in the PR branch, so the PR
that comes out is one the reviewer would have written: correct, safe, smaller, and still a
pleasure to use.

Order of importance, as in every judgement below: **correct, safe, holds under real use,
tested, fast, lean.** Lean still matters: every extra line is read, tested and fixed later.

What finds bugs, measured on past reviews (axiph #825–#1040): the in-app combination sweep
found the most, second looks from another model the next most, outside oracles (R) backed the
numeric fixes, and the owner's own hands-on runs find what no agent knew to look for. What
escaped was a fix that changed a value and missed one of its readers. What cost effort and
found nothing was bookkeeping: filing and closing findings that had no failing case. The phases
below spend effort accordingly.

**Sequence.** §2 applies throughout. The phases run in order, each the precondition of the
next: map and necessity (§3) → baseline (§4) → shrink (§5) → tests (§6) → close out (§7) →
release notes (§8). Nothing waits on the owner. Decisions go in the final report; the owner's
hands-on run is handed over early and folded in if it arrives before the end; anything still
open at the end is listed in the report.

Canon: `../principles/SKILL.md` (proven / traced / suspected, fixing the class, test value,
what "verified" means). Leans on `../adversarial-delegation/SKILL.md` for every subagent and
browser worker, `references/lean.md` for the smallest-change ladder and the bloat and test
shapes, and `references/bug-shapes.md` for bug hypotheses.

## 0. Inputs

State each in one line: given by the user, settled by project instructions, or defaulted.

| Input | Default |
|---|---|
| **PR** | the current branch's PR (`gh pr view`); if there is none, stop and say so |
| **Stage** | from project instructions; if silent, infer it (a production deploy, real users' data, a released version) and state the evidence; if nothing settles it, take **alpha** and list it under Needs your decision |
| **Subagents** | at most 3 at once, through adversarial-delegation (second-look lanes are outside processes and do not count) |
| **New tests** | none net-new unless the PR adds a net-new component; a fix's regression test extends the unit's existing tests (§2b) |

| Stage | Rebuild budget |
|---|---|
| **Pre-release** (only test data) | Rebuild, rename, reshape freely. The cheapest refactor window the project will have; spend it. |
| **Alpha** | Reshape freely, but testers' data is real: a shape change carries their rows forward. |
| **GA** | A rebuild needs a migration and a compatibility story; file a large one as an issue instead. |

## 1. Hard rules

- **Never mark the PR ready.** Not by `gh pr ready`, not by the API, not "since everything passed".
- **This PR's branch only.** Check out the PR head in the main checkout, or, if that has
  uncommitted work, in a worktree of its own set up as the project's docs say (untracked env
  files copied over unread). Confirm the branch before the first edit. No other pushed
  branch, no new PR; a scratch worktree for an experiment is never pushed. If a push is refused
  (no rights, a fork), keep committing locally and say so in the report.
- **Find and fix.** Proven or traced → fixed, and pushed as you go, so a run that dies leaves
  its work. Suspected → one ledger line, promoted by a repro or dropped. **No concrete failing
  case, no finding**: a finding names the input or situation and the wrong result it produces.
- **No refactor before the baseline exists, and none lands without replaying its matrix rows.**
- **Atomic commits** pushed to the PR branch: one concern each, a message saying what the user
  now sees, staged by explicit path, project conventions obeyed, never `--no-verify`.
- **Review bookkeeping is never committed** — no ledger, no finding lists, no "close N
  findings" commits. A living doc's decision record (§7) is not bookkeeping.
- **What cannot run is recorded, never waited on.** A matrix row that needs a browser, a sign-in
  or a service you cannot get (no browser worker, no test account in the project's seeds or
  fixtures) is checked through code where it can be, and is otherwise marked *not run* with the
  reason. It never counts as green and never blocks; the report lists it. A red check that
  three attempts cannot fix is recorded with what was ruled out (principles §3), and the
  review goes on.
- **Ambiguous fix → the simplest, recorded** in the commit message. Escalate only the owner's
  decisions (§2d), in the final report, and never stop for one.

## 2. Throughout the review

### 2a. The ledger

A long review is summarised mid-way, and what it had not covered is forgotten silently. Keep
state in `pr-review-<n>.md` in the scratchpad (or another untracked place): the map, the matrix and its latest results, the
constraints per feature, every second-look finding and its outcome, and a disposition per file
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

Models from another lineage catch what a Claude reviewer shares assumptions with. Run them
through the lanes runner, which reads `../../second-looks.json` (the owner overrides it at
`~/.claude/first-principles/second-looks.json`) and runs every enabled lane in parallel:

```bash
python3 ../../scripts/second-look.py <brief-file> <repo-dir> <out-dir>
```

**When:** every rebuild (§5), and the final diff once the last code change is in (§7). A
rebuild's look runs in the background while the review continues; its findings are folded in
when it lands (a lane can take 15–20 minutes). The final look is waited for, up to the lane's
timeout.

**The brief:** the diff and the one claim to attack, nothing of your preferred answer;
read-only; report everything, each with a confidence; each finding names the test or command
that fails if it is real.

Each lane's report is at the end of its output file. **Then each finding is proven or refuted**
by running its falsifier. Only a failing falsifier is acted on; a finding whose falsifier cannot be run is
suspected, one ledger line, not acted on. Track each lane's real-to-raised ratio in the ledger, and report it; a lane whose
findings mostly refute across a review is costing time — say so, and the owner can switch it
off. A missing, out-of-quota or silent lane is skipped and reported, never retried, never
blocking, never replaced by a Claude reviewer. Agreement between models is not evidence.

### 2d. Escalation

Only the owner's decisions: what the product does, what the user is told, whether a cost is
worth paying. Code shape is yours. Each escalation, in order: the decision in one plain
sentence; what each option means for the person using the product; your recommendation and
the tradeoff. Technical detail below, marked optional. Batch them into the final report, and
meanwhile keep the behaviour as it is (an intent of unclear value stays, an unclear fix takes the simplest
option). Ask the smallest number of genuine forks, the one that dissolves others first.

## 3. Map

Load: `gh pr view <n> --json title,body,isDraft,baseRefName,headRefName,closingIssuesReferences,files`
(record `isDraft`); `git diff <base>...HEAD`; `git log --reverse --format='%h %s%n%b' <base>..HEAD`;
every issue it claims to close, its premise **quoted**; **every** open issue
(`gh issue list --state open --limit 1000 ...` — the default 30 truncates silently); the
project's docs index.

Build **intent → commits → files → units** (a unit is the smallest piece with a stated
interface). A commit message is a claim: read each diff and flag any that does more, less or
other than it says. Flag **fix-on-fix chains** (a later commit patching an earlier one): the
strongest early sign the structure is wrong.

**Necessity, before anything is swept or fixed.** For each intent: revert it in your head (or
in a scratch worktree), name what the user would see differently, and trace a real input that
reaches it from an entry point a user touches. No visible difference, or no reachable input →
revert it, one commit, so no later phase spends effort on it. Reachable but of unclear value,
or explicitly asked for by the PR or its issue yet unreachable → keep it, and escalate (§2d).

**Exit:** every commit has an intent, every file a unit, every mismatch and chain is flagged,
every intent is necessary (with the behaviour it protects), reverted, or escalated.

## 4. Baseline — see it work, and save what you saw

### 4a. The matrix

First run the project's quick gate (typecheck, lint, the changed packages' tests) on the base
branch once, so a red later can be told apart from one that was already there.

For each intent, name the surfaces it meets (features, types, modes, settings, data states)
and enumerate every combination a user can reach. A new plot type is swept against every other
plot type and every statistic on it; a fix against every surface where the fixed behaviour
appears. When the product is too large: every pair across all axes, and the full product on
the risky axes (changed by the PR, touched by a chain, named by an open issue). Write down what
was cut. Each row: the combination, exact replay steps, the expected result in user terms, the
observed result.

Every open issue that names a surface this PR touches is a row: what the issue says the user
sees.

Run it **in the running app** as a user would (if you cannot drive a browser, a browser worker
does, through adversarial-delegation; sign in with the project's test accounts), and **in code** through the same entry points
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
the quick gate green or its reds shown to pre-date the PR; the matrix saved and replayable.

## 5. Shrink — the fewest states, owners and lines that deliver each feature

For each necessary intent (§3), climb the rest of the ladder in `references/lean.md`, and stop
at the first rung that fully works:

1. **Which constraints are essential?** List every guard, special case, ordering rule, retry,
   clamp, fallback, sync step and flag, plus each chain and structural known-failure. A
   constraint is **essential** if it would exist in the simplest design delivering the same end
   behaviour; otherwise it is **accidental**, and the producer is usually still wrong.
2. **Rebuild to the shape that needs fewer of them.** Design the unit's states, value owners
   and flows abstractly, then compare. The rebuild wins only with fewer states, fewer owners of
   one value, fewer paths to one behaviour, or fewer constraints, at the same behaviour or
   better. Delete the old path in the same change; two live paths is never acceptable,
   fallback included. Reach beyond the PR only where an accidental constraint's cause lives.
   Performance fixes fold in here: a slow path is usually a shape problem.
3. **Then the small rungs**, unit by unit: reuse what the codebase has, then the platform or an
   installed dependency, then one readable line, then the least code. Run the lean shapes over
   each unit.

**Never cut:** validation at trust boundaries, error handling that prevents data loss,
security, accessibility, anything the user sees or asked for, and a test with an external
oracle. A shortcut with a known limit stays when it says so in a `shortcut: <limit>, <when to
upgrade>` comment.

Every rebuild gets a second look (§2c) on one question: *which of these constraints exist only
because of the structure, and what structure needs none of them?* Replay the touched matrix
rows after each change; green → red is a regression in the change, never in the row.

**Exit:** every accidental
constraint is removed, or filed with the reason it cannot be in this PR (the stage forbids
the rebuild, or its cause lies outside); every structural known-failure is fixed or filed the
same way; the matrix is green.

## 6. Tests — load-bearing or gone

For every test the PR adds or touches: **can it fail for a reason a user would care about,
and can a correct refactor leave it green?** A test that broke under a behaviour-preserving
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
   parallel doc. Record each design decision the PR settles: what, why, the date, and what
   would reopen it.
2. **Bring the branch up to date** with its base: merge the base in and resolve conflicts so
   both sides' behaviour survives; where they want different product behaviour, keep the
   base's and escalate. The final checks then run on what will merge.
3. **The final second look** (§2c) on the whole diff against the base.
4. **Final sweep:** replay the whole matrix in the running app, run the project's full gate
   after the last commit (a lane that refused is not a pass), send any red back to the phase
   that owns it, then push.

Any code change after step 4 (a late second-look finding, the owner's recording) reruns steps
2–4 on what it touched, at most twice; what is still open after that goes in the report.

**Exit:** every row green or not run with its reason, full gate green or its reds shown to pre-date the
PR, every second-look finding fixed or refuted, everything pushed.

## 8. Release notes — the final step

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
PR:          #n — title · draft: yes · stage · branch
Premise:     <quoted> → held | partly | did not hold: why
Map:         n intents · n commits · n units · n mismatches · n fix-on-fix chains
Baseline:    n rows (n in the app · n via code · n not run: why · n cut: why) · owner's run: n tasks, n flags → n fixed
Necessity:   n necessary · n reverted · n escalated
Shrink:      constraints n essential / n accidental → n removed · lines -n / +n
             per rebuilt unit: old shape → new shape
Fixes:       n proven · n traced · n suspected dropped · each with its Readers: line
Second look: per lane: n raised, n real, n refuted | skipped: why
Tests:       n removed (each with the defect it could not catch) · n strengthened · n new
Issues:      closes #… · fixed #… · reconciled #… · escalated #…
Final:       n/n rows green · gate <command, result, what did not run> · n commits pushed
Needs your decision: <escalations, §2d format, including an inferred stage>
Still open:  <the owner's run if it has not arrived: the task list and the start command>
```
