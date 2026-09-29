---
name: pr-review
description: "Adversarially review a pull request and fix what the review finds, in that PR's branch — activated by \"review this PR\", \"review PR #n\", or \"adversarially review\" a PR. Not a findings list: every proven defect is fixed and pushed as an atomic commit. Distrusts the PR's stated premise (revert the fix in your head — what would a user actually lose, and can the problem even occur?), checks the fix sits at the right layer rather than being a band-aid, rebuilds each touched contract-bounded unit from scratch in thought and implements the simpler shape (with a cross-lineage second look on the rebuild decision), prunes tests that cannot fail for a reason a user would care about, cross-checks every open repo issue against the PR, strips historical bloat, folds surviving knowledge into living docs as revisitable locked-in decisions, and finishes by rewriting the PR title and body as concise, user-facing release notes regenerated from the branch. Never marks a draft PR ready. Takes the release stage (pre-release / alpha / GA) as the input that decides how much rebuild is allowed."
---

# pr-review

A PR is a claim: *this problem exists, this change fixes it, and this is the right shape
for the fix.* The review attacks all three, then repairs what it breaks — in the PR
branch, commit by commit — so the PR that comes out is one the reviewer would have
written.

Canon: `../principles/SKILL.md`. Mechanics this skill leans on rather than restates:

- `../adversarial-delegation/SKILL.md` — every subagent and every grok second look.
- `../bug-gate/SKILL.md` — proven / traced / suspected, and fixing the class.
- `../cut-gate/SKILL.md` — test value, and the bloat catalog.
- `../done-gate/SKILL.md` — what "verified" means before the verdict.

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
  hunch (bug-gate).
- **Atomic commits, pushed to the PR branch.** One concern per commit, a message that says
  what the user now sees, staged by explicit path. Obey the project's commit conventions
  (trailers, hooks); never `--no-verify`.
- **Ambiguous fix → pick the simplest, and record the choice** in the commit message and
  the verdict. Escalate only what is genuinely the owner's decision (§9).
- **No net-new unit tests** unless the PR introduces a net-new component. Otherwise, make
  the existing tests more load-bearing (§6).

## 2. Load the PR

Before judging anything:

1. `gh pr view <n> --json title,body,isDraft,baseRefName,headRefName,closingIssuesReferences,files`
   — and confirm `isDraft`. Record it; §1 depends on it.
2. The full diff against the merge base, not the last commit: `git diff <base>...HEAD`.
3. Every issue the PR claims to close, and the PR's own stated premise, **quoted** — you
   are about to test it, so write down exactly what it says.
4. The project's living docs index and the rules the project holds itself to.

Then name the **contract-bounded units** the diff touches — the smallest pieces with a
stated interface (a module, a service, a component with its props/events, a table with its
readers). Every later pass works per unit.

## 3. Necessity — does this change need to exist?

Run this **first**. Simplifying a change that should not exist is wasted work, and the
answer here can dissolve every later pass.

**Do not trust the premise.** The PR description and the linked issue are the author's
belief, not evidence. For each change in the diff:

1. **Revert it in your head** (or actually, on a scratch branch). What user-facing
   behaviour changes? Name it concretely: what the person would see, click, or be told
   differently.
2. **Would a real user notice?** Picture the actual user of this product doing their
   actual job. If nobody would ever see the difference, the change is ballast.
3. **Can the problem actually occur?** Trace the input that reaches the fixed branch, from
   a real entry point. State the circumstance: which user action, which data, which
   sequence. A problem with no reachable input is theoretical — do not keep a fix for it.
4. **Is the fix at the right layer?** Find where the wrong value is *produced*, not where
   it is *noticed*. A guard at the consumer, a retry, a clamp, a special case for one
   input — these are band-aids when the producer is still wrong. Principle 2: if two places
   decide one value, the fix is removing one of them.

Dispose every change as **necessary** (with the user-visible behaviour it protects),
**unnecessary** (revert it, one commit, and say what was reverted), or **ambiguous** —
reachable but only under conditions you cannot confirm, or visible but of unclear value.
Ambiguous goes to §9. Do not guess on the owner's behalf.

## 4. Fresh-eyes rebuild — would it be simpler from scratch?

For each contract-bounded unit the PR touches, ask: *knowing what we know now, if we built
this unit from nothing, against the same contract, what would it look like?*

- Write the from-scratch shape down in a few lines: its states, its owners, its paths.
- Compare to what exists after the PR. The rebuild wins when it has **fewer states, fewer
  owners of one value, or fewer paths to the same behaviour** — not when it is merely
  different or shorter.
- **Performance fixes fold into this pass.** A slow path is usually a shape problem; fix it
  as part of the rebuild, not as a separate patch on the old shape.

**Get a second look on every rebuild decision** via adversarial-delegation §1b (grok through
`cursor-agent`). Give it one question: *could this unit be built better from the ground up?*
Tell it the stage in plain words — for pre-release: "we are pre-release, with no users and
only test data; this is the best window for any refactor or rebuild; do not weigh refactor
cost, migration cost, or backward compatibility." Hand it the unit's contract and current
code, not your preferred answer. Its findings are hypotheses: only those whose named
falsifier fails, or whose simpler shape you can actually write, are acted on.

**Implement the simpler shape** when it wins, within the stage's budget (§0). Delete the old
path in the same change — two live paths for one behaviour is never acceptable, including
the form where the old path survives behind a fallback.

Use subagents here when a rebuild is large enough to hand off — through adversarial-
delegation's triage, at most three at once, each fenced to disjoint files, each reviewed
rather than believed.

## 5. Correctness — what is actually wrong

Run bug-gate over the diff and its reachable neighbours: its shape catalog as hypothesis
generator, every finding tiered. Two checks this review always runs, because they are where
PRs most often go wrong:

- **Every writer, every reader.** For each value the PR changes the shape of, enumerate every
  producer and consumer — including rows written before the change, cold reloads, and
  migrations. Each is **updated**, **unaffected because …**, or **skipped because …**.
- **Every sibling.** A defect at one call site has siblings; search for the shape and fix
  them together.

## 6. Tests — load-bearing or gone

Apply cut-gate's two questions to every test the PR adds or touches:

1. Can it fail for a reason a user would care about?
2. Can a correct refactor leave it green?

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

## 7. Open-issue cross-check

Pull **every** open issue: `gh issue list --state open --limit 1000 --json number,title,body,labels`.
The default limit is 30, and a truncated list is a silent miss.

For each issue, one disposition:

| The issue is | Do |
|---|---|
| **resolved by this PR** | confirm it against the code, not the title; add `Closes #n` so it closes atomically when the PR merges — one `Closes` per issue, on the release-notes line of the change that resolves it (§11) |
| **in tension with a decision this PR made** | reconcile it — adjust the code or the issue text — if the right answer is clear; otherwise escalate (§9) |
| **a real bug, unfixed** | reproduce it (bug-gate); proven or traced → fix it in this branch with `Closes #n`; suspected → comment what you tried, leave it open |
| **a net-new feature** | if this PR changed a premise the issue rests on, update the issue text to match; otherwise leave it alone |
| **unrelated** | leave it alone; no comment |

Most issues are unrelated. Report only the non-trivial dispositions.

## 8. Historical bloat and living docs

**Remove from the branch:** comments narrating history ("previously", "was changed to",
"fix for #n"), dead code and unreachable arms, commented-out code, stale TODOs, generated
artifacts, and planning or scratch docs that describe work rather than the system.

**Before deleting anything, extract what should persist** — anything that affects future
development or maintenance: a constraint, a non-obvious reason, a trap someone fell into.
Fold it into the living doc that owns that subject, found through the project's docs index.
Never create a parallel doc where one already owns the topic.

**Update the living docs** the PR's change touches, so they describe the system as it now
is. **Record each design decision the PR settles** as a locked-in decision that can be
revisited: what was decided, the reason, the date, and what evidence would reopen it. A
decision without its reopen condition reads as permanent and stops being questioned.

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

## 10. Verify and push

- Run the project's full gate (done-gate's layer 1) after the last commit, not per commit.
  A lane that refused is not a pass.
- Push to the PR branch.

## 11. Rewrite the PR message as release notes — the final step

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
- **Honest.** `Verification` states what actually ran; a skipped lane is written as skipped.
  Nothing claims more than the commits and the gate show.

**Title:** a plain summary of the user-visible change, matching the project's title
convention if it has one.

Apply with `gh pr edit <n> --title … --body-file …`, then re-read it with `gh pr view <n>`
to confirm what landed.

**Confirm the PR is still a draft** (`gh pr view <n> --json isDraft`). If it somehow is not,
say so first in the report.

## 12. Report

```
PR:          <#n — title> · draft: yes · stage: <stage> · branch: <head>
Premise:     <quoted claim> → <held | partly held | did not hold: why>
Layer:       <fix at the producer | band-aid at <site> → moved to <site>>

Necessity:   <n> necessary · <n> reverted (what the user would have lost: nothing) · <n> escalated
Rebuild:     <per unit: kept | rebuilt to <shape> — states/owners/paths removed>
  Second look: <grok on <question>: N findings, N proven, N refuted | skipped: why>
Correctness: <n> proven fixed · <n> traced fixed · <n> suspected logged
Tests:       <n> removed (each with the defect it could not catch) · <n> refactored · <n> new (new component only)
Issues:      closes <#a, #b> · fixed <#c> · reconciled <#d> · escalated <#e>
Bloat/docs:  <removed> · <folded into <doc>> · <decisions recorded>
Choices:     <ambiguous fixes where the simplest was picked, one line each>
Gate:        <command, result, what did not run>
Commits:     <n pushed, one line each>
PR message:  <rewritten as release notes — title, sections used>

Needs your decision:
  <escalations, §9 format>
```
