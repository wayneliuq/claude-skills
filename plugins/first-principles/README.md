# first-principles

Four skills, kept small on purpose: capable models need goals and the few processes
they would not run unaided, not checklists.

| Skill | What it is |
|---|---|
| [`principles`](skills/principles/) | Seven goal-oriented principles for building, debugging, fixing and shipping. Loaded into **every session** by a `SessionStart` hook ([`hooks/hooks.json`](hooks/hooks.json)); not model-invoked. |
| [`pr-review`](skills/pr-review/) | Adversarial find-and-fix review of a PR, in that PR's branch: an in-app combination sweep, a short hands-on run for the owner, shrinking each feature by the smallest-change ladder, every reader of every changed value, and second looks from other models. Never marks a draft ready. The bug catalog and the lean reference are in [`references/`](skills/pr-review/references/). |
| [`adversarial-delegation`](skills/adversarial-delegation/) | Keep Opus-level work in-session; hand scouting and narrow checkable edits to Haiku and bounded implementation to Sonnet, review rather than trust; a second look from other model lineages on every consequential change. |
| [`deepen`](skills/deepen/) | Rewrites a plan, prompt or brief into a deeper version, not a bigger one: evidence first, then the bar each relevant domain's best practitioners would hold, each addition judged by an external oracle. Returned in the input's own form. User-invoked only. |

## Worker definitions

[`agents/`](agents/) holds the three workers that `adversarial-delegation`'s triage
dispatches to — Haiku 5.5 at medium, and Sonnet 5.5 at medium and high effort. There are
no Opus workers: Opus-level work stays in the orchestrating session. The definitions exist
because an Agent-tool call can pick a model but not an effort level, and because the
`sonnet`/`haiku` aliases resolve differently per provider, so they pin full model ids.
**The three share one system prompt body; change all three together.**

## Scripts and settings

| File | What it does |
|---|---|
| [`second-looks.json`](second-looks.json) | The second-look lanes (today grok and a free opencode model): harness, model, command, on or off. Copy it to `~/.claude/first-principles/second-looks.json` to change lanes without editing the plugin. |
| [`scripts/second-look.py`](scripts/second-look.py) | Runs every enabled lane on one brief in parallel; a lane that is missing, out of quota or silent is reported as skipped. |
| [`scripts/record-session.mjs`](scripts/record-session.mjs) | Records a hands-on run of a web app: clicks, a screenshot per click, console errors, failed requests, and problems you flag with Ctrl/Cmd+Shift+F, into a folder with a `summary.md` the agent reads first. Password, token and key fields are redacted in the log and blacked out in screenshots. |

## v4.0.0

v4 rebuilt `pr-review` around what found bugs on past reviews, and cut it from about 11,000
words to about 4,200. Realign and simplify became one shrink phase driven by the
smallest-change ladder from [ponytail](https://github.com/DietrichGebert/ponytail); every fix
that changes a value lists its readers; the owner gets a short recorded hands-on run; second
looks became swappable lanes. `bloat-shapes.md` and `test-value-by-domain.md` merged into
`references/lean.md`.

## v3.0.0

v3 removed `worker-opus` and `worker-opus-high`. Opus-priced subagents bought context
isolation at the orchestrator's own price; Haiku 5.5 buys the same for a fortieth of it.

## v2.0.0

v2 removed the seven gates (`scope-`, `build-`, `cut-`, `done-`, `bug-`, `ship-`,
`watch-gate`) and the `agent-roi.py` telemetry script. On current models they cost
more process than they returned; what still earned its keep was folded into
`principles`. They remain in git history at v1.4.1.

Codex installs the skills but not the `SessionStart` hook.
