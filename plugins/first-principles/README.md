# first-principles

Four skills, kept small on purpose: capable models need goals and the few processes
they would not run unaided, not checklists.

| Skill | What it is |
|---|---|
| [`principles`](skills/principles/) | Seven goal-oriented principles for building, debugging, fixing and shipping. Loaded into **every session** by a `SessionStart` hook ([`hooks/hooks.json`](hooks/hooks.json)); not model-invoked. |
| [`pr-review`](skills/pr-review/) | Adversarial find-and-fix review of a PR, a change or a whole codebase, on the PR's branch or a review branch: an in-app combination sweep, a short hands-on run for the owner, a constraint trace (every rule ends removed or with one owner, counted before and after, traced past the diff), every reader of every changed value, and second looks from other models. Never marks a draft ready. The bug catalog and the lean reference are in [`references/`](skills/pr-review/references/). |
| [`second-look`](skills/second-look/) | Every consequential change, whoever wrote it, is attacked by a model from another lineage (grok, a free opencode model), read-only, and a finding counts only once its test fails. |
| [`deepen`](skills/deepen/) | Rewrites a plan, prompt or brief into a deeper version, not a bigger one: evidence first, then how each relevant domain's best practitioners would find the solution (never the solution itself), each addition judged by an external oracle. Returned in the input's own form. User-invoked only. |

## Scripts and settings

| File | What it does |
|---|---|
| [`second-looks.json`](second-looks.json) | The second-look lanes (today grok and a free opencode model): harness, model, command, on or off. Copy it to `~/.claude/first-principles/second-looks.json` to change lanes without editing the plugin. |
| [`scripts/second-look.py`](scripts/second-look.py) | Runs every enabled lane on one brief in parallel; a lane that is missing, out of quota or silent is reported as skipped. |
| [`scripts/record-session.mjs`](scripts/record-session.mjs) | Records a hands-on run of a web app: clicks, a screenshot per click, console errors, failed requests, and problems you flag with Ctrl/Cmd+Shift+F, into a folder with a `summary.md` the agent reads first. Password, token and key fields are redacted in the log and blacked out in screenshots. |

## v5.0.0

`pr-review` makes the constraint trace its primary phase, replacing shrink. Every value the
target touches is traced to all its owners and readers across the repo and stored data, never
bounded by the diff; each constraint's owners, consumers, legacy paths and bad states are
counted before any change; each ends removed by a shape that makes its failure impossible, or
held by one owner, proven by a search and a test seen failing first. A rule people must
remember counts as not met. The baseline now records suite counts and timing medians the end
must hold. The target can be a PR, a change, a path or the whole codebase.

The plugin no longer defines any worker subagents; subagents are left to the harness's
defaults. `adversarial-delegation` is renamed `second-look` and keeps only second looks from
another model lineage; it owns the second-look rules that `pr-review` used to repeat.

## v4.0.0

v4 rebuilt `pr-review` around what found bugs on past reviews, and cut it from about 11,000
words to about 4,200. Realign and simplify became one shrink phase driven by the
smallest-change ladder from [ponytail](https://github.com/DietrichGebert/ponytail); every fix
that changes a value lists its readers; the owner gets a short recorded hands-on run; second
looks became swappable lanes. `bloat-shapes.md` and `test-value-by-domain.md` merged into
`references/lean.md`.

## v3.0.0

v3 removed `worker-opus` and `worker-opus-high`: Opus-priced subagents bought context
isolation at the orchestrator's own price.

## v2.0.0

v2 removed the seven gates (`scope-`, `build-`, `cut-`, `done-`, `bug-`, `ship-`,
`watch-gate`) and the `agent-roi.py` telemetry script. On current models they cost
more process than they returned; what still earned its keep was folded into
`principles`. They remain in git history at v1.4.1.

Codex installs the skills but not the `SessionStart` hook.
