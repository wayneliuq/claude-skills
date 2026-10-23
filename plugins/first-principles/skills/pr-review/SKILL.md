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

Canon: `../principles/SKILL.md` (proven / traced / suspected, fixing the class, test value,
what "verified" means). Leans on `../adversarial-delegation/SKILL.md` for every subagent and
browser worker, `references/lean.md` for the smallest-change ladder and the bloat and test
shapes, and `references/bug-shapes.md` for bug hypotheses.

## 0. Inputs

State each in one line: given by the user, settled by project instructions, or defaulted.

| Input | Default |
|---|---|
| **PR** | the current branch's PR (`gh pr view`); ask only if there is none |
| **Stage** | from project instructions; if silent, **ask**, since it sets the rebuild budget |
| **Subagents** | at most 3 at once, through adversarial-delegation |
| **New tests** | none net-new unless the PR adds a net-new component |

| Stage | Rebuild budget |
|---|---|
| **Pre-release** (only test data) | Rebuild, rename, reshape freely. The cheapest refactor window the project will have; spend it. |
| **Alpha** | Reshape freely, but testers' data is real: a shape change carries their rows forward. |
| **GA** | A rebuild needs a migration and a compatibility story; file a large one as an issue instead. |

## 1. Hard rules

- **Never mark the PR ready.** Not by `gh pr ready`, not by the API, not "since everything passed".
- **This PR's branch only.** `gh pr checkout <n>`, confirm `git branch --show-current` before
  the first edit. No other branch, no new PR.
- **Find and fix.** Proven or traced → fixed and pushed. Suspected → one ledger line, promoted
  by a repro or dropped. **No concrete failing case, no finding**: a finding names the input or
  situation and the wrong result it produces.
- **No refactor before the baseline exists, and none lands without replaying its matrix rows.**
- **Atomic commits** pushed to the PR branch: one concern each, a message saying what the user
  now sees, staged by explicit path, project conventions obeyed, never `--no-verify`.
- **Review bookkeeping is never committed** — no ledger files, no "close N findings" commits.
- **Ambiguous fix → the simplest, recorded** in the commit message. Escalate only the owner's
  decisions (§10).

## 2. The ledger

A long review is summarised mid-way, and what it had not covered is forgotten silently. Keep
state in `pr-review-<n>.md` in the scratchpad: the map, the matrix and its latest results, the
constraints per feature, every second-look finding and its outcome, and a disposition per file
per phase (*done*, *unaffected because …*, *skipped because …*; a blank is a miss). Update it as
items close. On resuming, read it first and continue from its first open cell.

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

**Exit:** every commit has an intent, every file a unit, every mismatch and chain is flagged.

## 4. Baseline — see it work, and save what you saw

### 4a. The matrix

For each intent, name the surfaces it meets (features, types, modes, settings, data states)
and enumerate every combination a user can reach. A new plot type is swept against every other
plot type and every statistic on it; a fix against every surface where the fixed behaviour
appears. When the product is too large: every pair across all axes, and the full product on
the risky axes (changed by the PR, touched by a chain, named by an open issue). Write down what
was cut. Each row: the combination, exact replay steps, the expected result in user terms, the
observed result.

Run it **in the running app** as a user would, and **in code** through the same entry points
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
moments. Every
flag becomes a matrix row, then is fixed or answered. Do not wait on the run: keep working, and
fold it in when it arrives.

### 4c. Triage

Tier every failure. **Local cause** (one wrong value, structure sound) → fix now at the
producer, with its siblings (§6). **Structural cause** (two owners of a value, a state the
design should not allow, a path that should not exist) → mark the row
**known-failure: structural** for §5; a patch now is work §5 throws away.

**Exit:** every reachable row green or known-failure: structural; the fast gate green; the
matrix saved and replayable.

## 5. Shrink — the fewest states, owners and lines that deliver each feature

For each intent, climb the ladder in `references/lean.md` from the top, and stop at the first
rung that fully works:

1. **Does it need to exist?** Revert it in your head (or on a scratch branch). Name what the
   user would see differently, and trace a real input that reaches it. No visible difference,
   or no reachable input → revert it, one commit. Reachable but of unclear value → §10.
2. **Which constraints are essential?** List every guard, special case, ordering rule, retry,
   clamp, fallback, sync step and flag, plus each chain and structural known-failure. A
   constraint is **essential** if it would exist in the simplest design delivering the same end
   behaviour; otherwise it is **accidental**, and the producer is usually still wrong.
3. **Rebuild to the shape that needs fewer of them.** Design the unit's states, value owners
   and flows abstractly, then compare. The rebuild wins only with fewer states, fewer owners of
   one value, fewer paths to one behaviour, or fewer constraints, at the same behaviour or
   better. Delete the old path in the same change; two live paths is never acceptable,
   fallback included. Reach beyond the PR only where an accidental constraint's cause lives.
   Performance fixes fold in here: a slow path is usually a shape problem.
4. **Then the small rungs**, unit by unit: reuse what the codebase has, then the platform or an
   installed dependency, then one readable line, then the least code. Run the lean shapes over
   each unit.

**Never cut:** validation at trust boundaries, error handling that prevents data loss,
security, accessibility, anything the user sees or asked for, and a test with an external
oracle. A shortcut with a known limit stays when it says so in a `shortcut: <limit>, <when to
upgrade>` comment.

Every rebuild gets a second look (§7) on one question: *which of these constraints exist only
because of the structure, and what structure needs none of them?* Replay the touched matrix
rows after each change; green → red is a regression in the change, never in the row.

**Exit:** every intent is necessary-with-behaviour, reverted, or escalated; no accidental
constraint is left without a reason; no structural known-failure remains; the matrix is green.

## 6. Every fix — every reader, every sibling

The escape class: a fix that changes how a value is produced, while another reader of that
value — a preview, a fallback, a cache, an export, a second renderer, rows saved before the
change — still computes it the old way. So before committing any fix that changes a produced
value:

- **Enumerate every reader and writer** (search, call graph, and rows written before the
  change). Each is updated, or unaffected because …. Put the list in the commit body as a
  `Readers:` line.
- **Search for the shape** of the defect, and fix its siblings in the same commit.
- **A regression test fails on the unfixed code**: run it there once, and say so in the body.
  Where readers can disagree, the test compares them (one input, every path, the same answer).

A finding the matrix missed is a missing row: add it.

## 7. Second looks

Models from another lineage catch what a Claude reviewer shares assumptions with. Run them
through the lanes runner, which reads `../../second-looks.json` (the owner overrides it at
`~/.claude/first-principles/second-looks.json`) and runs every enabled lane in parallel:

```bash
python3 ../../scripts/second-look.py <brief-file> <repo-dir> <out-dir>
```

**When:** every rebuild (§5), and the final diff before §9. Off the critical path: start it in
the background, keep reviewing.

**The brief:** the diff and the one claim to attack, nothing of your preferred answer;
read-only; report everything, each with a confidence; each finding names the test or command
that fails if it is real.

Each lane's report is at the end of its output file. **Then each finding is proven or refuted** by running its falsifier. Only a failing falsifier
is acted on. Track each lane's real-to-raised ratio in the ledger, and report it; a lane whose
findings mostly refute across a review is costing time — say so, and the owner can switch it
off. A missing, out-of-quota or silent lane is skipped and reported, never retried, never
blocking, never replaced by a Claude reviewer. Agreement between models is not evidence.

## 8. Tests — load-bearing or gone

For every test the PR adds or touches: **can it fail for a reason a user would care about,
and can a correct refactor leave it green?** A test that broke under a behaviour-preserving
rebuild was pinned to structure. Remove spurious tests (mocks its own subject, asserts what it
set, guards a regression whose cause was never known, pins an undecided design or source text,
or guards a failure the root fix made unreachable); for each deletion write the one sentence
naming the defect it could not have caught, and keep it if you cannot. Never delete across a
layer whose floor `references/lean.md` says not to cross. Strengthen what survives: a property
over many examples, an invariant across every writer, a real boundary over a mock.

## 9. History, docs, final sweep

**Remove** narration comments, dead and commented-out code, stale TODOs, generated artifacts,
and scratch or planning docs. First fold anything that should persist (a constraint, a
non-obvious reason, a trap) into the living doc that owns its subject; never a parallel doc.
Record each design decision the PR settles: what, why, the date, and what would reopen it.

**Open issues**, settled against the branch as it now is: resolved here → confirm in the code
and the matrix, `Closes #n` on its release-notes line; a real bug → reproduce, fix with
`Closes #n`, add its row; in tension with a decision here → reconcile or escalate; a feature
whose premise changed → update its text; otherwise leave it, no comment.

**Final sweep:** replay the whole matrix in the running app, run the project's full gate after
the last commit (a lane that refused is not a pass), send any red back to the phase that owns
it, then push. **Exit:** full matrix green, full gate green, everything pushed.

## 10. Escalation

Only the owner's decisions: what the product does, what the user is told, whether a cost is
worth paying. Code shape is yours. Each escalation, in order: the decision in one plain
sentence; what each option means for the person using the product; your recommendation and
the tradeoff. Technical detail below, marked optional. Batch them, keep working, ask the
smallest number of genuine forks, the one that dissolves others first.

## 11. Release notes — the final step

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
appended. Apply with `gh pr edit`, re-read with `gh pr view`, and confirm it is still a draft.

## 12. Report

```
PR:          #n — title · draft: yes · stage · branch
Premise:     <quoted> → held | partly | did not hold: why
Map:         n intents · n commits · n units · n mismatches · n fix-on-fix chains
Baseline:    n rows (n in the app · n via code · n cut: why) · owner's run: n tasks, n flags → n fixed
Shrink:      n reverted · constraints n essential / n accidental → n removed · lines -n / +n
             per rebuilt unit: old shape → new shape
Fixes:       n proven · n traced · n suspected dropped · each with its Readers: line
Second look: per lane: n raised, n real, n refuted | skipped: why
Tests:       n removed (each with the defect it could not catch) · n strengthened · n new
Issues:      closes #… · fixed #… · reconciled #… · escalated #…
Final:       n/n rows green · gate <command, result, what did not run> · n commits pushed
Needs your decision: <escalations, §10 format>
```
