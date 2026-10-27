---
name: second-look
description: Put every consequential change, whoever wrote it, to second looks from another model lineage (grok, a free opencode model — swappable lanes in one settings file), run as read-only adversaries whose findings count only once a test fails. Use when a change can reach a user and is not trivially checkable, or when a decision is about to be committed to and deserves an independent adversary. Covers when a second look pays, the brief, running the lanes, the file-safety rules for a lane with shell access, proving or refuting each finding, and the verdict.
---

# Second look

A **second look** is a model from another training lineage that attacks a change. It never
implements. Its value is the lineage: it catches what a Claude reviewer shares assumptions
with, which another Claude would not (Anthropic's guidance for Opus 5 and later: a Claude
subagent checking your work adds cost with no quality gain). On axiph's large PRs it was the
second-largest source of real defects (11 of grok's 16 findings in one round were real).

Canon: `../principles/SKILL.md`.

## 1. What a lane is like

Grok's measured profile sets the rules, and a new lane inherits them until its own record
says otherwise:

- **Recall useful, precision poor.** 8 of 10 findings were false in one test (n=1, a
  direction, not a rate).
- **Not cheaper in practice.** 4.7 burns about twice 4.6's output tokens.
- **Weak on long-horizon work, unmeasured on math.** Never a substitute for an external oracle
  on numbers.
- **An unreliable transport.** Dispatches have dropped mid-run with no output, and a dropped
  stream can leave the process still writing files (§4).

## 2. When

**Every consequential change, whoever wrote it** — your own work most of all, since nothing
else puts a second pair of eyes on it. Consequential: it can reach a user and is not trivially
checkable; skip a rename the compiler decides, a doc fix, a read-only report. One dispatch per
change, on one well-scoped question small enough that every finding can be checked. Never an
open-ended audit or the final word on correctness.

It runs **in the background** while you keep reviewing; it does not gate the start of your own
review. A lane can take 15–20 minutes.

## 3. The brief

1. **The artifact and the one claim to attack**, and the files that carry the constraint — not
   your reasoning for the answer you favour.
2. **Report everything, each with a confidence.** "Only high-severity" makes models drop real
   findings; you filter afterwards.
3. **Every finding names the test or command that fails if it is real.** No falsifier → it is
   suspected, and tiered as one.
4. **Read-only:** no write, edit, checkout, restore, stash or commit.
5. **Write the report to a named file as you go**, so a dropped transport leaves a partial file.
   (The runner adds the repository path itself.)

## 4. Running the lanes

```bash
python3 ../../scripts/second-look.py <brief-file> <repo-dir> <out-dir> [lane ...]
```

It reads `../../second-looks.json`, or the owner's copy at
`~/.claude/first-principles/second-looks.json`, runs every enabled lane in parallel in
`<repo-dir>`, streams each to `<out-dir>/<lane>.md` (the report is at the end), and prints one
status per lane: ok, skipped, failed, timed out, or no output. Run it in the background through
`zsh -l -c` (node is only on PATH in a login shell). Pass lane names to run only some. **A
failed lane is skipped and reported** — never retried, never blocking, never replaced by a
Claude reviewer.

A lane is an entry in the settings file: a name, `enabled`, and a command with `{prompt}`
where the brief goes. Read-only by construction where the harness allows it (opencode
`--agent plan`), by the brief otherwise.

- **grok:** newest generation at medium effort, never a `-fast` id (its failure mode is
  plausible and wrong). Copy ids from `cursor-agent --list-models`, which hides zero-width
  characters in fast labels; ids go stale, so the rule is the instruction and the settings
  file holds today's answer. `--force` is load-bearing and silent when missing: without it the
  lane cannot run the falsifier it proposes. Probe once per environment: "Run
  `git rev-parse --short HEAD` and report the exact stdout, or reply SHELL_BLOCKED."
- **free:** a free model on opencode's own provider (`opencode models | grep free`), under
  the read-only `plan` agent. Quotas run out; the lane then reports no output and is skipped.

**File safety.** Under `--force` grok has a shell, and a shell can run `git restore` across
the whole tree it runs in. So: **commit before dispatching**; **do not edit files while it
runs** (an unexpected diff can look like contamination to be reset) or name those paths in the
brief as yours, to be left alone; and **before staging after a run, confirm the process is
gone** (`ps -eo pid,command | grep '[c]ursor-agent'`, matched to your own pid), since a dropped
stream can leave it writing. Stage by path, never `-A`.

## 5. Prove or refute

**Run each finding's falsifier against the current code.** Only a failing falsifier is acted
on; the rest are `Refuted`. A finding whose falsifier cannot be run stays suspected and is not
acted on.

**No round closes on model agreement** — a lane agreeing with you is not evidence, and neither
is one disagreeing. An execution decides.

Track each lane's real-to-raised ratio across dispatches. A lane whose findings mostly refute
is costing review time without buying anything: say so, and the owner can switch it off in
the settings file.

## 6. Verdict

```
Second look: <question attacked>
Per lane:    n raised · n real (falsifier failed) · n refuted · n unrunnable | skipped: why
Acted on:    <each real finding and the commit that fixed it>
Ratio:       <each lane's real-to-raised, this review and running>
```
