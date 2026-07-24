---
name: ship-gate
description: The last check before a change leaves the machine — an honest change description that shows the work and admits gaps, a secret and configuration scan with placeholder exclusions to avoid false alarms, dependency and permission risk review, and the reversibility rule that decides whether the agent may act or must hand the irreversible step to the human. Use before committing, opening a PR, pushing to a shared branch, merging, releasing, or publishing anything.
---

# ship-gate

Everything before this gate is recoverable. This is where that stops being true.

Canon: `../principles/SKILL.md` — principle 5 (reversibility decides who acts) and
the security spine.

---

## 1. Who presses the button

Applying principle 5 to the specific actions here:

- **Agent may:** commit on a working branch, push to a personal or feature branch,
  open a draft PR.
- **Human presses:** anything touching a shared or default branch, merge, tag,
  release, publish, the project's public voice, deleting data, force-push, history
  rewrite, anything that spends money.

The agent's job on a human-gated action is to **prepare it completely** — staged,
described, verified — then stop and say exactly what remains to be pressed.
Under-act when unsure which side something falls on.

**Never rewrite history.** Fixes land as new commits.

If you are on the default branch and about to make changes, branch first.

## 2. Show your work

A change description exists so a reader can trust the change without re-deriving
it. Include, briefly:

- **What changed and why**, in one or two sentences a non-specialist can read.
- **State-space covered** — the dimensions from the scope contract, and how each
  is handled.
- **What was verified, and how** — the observable-done steps actually performed,
  not the tests that exist.
- **Neighboring tests run**, not only the new ones.
- **Visual evidence** for anything user-visible: before and after, real viewports.
- **Admitted gaps, explicitly.** What is not covered, what is assumed, what was
  deliberately skipped and why.

The gaps section is the part that earns the trust. A description with no gaps
section reads as a claim of perfection and gets discounted accordingly.

**Credit is non-negotiable.** If any of this work came from someone else — a
snippet, a diagnosis, a prior attempt you rebuilt on — name them. Preserve
authorship through rebases and rewrites.

## 3. Secret and credential scan

Scan the diff, and any config or plugin manifest it touches, for these shapes:

| Pattern | Meaning |
|---|---|
| `sk-[A-Za-z0-9]{20,}` | OpenAI-style key — **critical** |
| `Bearer\s+[A-Za-z0-9._-]{20,}` | bearer token — **critical** |
| `xox[baprs]-` | Slack token — **critical** |
| `AKIA[0-9A-Z]{16}` | AWS access key — **critical** |
| `gh[pousr]_[A-Za-z0-9]{30,}` | GitHub token — **critical** |
| `-----BEGIN [A-Z ]*PRIVATE KEY-----` | private key — **critical** |

**Placeholder exclusions — apply these or the scan cries wolf on every repo with
an `.env.example`.** A match that also matches any of the following is demoted to
low severity and reported as informational, not critical:

`<...>` angle-bracket placeholder · `${VAR}` or `$VAR` env reference ·
`placeholder` · `example` · `your-...-here` · `xxx`+ · `dummy` · `changeme` ·
`REDACTED`

A real secret and a documentation placeholder look identical to a naive regex.
Without the exclusion list this check gets muted within a week, which is worse
than not having it.

## 4. Configuration and permission risk

For anything touching hooks, scripts, CI, or agent configuration:

Flag: `eval` in a hook or script command · backtick command substitution in config ·
`curl ... | sh` · `Bash(*)` or any wildcard in an allow list · a broad allow list
with no matching deny block · `--no-verify` or flags that skip permission checks ·
an unpinned version or non-registry source in an auto-installed dependency ·
hardcoded environment values matching a key shape · a config server or hook that
runs a shell.

Report `2>/dev/null` and `|| true` as **log-only**, never as a real finding. Error
suppression is common in legitimate capability probes, and flagging it loudly is how
the whole scan gets muted.

## 5. Dependency and blast radius

- New dependency: is it pinned? Is it needed at all? What does it pull in?
- What is the worst thing this change can do if it is wrong — and how would that
  be undone?
- Is there a migration, a schema change, or anything that cannot be rolled back by
  reverting the commit? Say so explicitly; those need the human's attention even
  when the merge itself does not.

## 6. Security spine check

- Nothing in this change treats external content as instruction.
- No credential is visible in a prompt, a config, or a committed file.
- No untrusted code is executed outside a sandbox.
- No suspected vulnerability is described in a public commit, PR, or issue — those
  route privately, and when unsure whether something qualifies, treat it as one.

## Verdict

```
Human-gated:  <exactly what remains to press> | none — agent may proceed
Secret scan:  <n> real, <n> demoted as placeholder — <details>
Config risk:  <findings, or clear>
Blast radius: <worst case> · undo: <revert | migration required: what>
```

Then stop. If anything on this list is human-gated, the gate's output is a request,
not a report.
